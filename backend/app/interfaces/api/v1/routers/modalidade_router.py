"""Rotas de Modalidades. Tag Swagger: 'Modalidades'."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.application.modalidade.service import ModalidadeService
from app.core.dependencies import CurrentUser, DbSession, UsuarioAutenticado, require_modulo_ou_perfis
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.schemas.modalidade_schemas import (
    ModalidadeCreateRequest,
    ModalidadeResponse,
    ModalidadeUpdateRequest,
)

router = APIRouter(prefix="/modalidades", tags=["Modalidades"])

MasterOuGestor = Annotated[
    UsuarioAutenticado,
    Depends(require_modulo_ou_perfis("modalidades", PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO)),
]


@router.get("", response_model=list[ModalidadeResponse], summary="Listar modalidades")
def listar_modalidades(usuario: CurrentUser, db: DbSession) -> list[ModalidadeResponse]:
    return [ModalidadeResponse.model_validate(m) for m in ModalidadeService(db).listar()]


@router.post(
    "",
    response_model=ModalidadeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar modalidade",
    description="Disponível para MASTER e GESTOR_POLO.",
)
def criar_modalidade(body: ModalidadeCreateRequest, usuario: MasterOuGestor, db: DbSession) -> ModalidadeResponse:
    criada = ModalidadeService(db).criar(nome=body.nome, descricao=body.descricao)
    return ModalidadeResponse.model_validate(criada)


@router.patch(
    "/{modalidade_id}",
    response_model=ModalidadeResponse,
    summary="Editar modalidade",
    description="Disponível para MASTER e GESTOR_POLO.",
)
def editar_modalidade(
    modalidade_id: UUID, body: ModalidadeUpdateRequest, usuario: MasterOuGestor, db: DbSession
) -> ModalidadeResponse:
    atualizada = ModalidadeService(db).atualizar(modalidade_id, nome=body.nome, descricao=body.descricao)
    return ModalidadeResponse.model_validate(atualizada)


@router.delete(
    "/{modalidade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover modalidade",
    description="Disponível para MASTER e GESTOR_POLO. Recusa a remoção se existir alguma turma "
    "cadastrada com essa modalidade.",
)
def remover_modalidade(modalidade_id: UUID, usuario: MasterOuGestor, db: DbSession) -> None:
    ModalidadeService(db).remover(modalidade_id)
