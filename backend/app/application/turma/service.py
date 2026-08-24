"""Use cases de Turma."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.turma.entities import Turma
from app.infrastructure.repositories.turma_repository import TurmaRepository


class TurmaService:
    def __init__(self, db: Session):
        self.repo = TurmaRepository(db)

    def listar(self, polo_id: UUID | None = None, professor_id: UUID | None = None) -> list[dict]:
        turmas = self.repo.listar(polo_id=polo_id, professor_id=professor_id)
        return [self._com_vagas(t) for t in turmas]

    def buscar(self, turma_id: UUID) -> dict | None:
        t = self.repo.buscar_por_id(turma_id)
        return self._com_vagas(t) if t else None

    def criar(
        self, polo_id: UUID, modalidade_id: UUID, professor_id: UUID | None,
        horario_inicio: str, horario_fim: str, dias_semana: list[str], limite_vagas: int,
    ) -> dict:
        turma = Turma(
            id=None, polo_id=polo_id, modalidade_id=modalidade_id, professor_id=professor_id,
            horario_inicio=horario_inicio, horario_fim=horario_fim,
            dias_semana=dias_semana, limite_vagas=limite_vagas,
        )
        criada = self.repo.criar(turma)
        return self._com_vagas(criada)

    def atualizar(self, turma_id: UUID, **campos) -> dict | None:
        t = self.repo.atualizar(turma_id, **campos)
        return self._com_vagas(t) if t else None

    def _com_vagas(self, turma: Turma) -> dict:
        ocupadas = self.repo.contar_beneficiarios_ativos(turma.id) if turma.id else 0
        return {
            "id": turma.id, "polo_id": turma.polo_id, "modalidade_id": turma.modalidade_id,
            "professor_id": turma.professor_id, "horario_inicio": turma.horario_inicio,
            "horario_fim": turma.horario_fim, "dias_semana": turma.dias_semana,
            "limite_vagas": turma.limite_vagas, "vagas_ocupadas": ocupadas,
        }
