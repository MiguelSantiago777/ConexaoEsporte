"""Repositório de Frequência/Presença."""
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.domain.frequencia.entities import RegistroFrequencia
from app.infrastructure.database.models import FrequenciaModel


def _to_entity(m: FrequenciaModel) -> RegistroFrequencia:
    return RegistroFrequencia(
        id=m.id, turma_id=m.turma_id, beneficiario_id=m.beneficiario_id,
        data=m.data, presente=m.presente, registrado_por_id=m.registrado_por_id,
        falta_justificada=m.falta_justificada, justificativa=m.justificativa,
    )


class FrequenciaRepository:
    def __init__(self, db: Session):
        self.db = db

    def registrar_chamada(self, registros: list[RegistroFrequencia]) -> list[RegistroFrequencia]:
        """Upsert em lote: se já existe registro para turma+beneficiario+data, atualiza a presença."""
        resultado = []
        for r in registros:
            stmt = pg_insert(FrequenciaModel).values(
                turma_id=r.turma_id, beneficiario_id=r.beneficiario_id, data=r.data,
                presente=r.presente, registrado_por_id=r.registrado_por_id,
                falta_justificada=r.falta_justificada, justificativa=r.justificativa,
            ).on_conflict_do_update(
                index_elements=["turma_id", "beneficiario_id", "data"],
                set_={
                    "presente": r.presente, "registrado_por_id": r.registrado_por_id,
                    "falta_justificada": r.falta_justificada, "justificativa": r.justificativa,
                },
            ).returning(FrequenciaModel)
            m = self.db.execute(stmt).scalar_one()
            resultado.append(m)
        self.db.commit()
        return [_to_entity(m) for m in resultado]

    def listar_por_turma_e_data(self, turma_id: UUID, data_ref: date) -> list[RegistroFrequencia]:
        stmt = select(FrequenciaModel).where(
            FrequenciaModel.turma_id == turma_id, FrequenciaModel.data == data_ref
        )
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def listar_por_turma_e_periodo(self, turma_id: UUID, data_inicio: date, data_fim: date) -> list[RegistroFrequencia]:
        stmt = select(FrequenciaModel).where(
            FrequenciaModel.turma_id == turma_id,
            FrequenciaModel.data >= data_inicio,
            FrequenciaModel.data <= data_fim,
        )
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def listar_por_beneficiario(self, beneficiario_id: UUID) -> list[RegistroFrequencia]:
        stmt = select(FrequenciaModel).where(FrequenciaModel.beneficiario_id == beneficiario_id)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def listar_por_turmas_e_periodo(
        self, turma_ids: list[UUID], data_inicio: date, data_fim: date
    ) -> list[RegistroFrequencia]:
        """Frequências de várias turmas num período — usado nos relatórios agregados de polo."""
        if not turma_ids:
            return []
        stmt = select(FrequenciaModel).where(
            FrequenciaModel.turma_id.in_(turma_ids),
            FrequenciaModel.data >= data_inicio,
            FrequenciaModel.data <= data_fim,
        )
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def listar_por_periodo(self, data_inicio: date, data_fim: date) -> list[RegistroFrequencia]:
        """Todas as frequências (todos os polos/turmas) num período — usado no relatório geral do MASTER."""
        stmt = select(FrequenciaModel).where(
            FrequenciaModel.data >= data_inicio, FrequenciaModel.data <= data_fim
        )
        return [_to_entity(m) for m in self.db.scalars(stmt)]
