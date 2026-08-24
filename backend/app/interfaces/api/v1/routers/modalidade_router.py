"""Rotas de Modalidades. Tag Swagger: 'Modalidades'."""
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.application.modalidade.service import ModalidadeService
from app.core.dependencies import CurrentUser, DbSession, UsuarioAutenticado, require_perfis
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.schemas.modalidade_schemas import ModalidadeCreateRequest, ModalidadeResponse

router = APIRouter(prefix="/modalidades", tags=["Modalidades"])

MasterOuGestor = Annotated[
    UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO))
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
