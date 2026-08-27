"""Repositório de Impeditivo de Aula (dia em que a turma inteira não teve aula)."""
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.frequencia.entities import ImpeditivoAula
from app.infrastructure.database.models import ImpeditivoAulaModel


def _to_entity(m: ImpeditivoAulaModel) -> ImpeditivoAula:
    return ImpeditivoAula(
        id=m.id, turma_id=m.turma_id, data=m.data, justificativa=m.justificativa,
        criado_por_id=m.criado_por_id, criado_em=m.criado_em,
    )


class ImpeditivoAulaRepository:
    def __init__(self, db: Session):
        self.db = db

    def buscar_por_turma_e_data(self, turma_id: UUID, data_ref: date) -> ImpeditivoAula | None:
        m = self.db.scalar(
            select(ImpeditivoAulaModel).where(
                ImpeditivoAulaModel.turma_id == turma_id, ImpeditivoAulaModel.data == data_ref
            )
        )
        return _to_entity(m) if m else None

    def buscar_por_id(self, impeditivo_id: UUID) -> ImpeditivoAula | None:
        m = self.db.get(ImpeditivoAulaModel, impeditivo_id)
        return _to_entity(m) if m else None

    def listar_por_turma_e_periodo(self, turma_id: UUID, data_inicio: date, data_fim: date) -> list[ImpeditivoAula]:
        stmt = select(ImpeditivoAulaModel).where(
            ImpeditivoAulaModel.turma_id == turma_id,
            ImpeditivoAulaModel.data >= data_inicio,
            ImpeditivoAulaModel.data <= data_fim,
        ).order_by(ImpeditivoAulaModel.data)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def criar(self, impeditivo: ImpeditivoAula) -> ImpeditivoAula:
        m = ImpeditivoAulaModel(
            turma_id=impeditivo.turma_id, data=impeditivo.data, justificativa=impeditivo.justificativa,
            criado_por_id=impeditivo.criado_por_id,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def remover(self, impeditivo_id: UUID) -> bool:
        m = self.db.get(ImpeditivoAulaModel, impeditivo_id)
        if not m:
            return False
        self.db.delete(m)
        self.db.commit()
        return True
