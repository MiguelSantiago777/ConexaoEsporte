"""Rotas de Polos. Tag Swagger: 'Polos'. Somente MASTER gerencia Polos."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.polo.service import PoloService
from app.core.dependencies import CurrentUser, DbSession, UsuarioAutenticado, assert_acesso_ao_polo, require_perfis
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.schemas.polo_schemas import PoloCreateRequest, PoloResponse, PoloUpdateRequest

router = APIRouter(prefix="/polos", tags=["Polos"])

SomenteMaster = Annotated[UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.MASTER))]


@router.get(
    "",
    response_model=list[PoloResponse],
    summary="Listar polos",
    description="MASTER vê todos os polos. GESTOR_POLO vê apenas o seu.",
)
def listar_polos(usuario: CurrentUser, db: DbSession) -> list[PoloResponse]:
    service = PoloService(db)
    todos = service.listar()
    if usuario.perfil == PerfilUsuario.GESTOR_POLO:
        todos = [p for p in todos if p.id == usuario.polo_id]
    return [PoloResponse.model_validate(p) for p in todos]


@router.post(
    "",
    response_model=PoloResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar polo (somente MASTER)",
)
def criar_polo(body: PoloCreateRequest, usuario: SomenteMaster, db: DbSession) -> PoloResponse:
    service = PoloService(db)
    criado = service.criar(
        nome=body.nome, codigo=body.codigo, endereco=body.endereco,
        horario_funcionamento=body.horario_funcionamento, gestor_responsavel_id=body.gestor_responsavel_id,
    )
    return PoloResponse.model_validate(criado)


@router.patch(
    "/{polo_id}",
    response_model=PoloResponse,
    summary="Editar polo (somente MASTER)",
)
def atualizar_polo(polo_id: UUID, body: PoloUpdateRequest, usuario: SomenteMaster, db: DbSession) -> PoloResponse:
    service = PoloService(db)
    atualizado = service.atualizar(polo_id, **body.model_dump(exclude_unset=True))
    if not atualizado:
        raise HTTPException(status_code=404, detail="Polo não encontrado.")
    return PoloResponse.model_validate(atualizado)
