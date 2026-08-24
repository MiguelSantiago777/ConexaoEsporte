"""Rotas de Relatório de Aula. Tag Swagger: 'Relatórios de Aula'. Emitido pelo PROFESSOR."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.application.relatorio_aula.service import RelatorioAulaService
from app.core.dependencies import (
    CurrentUser,
    DbSession,
    UsuarioAutenticado,
    assert_acesso_a_turma,
    require_perfis,
)
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.schemas.relatorio_aula_schemas import (
    RelatorioAulaCreateRequest,
    RelatorioAulaResponse,
)

router = APIRouter(prefix="/relatorios-aula", tags=["Relatórios de Aula"])

SomenteProfessor = Annotated[UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.PROFESSOR))]


@router.post(
    "",
    response_model=RelatorioAulaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Emitir relatório de aula (somente PROFESSOR)",
    description="O professor registra o conteúdo trabalhado e observações da aula "
    "de uma das suas turmas.",
)
def emitir_relatorio(
    body: RelatorioAulaCreateRequest, usuario: SomenteProfessor, db: DbSession
) -> RelatorioAulaResponse:
    assert_acesso_a_turma(usuario, db, body.turma_id)
    service = RelatorioAulaService(db)
    criado = service.criar(
        turma_id=body.turma_id, professor_id=usuario.id, data_ref=body.data,
        conteudo_trabalhado=body.conteudo_trabalhado, observacoes=body.observacoes,
    )
    return RelatorioAulaResponse.model_validate(criado)


@router.get(
    "/turma/{turma_id}",
    response_model=list[RelatorioAulaResponse],
    summary="Listar relatórios de uma turma",
    description="MASTER, GESTOR_POLO (do polo) e PROFESSOR (da turma) podem consultar.",
)
def listar_relatorios(turma_id: UUID, usuario: CurrentUser, db: DbSession) -> list[RelatorioAulaResponse]:
    assert_acesso_a_turma(usuario, db, turma_id)
    service = RelatorioAulaService(db)
    return [RelatorioAulaResponse.model_validate(r) for r in service.listar_por_turma(turma_id)]
