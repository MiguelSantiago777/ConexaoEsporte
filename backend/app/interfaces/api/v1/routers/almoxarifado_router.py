"""Rotas de Almoxarifado (locais físicos do estoque central). Tag Swagger:
'Estoque'. Cadastro/edição/remoção exclusivos do MASTER; GESTOR_POLO só
consulta (usa a lista pra escolher de onde uma Saída sai, ao registrar uma
Entrega de Materiais)."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.almoxarifado.service import AlmoxarifadoService
from app.application.produto.service import ProdutoService
from app.core.dependencies import (
    CurrentUser,
    DbSession,
    UsuarioAutenticado,
    assert_acesso_ao_almoxarifado,
    require_modulo_ou_perfis,
)
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.schemas.almoxarifado_schemas import (
    AlmoxarifadoCreateRequest,
    AlmoxarifadoResponse,
    AlmoxarifadoUpdateRequest,
)
from app.interfaces.api.v1.schemas.paginacao_schemas import PaginaResponse
from app.interfaces.api.v1.schemas.produto_schemas import SaldoProdutoNoAlmoxarifadoItem

router = APIRouter(prefix="/almoxarifados", tags=["Estoque"])

SomenteMaster = Annotated[
    UsuarioAutenticado, Depends(require_modulo_ou_perfis("almoxarifados", PerfilUsuario.MASTER))
]
MasterOuGestor = Annotated[
    UsuarioAutenticado,
    Depends(require_modulo_ou_perfis("almoxarifados", PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO)),
]


@router.get(
    "",
    response_model=list[AlmoxarifadoResponse] | PaginaResponse[AlmoxarifadoResponse],
    summary="Listar almoxarifados",
    description="MASTER e GESTOR_POLO podem consultar. Informe `pagina` pra paginar — sem isso, "
    "devolve a lista inteira (uso por telas que só precisam das opções, como um <select>).",
)
def listar_almoxarifados(
    usuario: MasterOuGestor, db: DbSession,
    apenas_ativos: bool = False,
    nome: str | None = None,
    pagina: Annotated[int | None, Query(ge=1)] = None,
    tamanho_pagina: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[AlmoxarifadoResponse] | PaginaResponse[AlmoxarifadoResponse]:
    service = AlmoxarifadoService(db)
    if pagina is None:
        almoxarifados = service.listar(apenas_ativos=apenas_ativos)
        return [AlmoxarifadoResponse.model_validate(a) for a in almoxarifados]

    almoxarifados, total = service.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, nome=nome)
    return PaginaResponse(
        itens=[AlmoxarifadoResponse.model_validate(a) for a in almoxarifados],
        total=total, pagina=pagina, tamanho_pagina=tamanho_pagina,
    )


@router.get(
    "/{almoxarifado_id}", response_model=AlmoxarifadoResponse,
    summary="Detalhar almoxarifado",
    description="MASTER e GESTOR_POLO consultam qualquer um. COORDENADOR_ALMOXARIFADO só o próprio.",
)
def buscar_almoxarifado(almoxarifado_id: UUID, usuario: CurrentUser, db: DbSession) -> AlmoxarifadoResponse:
    assert_acesso_ao_almoxarifado(usuario, almoxarifado_id, "almoxarifados", "estoque")
    almoxarifado = AlmoxarifadoService(db).buscar(almoxarifado_id)
    if not almoxarifado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Almoxarifado não encontrado.")
    return AlmoxarifadoResponse.model_validate(almoxarifado)


@router.get(
    "/{almoxarifado_id}/saldos", response_model=list[SaldoProdutoNoAlmoxarifadoItem],
    summary="Saldo de cada produto num almoxarifado",
    description="MASTER e GESTOR_POLO consultam qualquer um. COORDENADOR_ALMOXARIFADO só o próprio. "
    "Só lista produtos que já tiveram alguma movimentação nele.",
)
def saldos_do_almoxarifado(almoxarifado_id: UUID, usuario: CurrentUser, db: DbSession) -> list[SaldoProdutoNoAlmoxarifadoItem]:
    assert_acesso_ao_almoxarifado(usuario, almoxarifado_id, "almoxarifados", "estoque")
    saldos = ProdutoService(db).saldos_por_produto_de(almoxarifado_id)
    return [SaldoProdutoNoAlmoxarifadoItem(**s) for s in saldos]


@router.post(
    "", response_model=AlmoxarifadoResponse, status_code=status.HTTP_201_CREATED,
    summary="Cadastrar almoxarifado",
)
def criar_almoxarifado(body: AlmoxarifadoCreateRequest, usuario: SomenteMaster, db: DbSession) -> AlmoxarifadoResponse:
    criado = AlmoxarifadoService(db).criar(nome=body.nome, descricao=body.descricao)
    return AlmoxarifadoResponse.model_validate(criado)


@router.patch("/{almoxarifado_id}", response_model=AlmoxarifadoResponse, summary="Editar almoxarifado")
def editar_almoxarifado(
    almoxarifado_id: UUID, body: AlmoxarifadoUpdateRequest, usuario: SomenteMaster, db: DbSession
) -> AlmoxarifadoResponse:
    atualizado = AlmoxarifadoService(db).atualizar(
        almoxarifado_id, nome=body.nome, descricao=body.descricao, ativo=body.ativo,
    )
    return AlmoxarifadoResponse.model_validate(atualizado)


@router.delete(
    "/{almoxarifado_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover almoxarifado",
    description="Recusa a remoção se existir alguma movimentação de estoque registrada nele.",
)
def remover_almoxarifado(almoxarifado_id: UUID, usuario: SomenteMaster, db: DbSession) -> None:
    AlmoxarifadoService(db).remover(almoxarifado_id)
