"""Use cases de Relatório de Aula (emitido pelo Professor)."""
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.relatorio_aula.entities import RelatorioAula
from app.infrastructure.repositories.relatorio_aula_repository import RelatorioAulaRepository


class RelatorioAulaService:
    def __init__(self, db: Session):
        self.repo = RelatorioAulaRepository(db)

    def listar_por_turma(self, turma_id: UUID) -> list[RelatorioAula]:
        return self.repo.listar_por_turma(turma_id)

    def criar(
        self, turma_id: UUID, professor_id: UUID, data_ref: date,
        conteudo_trabalhado: str, observacoes: str | None,
    ) -> RelatorioAula:
        relatorio = RelatorioAula(
            id=None, turma_id=turma_id, professor_id=professor_id, data=data_ref,
            conteudo_trabalhado=conteudo_trabalhado, observacoes=observacoes,
        )
        return self.repo.criar(relatorio)
