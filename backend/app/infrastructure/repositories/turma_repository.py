"""Repositório de Turma."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.turma.entities import Turma
from app.infrastructure.database.models import BeneficiarioModel, TurmaModel


def _to_entity(m: TurmaModel) -> Turma:
    return Turma(
        id=m.id, polo_id=m.polo_id, modalidade_id=m.modalidade_id, professor_id=m.professor_id,
        horario_inicio=m.horario_inicio, horario_fim=m.horario_fim,
        dias_semana=m.dias_semana.split(","), limite_vagas=m.limite_vagas,
    )


class TurmaRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, polo_id: UUID | None = None, professor_id: UUID | None = None) -> list[Turma]:
        stmt = select(TurmaModel)
        if polo_id:
            stmt = stmt.where(TurmaModel.polo_id == polo_id)
        if professor_id:
            stmt = stmt.where(TurmaModel.professor_id == professor_id)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def buscar_por_id(self, turma_id: UUID) -> Turma | None:
        m = self.db.get(TurmaModel, turma_id)
        return _to_entity(m) if m else None

    def contar_beneficiarios_ativos(self, turma_id: UUID) -> int:
        stmt = select(func.count()).select_from(BeneficiarioModel).where(
            BeneficiarioModel.turma_id == turma_id, BeneficiarioModel.ativo.is_(True)
        )
        return self.db.scalar(stmt) or 0

    def criar(self, turma: Turma) -> Turma:
        m = TurmaModel(
            polo_id=turma.polo_id, modalidade_id=turma.modalidade_id, professor_id=turma.professor_id,
            horario_inicio=turma.horario_inicio, horario_fim=turma.horario_fim,
            dias_semana=",".join(turma.dias_semana), limite_vagas=turma.limite_vagas,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def atualizar(self, turma_id: UUID, **campos) -> Turma | None:
        m = self.db.get(TurmaModel, turma_id)
        if not m:
            return None
        for k, v in campos.items():
            if v is None:
                continue
            if k == "dias_semana":
                v = ",".join(v)
            setattr(m, k, v)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)
