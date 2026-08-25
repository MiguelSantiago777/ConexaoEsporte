"""Repositório de Matrícula (vínculo N:N beneficiário↔turma)."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.matricula.entities import Matricula
from app.infrastructure.database.models import BeneficiarioModel, MatriculaModel


def _to_entity(m: MatriculaModel) -> Matricula:
    return Matricula(
        id=m.id, beneficiario_id=m.beneficiario_id, turma_id=m.turma_id,
        ativo=m.ativo, criado_em=m.criado_em,
    )


class MatriculaRepository:
    def __init__(self, db: Session):
        self.db = db

    def buscar_por_id(self, matricula_id: UUID) -> Matricula | None:
        m = self.db.get(MatriculaModel, matricula_id)
        return _to_entity(m) if m else None

    def buscar_por_beneficiario_e_turma(self, beneficiario_id: UUID, turma_id: UUID) -> Matricula | None:
        stmt = select(MatriculaModel).where(
            MatriculaModel.beneficiario_id == beneficiario_id, MatriculaModel.turma_id == turma_id
        )
        m = self.db.scalar(stmt)
        return _to_entity(m) if m else None

    def listar_por_beneficiario(self, beneficiario_id: UUID) -> list[Matricula]:
        stmt = select(MatriculaModel).where(MatriculaModel.beneficiario_id == beneficiario_id)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def contar_ativas_por_turma(self, turma_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(MatriculaModel)
            .join(BeneficiarioModel, BeneficiarioModel.id == MatriculaModel.beneficiario_id)
            .where(
                MatriculaModel.turma_id == turma_id,
                MatriculaModel.ativo.is_(True),
                BeneficiarioModel.ativo.is_(True),
            )
        )
        return self.db.scalar(stmt) or 0

    def criar(self, matricula: Matricula) -> Matricula:
        m = MatriculaModel(
            beneficiario_id=matricula.beneficiario_id, turma_id=matricula.turma_id, ativo=matricula.ativo
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def atualizar(self, matricula_id: UUID, **campos) -> Matricula | None:
        m = self.db.get(MatriculaModel, matricula_id)
        if not m:
            return None
        for k, v in campos.items():
            if v is not None:
                setattr(m, k, v)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)
