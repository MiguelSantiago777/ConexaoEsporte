"""Rotas de Papel — a Central de Acessos, exclusiva do MASTER: cria níveis
de acesso personalizados escolhendo módulos do sistema, para depois
vincular usuários com perfil PERSONALIZADO a eles. Tag Swagger: 'Central de
Acessos'."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.application.papel.service import PapelService
from app.core.dependencies import DbSession, UsuarioAutenticado, require_perfis
from app.domain.enums import MODULOS_SISTEMA, PerfilUsuario
from app.interfaces.api.v1.schemas.paginacao_schemas import PaginaResponse
from app.interfaces.api.v1.schemas.papel_schemas import (
    ModuloDisponivelItem,
    PapelCreateRequest,
    PapelResponse,
    PapelUpdateRequest,
)

router = APIRouter(prefix="/papeis", tags=["Central de Acessos"])

SomenteMaster = Annotated[UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.MASTER))]


@router.get(
    "/modulos", response_model=list[ModuloDisponivelItem],
    summary="Listar módulos do sistema disponíveis para um Papel",
)
def listar_modulos(usuario: SomenteMaster) -> list[ModuloDisponivelItem]:
    return [ModuloDisponivelItem(chave=chave, label=label) for chave, label in MODULOS_SISTEMA.items()]


@router.get(
    "",
    response_model=list[PapelResponse] | PaginaResponse[PapelResponse],
    summary="Listar Papéis (níveis de acesso personalizados)",
    description="Exclusivo do MASTER. Informe `pagina` pra paginar — sem isso, devolve a lista inteira "
    "(uso por telas que só precisam das opções, como um <select>).",
)
def listar_papeis(
    usuario: SomenteMaster, db: DbSession,
    apenas_ativos: bool = False,
    nome: str | None = None,
    pagina: Annotated[int | None, Query(ge=1)] = None,
    tamanho_pagina: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[PapelResponse] | PaginaResponse[PapelResponse]:
    service = PapelService(db)
    if pagina is None:
        return [PapelResponse.model_validate(p) for p in service.listar(apenas_ativos=apenas_ativos)]

    papeis, total = service.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, nome=nome)
    return PaginaResponse(
        itens=[PapelResponse.model_validate(p) for p in papeis], total=total, pagina=pagina, tamanho_pagina=tamanho_pagina,
    )


@router.post("", response_model=PapelResponse, status_code=status.HTTP_201_CREATED, summary="Criar Papel")
def criar_papel(body: PapelCreateRequest, usuario: SomenteMaster, db: DbSession) -> PapelResponse:
    criado = PapelService(db).criar(nome=body.nome, descricao=body.descricao, modulos=body.modulos)
    return PapelResponse.model_validate(criado)


@router.patch("/{papel_id}", response_model=PapelResponse, summary="Editar Papel")
def editar_papel(papel_id: UUID, body: PapelUpdateRequest, usuario: SomenteMaster, db: DbSession) -> PapelResponse:
    atualizado = PapelService(db).atualizar(
        papel_id, nome=body.nome, descricao=body.descricao, modulos=body.modulos, ativo=body.ativo,
    )
    return PapelResponse.model_validate(atualizado)


@router.delete(
    "/{papel_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover Papel",
    description="Recusa a remoção se existir algum usuário vinculado a este Papel.",
)
def remover_papel(papel_id: UUID, usuario: SomenteMaster, db: DbSession) -> None:
    PapelService(db).remover(papel_id)
