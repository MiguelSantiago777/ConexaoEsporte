"""Rotas de Frequência/Chamada. Tag Swagger: 'Frequência'. Foco no perfil PROFESSOR."""
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.frequencia.service import FrequenciaService
from app.core.dependencies import (
    CurrentUser,
    DbSession,
    UsuarioAutenticado,
    assert_acesso_a_turma,
    require_perfis,
)
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.schemas.frequencia_schemas import ChamadaCreateRequest, FrequenciaResponse

router = APIRouter(prefix="/frequencias", tags=["Frequência"])

# Chamada é feita pelo PROFESSOR; MASTER/GESTOR podem consultar/lançar em suporte.
QualquerPerfil = Annotated[
    UsuarioAutenticado,
    Depends(require_perfis(PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO, PerfilUsuario.PROFESSOR)),
]


@router.post(
    "/chamada",
    response_model=list[FrequenciaResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Lançar chamada diária (frequência dos beneficiários)",
    description="Registra a presença/ausência dos beneficiários de uma turma numa data. "
    "PROFESSOR só pode lançar chamada nas suas próprias turmas. Reenviar a mesma data "
    "atualiza os registros (idempotente por turma+beneficiário+data).",
)
def lancar_chamada(body: ChamadaCreateRequest, usuario: QualquerPerfil, db: DbSession) -> list[FrequenciaResponse]:
    assert_acesso_a_turma(usuario, db, body.turma_id)
    service = FrequenciaService(db)
    registros = service.registrar_chamada(
        turma_id=body.turma_id, data_ref=body.data,
        presencas=[(p.beneficiario_id, p.presente) for p in body.presencas],
        registrado_por_id=usuario.id,
    )
    return [FrequenciaResponse.model_validate(r) for r in registros]


@router.get(
    "/turma/{turma_id}",
    response_model=list[FrequenciaResponse],
    summary="Consultar chamada de uma turma por data",
)
def consultar_chamada(
    turma_id: UUID, data: date, usuario: QualquerPerfil, db: DbSession
) -> list[FrequenciaResponse]:
    assert_acesso_a_turma(usuario, db, turma_id)
    service = FrequenciaService(db)
    return [FrequenciaResponse.model_validate(r) for r in service.listar_chamada(turma_id, data)]
