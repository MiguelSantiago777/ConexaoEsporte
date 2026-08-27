"""Repositório das fotos de evidência anexadas a uma chamada (turma + data)."""
from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.frequencia.entities import ChamadaEvidencia
from app.infrastructure.database.models import ChamadaEvidenciaModel


def _to_entity(m: ChamadaEvidenciaModel) -> ChamadaEvidencia:
    return ChamadaEvidencia(
        id=m.id, turma_id=m.turma_id, data=m.data, nome_arquivo=m.nome_arquivo,
        caminho_arquivo=m.caminho_arquivo, content_type=m.content_type, tamanho_bytes=m.tamanho_bytes,
        enviado_por_id=m.enviado_por_id, criado_em=m.criado_em,
    )


class ChamadaEvidenciaRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_por_turma_e_data(self, turma_id: UUID, data_ref: date) -> list[ChamadaEvidencia]:
        stmt = select(ChamadaEvidenciaModel).where(
            ChamadaEvidenciaModel.turma_id == turma_id, ChamadaEvidenciaModel.data == data_ref
        )
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def buscar_por_id(self, evidencia_id: UUID) -> ChamadaEvidencia | None:
        m = self.db.get(ChamadaEvidenciaModel, evidencia_id)
        return _to_entity(m) if m else None

    def contar_por_turmas_e_periodo(self, turma_ids: list[UUID], data_inicio: date, data_fim: date) -> int:
        if not turma_ids:
            return 0
        stmt = (
            select(func.count())
            .select_from(ChamadaEvidenciaModel)
            .where(
                ChamadaEvidenciaModel.turma_id.in_(turma_ids),
                ChamadaEvidenciaModel.data >= data_inicio,
                ChamadaEvidenciaModel.data <= data_fim,
            )
        )
        return self.db.scalar(stmt) or 0

    def criar(self, evidencia: ChamadaEvidencia) -> ChamadaEvidencia:
        m = ChamadaEvidenciaModel(
            turma_id=evidencia.turma_id, data=evidencia.data, nome_arquivo=evidencia.nome_arquivo,
            caminho_arquivo=evidencia.caminho_arquivo, content_type=evidencia.content_type,
            tamanho_bytes=evidencia.tamanho_bytes, enviado_por_id=evidencia.enviado_por_id,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def remover(self, evidencia_id: UUID) -> ChamadaEvidencia | None:
        m = self.db.get(ChamadaEvidenciaModel, evidencia_id)
        if not m:
            return None
        entidade = _to_entity(m)
        self.db.delete(m)
        self.db.commit()
        return entidade
