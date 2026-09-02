"""Repositório de Relatório de Aula."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.relatorio_aula.entities import RelatorioAula
from app.infrastructure.database.models import RelatorioAulaModel


def _to_entity(m: RelatorioAulaModel) -> RelatorioAula:
    return RelatorioAula(
        id=m.id, turma_id=m.turma_id, professor_id=m.professor_id, data=m.data,
        conteudo_trabalhado=m.conteudo_trabalhado, observacoes=m.observacoes, criado_em=m.criado_em,
    )


class RelatorioAulaRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_por_turma(self, turma_id: UUID) -> list[RelatorioAula]:
        stmt = select(RelatorioAulaModel).where(RelatorioAulaModel.turma_id == turma_id)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def listar_por_turmas(self, turma_ids: list[UUID]) -> list[RelatorioAula]:
        if not turma_ids:
            return []
        stmt = (
            select(RelatorioAulaModel)
            .where(RelatorioAulaModel.turma_id.in_(turma_ids))
            .order_by(RelatorioAulaModel.criado_em.desc())
        )
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def criar(self, relatorio: RelatorioAula) -> RelatorioAula:
        m = RelatorioAulaModel(
            turma_id=relatorio.turma_id, professor_id=relatorio.professor_id, data=relatorio.data,
            conteudo_trabalhado=relatorio.conteudo_trabalhado, observacoes=relatorio.observacoes,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)
