"""Rotas de Produto (catálogo central de Estoque). Tag Swagger: 'Estoque'.
Cadastro/edição/remoção exclusivos do MASTER; COORDENADOR_ALMOXARIFADO só
consulta (usa o catálogo pra escolher itens na hora de registrar uma
Entrada de estoque)."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status

from app.application.importacao.planilha import ler_planilha
from app.application.produto.importacao_service import ProdutoImportacaoService
from app.application.produto.service import ProdutoService
from app.core.dependencies import CurrentUser, DbSession, UsuarioAutenticado, require_modulo_ou_perfis
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.routers._arquivo_helper import resposta_download
from app.interfaces.api.v1.schemas.importacao_schemas import ResultadoImportacaoResponse
from app.interfaces.api.v1.schemas.paginacao_schemas import PaginaResponse
from app.interfaces.api.v1.schemas.produto_schemas import (
    ProdutoCreateRequest,
    ProdutoResponse,
    ProdutoUpdateRequest,
    SaldoAlmoxarifadoItem,
)

router = APIRouter(prefix="/produtos", tags=["Estoque"])

SomenteMaster = Annotated[
    UsuarioAutenticado, Depends(require_modulo_ou_perfis("estoque", PerfilUsuario.MASTER))
]


def _com_saldo(service: ProdutoService, produtos) -> list[ProdutoResponse]:
    saldos = service.saldos_em_lote([p.id for p in produtos])
    return [
        ProdutoResponse(
            id=p.id, nome=p.nome, unidade_medida=p.unidade_medida, ncm=p.ncm, descricao=p.descricao,
            ativo=p.ativo, saldo_atual=saldos.get(p.id, 0),
        )
        for p in produtos
    ]


@router.get(
    "",
    response_model=list[ProdutoResponse] | PaginaResponse[ProdutoResponse],
    summary="Listar produtos do catálogo de Estoque",
    description="MASTER e COORDENADOR_ALMOXARIFADO podem consultar. Informe `pagina` pra paginar — sem "
    "isso, devolve a lista inteira (uso por telas que só precisam das opções, como um <select>).",
)
def listar_produtos(
    usuario: CurrentUser, db: DbSession,
    apenas_ativos: bool = False,
    nome: str | None = None,
    pagina: Annotated[int | None, Query(ge=1)] = None,
    tamanho_pagina: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[ProdutoResponse] | PaginaResponse[ProdutoResponse]:
    if (
        usuario.perfil not in (PerfilUsuario.MASTER, PerfilUsuario.COORDENADOR_ALMOXARIFADO)
        and not usuario.tem_modulo("estoque")
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil sem permissão para executar esta ação.")
    service = ProdutoService(db)

    if pagina is None:
        produtos = service.listar(apenas_ativos=apenas_ativos)
        return _com_saldo(service, produtos)

    produtos, total = service.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, nome=nome)
    return PaginaResponse(itens=_com_saldo(service, produtos), total=total, pagina=pagina, tamanho_pagina=tamanho_pagina)


@router.get(
    "/{produto_id}/saldos-por-almoxarifado",
    response_model=list[SaldoAlmoxarifadoItem],
    summary="Saldo do produto em cada almoxarifado",
    description="MASTER e COORDENADOR_ALMOXARIFADO podem consultar. Só lista almoxarifados que já "
    "tiveram alguma movimentação deste produto.",
)
def saldos_por_almoxarifado(produto_id: UUID, usuario: CurrentUser, db: DbSession) -> list[SaldoAlmoxarifadoItem]:
    if (
        usuario.perfil not in (PerfilUsuario.MASTER, PerfilUsuario.COORDENADOR_ALMOXARIFADO)
        and not usuario.tem_modulo("estoque")
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil sem permissão para executar esta ação.")
    saldos = ProdutoService(db).saldo_por_almoxarifado(produto_id)
    return [SaldoAlmoxarifadoItem(**s) for s in saldos]


@router.post(
    "", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED,
    summary="Cadastrar produto no catálogo de Estoque",
)
def criar_produto(body: ProdutoCreateRequest, usuario: SomenteMaster, db: DbSession) -> ProdutoResponse:
    service = ProdutoService(db)
    criado = service.criar(
        nome=body.nome, unidade_medida=body.unidade_medida, descricao=body.descricao,
        ncm=body.ncm, quantidade_inicial=body.quantidade, criado_por_id=usuario.id,
    )
    return ProdutoResponse(
        id=criado.id, nome=criado.nome, unidade_medida=criado.unidade_medida, ncm=criado.ncm,
        descricao=criado.descricao, ativo=criado.ativo, saldo_atual=body.quantidade,
    )


@router.get(
    "/importar/modelo",
    summary="Baixar modelo de planilha (.xlsx) para importação em massa de produtos",
)
def baixar_modelo_importacao_produtos(usuario: SomenteMaster, db: DbSession) -> Response:
    buffer = ProdutoImportacaoService(db).gerar_modelo()
    return resposta_download(
        buffer.getvalue(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "modelo-importacao-produtos.xlsx",
    )


@router.post(
    "/importar",
    response_model=ResultadoImportacaoResponse,
    summary="Importar produtos em massa a partir de planilha (.xlsx)",
    description="Envie o arquivo preenchido a partir do modelo (`GET /produtos/importar/modelo`). Com "
    "`confirmar=false` (padrão) só valida e devolve a prévia — nada é gravado. Com "
    "`confirmar=true` grava as linhas válidas e pula as com erro, sem abortar o lote inteiro.",
)
async def importar_produtos(
    usuario: SomenteMaster, db: DbSession,
    arquivo: UploadFile = File(...),
    confirmar: bool = Query(False),
) -> ResultadoImportacaoResponse:
    linhas = ler_planilha(await arquivo.read())
    resultado = ProdutoImportacaoService(db).importar(linhas, confirmar, criado_por_id=usuario.id)
    return ResultadoImportacaoResponse.de_resultado(resultado)


@router.patch("/{produto_id}", response_model=ProdutoResponse, summary="Editar produto do catálogo de Estoque")
def editar_produto(produto_id: UUID, body: ProdutoUpdateRequest, usuario: SomenteMaster, db: DbSession) -> ProdutoResponse:
    service = ProdutoService(db)
    atualizado = service.atualizar(
        produto_id, nome=body.nome, unidade_medida=body.unidade_medida, descricao=body.descricao, ativo=body.ativo,
        ncm=body.ncm,
    )
    saldo = service.saldo_atual(produto_id)
    return ProdutoResponse(
        id=atualizado.id, nome=atualizado.nome, unidade_medida=atualizado.unidade_medida, ncm=atualizado.ncm,
        descricao=atualizado.descricao, ativo=atualizado.ativo, saldo_atual=saldo,
    )


@router.delete(
    "/{produto_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover produto do catálogo de Estoque",
    description="Recusa a remoção se existir alguma movimentação de estoque registrada pra este produto.",
)
def remover_produto(produto_id: UUID, usuario: SomenteMaster, db: DbSession) -> None:
    ProdutoService(db).remover(produto_id)
