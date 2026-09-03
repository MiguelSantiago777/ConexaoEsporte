"""Rotas de Movimento de Estoque (Entrada/Saída de um Produto) e do
Relatório de Estoque. Tag Swagger: 'Estoque'.

ENTRADA é lançada manualmente (com nota fiscal/comprovante em anexo),
exclusiva do MASTER. SAÍDA não tem rota própria — ela nasce automaticamente
quando um item de uma Entrega de Materiais referencia um produto (ver
`entrega_material_router.py`). MASTER e COORDENADOR_ALMOXARIFADO podem consultar."""
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.application.estoque.service import MovimentoEstoqueService
from app.core.dependencies import (
    CurrentUser,
    DbSession,
    UsuarioAutenticado,
    assert_acesso_ao_almoxarifado,
    require_modulo_ou_perfis,
)
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.routers._arquivo_helper import resposta_download
from app.interfaces.api.v1.schemas.estoque_schemas import MovimentoEstoqueResponse, RelatorioEstoqueResponse
from app.interfaces.api.v1.schemas.paginacao_schemas import PaginaResponse

router = APIRouter(prefix="/movimentos-estoque", tags=["Estoque"])

MasterOuCoordenador = Annotated[
    UsuarioAutenticado,
    Depends(require_modulo_ou_perfis("estoque", PerfilUsuario.MASTER, PerfilUsuario.COORDENADOR_ALMOXARIFADO)),
]


def _acesso_leitura(usuario: UsuarioAutenticado) -> None:
    if (
        usuario.perfil not in (PerfilUsuario.MASTER, PerfilUsuario.COORDENADOR_ALMOXARIFADO)
        and not usuario.tem_modulo("estoque")
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil sem permissão para executar esta ação.")


def _forcar_escopo_almoxarifado(usuario: UsuarioAutenticado, almoxarifado_id: UUID | None) -> UUID | None:
    """COORDENADOR_ALMOXARIFADO só vê/opera no próprio almoxarifado — ignora
    qualquer outro valor pedido e força o dele."""
    if usuario.perfil == PerfilUsuario.COORDENADOR_ALMOXARIFADO:
        return usuario.almoxarifado_id
    return almoxarifado_id


@router.get(
    "",
    response_model=list[MovimentoEstoqueResponse] | PaginaResponse[MovimentoEstoqueResponse],
    summary="Listar movimentos de estoque (Entradas e Saídas)",
    description="MASTER e COORDENADOR_ALMOXARIFADO podem consultar. Informe `pagina` pra paginar — sem "
    "isso, devolve a lista inteira.",
)
def listar_movimentos(
    usuario: CurrentUser, db: DbSession,
    produto_id: UUID | None = None,
    almoxarifado_id: UUID | None = None,
    tipo: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    pagina: Annotated[int | None, Query(ge=1)] = None,
    tamanho_pagina: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[MovimentoEstoqueResponse] | PaginaResponse[MovimentoEstoqueResponse]:
    _acesso_leitura(usuario)
    almoxarifado_id = _forcar_escopo_almoxarifado(usuario, almoxarifado_id)
    service = MovimentoEstoqueService(db)

    if pagina is None:
        movimentos = service.listar(
            produto_id=produto_id, tipo=tipo, data_inicio=data_inicio, data_fim=data_fim,
            almoxarifado_id=almoxarifado_id,
        )
        return [MovimentoEstoqueResponse.model_validate(m) for m in movimentos]

    movimentos, total = service.listar_pagina(
        pagina=pagina, tamanho_pagina=tamanho_pagina, produto_id=produto_id, tipo=tipo,
        data_inicio=data_inicio, data_fim=data_fim, almoxarifado_id=almoxarifado_id,
    )
    return PaginaResponse(
        itens=[MovimentoEstoqueResponse.model_validate(m) for m in movimentos],
        total=total, pagina=pagina, tamanho_pagina=tamanho_pagina,
    )


@router.post(
    "", response_model=MovimentoEstoqueResponse, status_code=status.HTTP_201_CREATED,
    summary="Registrar Entrada de estoque",
    description="MASTER pode lançar em qualquer almoxarifado. COORDENADOR_ALMOXARIFADO só no seu "
    "próprio. O comprovante (nota fiscal, foto do recibo etc.) é obrigatório — aceita PDF, JPG, PNG "
    "ou WEBP, até o limite configurado de tamanho.",
)
async def registrar_entrada(
    usuario: MasterOuCoordenador, db: DbSession,
    produto_id: Annotated[UUID, Form()],
    almoxarifado_id: Annotated[UUID, Form()],
    quantidade: Annotated[int, Form(gt=0)],
    data: Annotated[date, Form()],
    arquivo: Annotated[UploadFile, File()],
    observacao: Annotated[str | None, Form()] = None,
    entregue_por: Annotated[str | None, Form()] = None,
    recebido_por: Annotated[str | None, Form()] = None,
) -> MovimentoEstoqueResponse:
    assert_acesso_ao_almoxarifado(usuario, almoxarifado_id, "estoque", "almoxarifados")
    criado = await MovimentoEstoqueService(db).registrar_entrada(
        produto_id=produto_id, almoxarifado_id=almoxarifado_id, quantidade=quantidade, data_ref=data,
        observacao=observacao, arquivo=arquivo, criado_por_id=usuario.id,
        entregue_por=entregue_por, recebido_por=recebido_por,
    )
    return MovimentoEstoqueResponse.model_validate(criado)


@router.get("/{movimento_id}/arquivo", summary="Baixar o comprovante de uma Entrada de estoque")
def baixar_arquivo(movimento_id: UUID, usuario: CurrentUser, db: DbSession):
    _acesso_leitura(usuario)
    movimento, conteudo = MovimentoEstoqueService(db).buscar_arquivo(movimento_id)
    if not movimento or conteudo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comprovante não encontrado.")
    assert_acesso_ao_almoxarifado(usuario, movimento.almoxarifado_id, "estoque", "almoxarifados")
    return resposta_download(conteudo, movimento.content_type, movimento.nome_arquivo or "comprovante")


@router.get(
    "/relatorio", response_model=RelatorioEstoqueResponse,
    summary="Relatório de Estoque — saldos por produto e movimentos do período",
    description="MASTER pode consultar tudo. COORDENADOR_ALMOXARIFADO só vê o próprio almoxarifado.",
)
def relatorio_estoque(
    data_inicio: date, data_fim: date, usuario: CurrentUser, db: DbSession
) -> RelatorioEstoqueResponse:
    _acesso_leitura(usuario)
    almoxarifado_id = _forcar_escopo_almoxarifado(usuario, None)
    dados = MovimentoEstoqueService(db).relatorio(data_inicio, data_fim, almoxarifado_id=almoxarifado_id)
    return RelatorioEstoqueResponse(
        data_inicio=dados["data_inicio"], data_fim=dados["data_fim"], total_produtos=dados["total_produtos"],
        total_entradas_periodo=dados["total_entradas_periodo"], total_saidas_periodo=dados["total_saidas_periodo"],
        saldos=dados["saldos"],
        movimentos=[MovimentoEstoqueResponse.model_validate(m) for m in dados["movimentos"]],
    )
