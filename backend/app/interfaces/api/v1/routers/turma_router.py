"""Rotas de Turmas. Tag Swagger: 'Turmas'."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.turma.service import TurmaService
from app.core.dependencies import (
    CurrentUser,
    DbSession,
    UsuarioAutenticado,
    assert_acesso_ao_polo,
    assert_acesso_a_turma,
    require_perfis,
)
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.schemas.turma_schemas import TurmaCreateRequest, TurmaResponse, TurmaUpdateRequest

router = APIRouter(prefix="/turmas", tags=["Turmas"])

MasterOuGestor = Annotated[
    UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO))
]


@router.get(
    "",
    response_model=list[TurmaResponse],
    summary="Listar turmas",
    description="MASTER vê todas. GESTOR_POLO vê as do seu polo. PROFESSOR vê apenas as suas.",
)
def listar_turmas(usuario: CurrentUser, db: DbSession) -> list[TurmaResponse]:
    service = TurmaService(db)
    if usuario.perfil == PerfilUsuario.MASTER:
        turmas = service.listar()
    elif usuario.perfil == PerfilUsuario.GESTOR_POLO:
        turmas = service.listar(polo_id=usuario.polo_id)
    else:  # PROFESSOR
        turmas = service.listar(professor_id=usuario.id)
    return [TurmaResponse(**t) for t in turmas]


@router.post(
    "",
    response_model=TurmaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar turma",
    description="MASTER cria em qualquer polo. GESTOR_POLO só cria turmas no seu próprio polo.",
)
def criar_turma(body: TurmaCreateRequest, usuario: MasterOuGestor, db: DbSession) -> TurmaResponse:
    assert_acesso_ao_polo(usuario, body.polo_id)  # bloqueia gestor de outro polo
    service = TurmaService(db)
    criada = service.criar(
        polo_id=body.polo_id, modalidade_id=body.modalidade_id, professor_id=body.professor_id,
        horario_inicio=body.horario_inicio, horario_fim=body.horario_fim,
        dias_semana=body.dias_semana, limite_vagas=body.limite_vagas,
    )
    return TurmaResponse(**criada)


@router.patch(
    "/{turma_id}",
    response_model=TurmaResponse,
    summary="Editar turma / vincular professor",
    description="MASTER e GESTOR_POLO (do próprio polo) podem editar. É aqui que o "
    "gestor vincula um PROFESSOR à turma via `professor_id`.",
)
def atualizar_turma(
    turma_id: UUID, body: TurmaUpdateRequest, usuario: MasterOuGestor, db: DbSession
) -> TurmaResponse:
    assert_acesso_a_turma(usuario, db, turma_id)
    service = TurmaService(db)
    atualizada = service.atualizar(turma_id, **body.model_dump(exclude_unset=True))
    if not atualizada:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return TurmaResponse(**atualizada)
