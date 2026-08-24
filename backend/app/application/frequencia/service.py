"""Use cases de Frequência: lançamento de chamada diária pelo Professor."""
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.frequencia.entities import RegistroFrequencia
from app.infrastructure.repositories.frequencia_repository import FrequenciaRepository


class FrequenciaService:
    def __init__(self, db: Session):
        self.repo = FrequenciaRepository(db)

    def registrar_chamada(
        self, turma_id: UUID, data_ref: date,
        presencas: list[tuple[UUID, bool]], registrado_por_id: UUID,
    ) -> list[RegistroFrequencia]:
        registros = [
            RegistroFrequencia(
                id=None, turma_id=turma_id, beneficiario_id=benef_id, data=data_ref,
                presente=presente, registrado_por_id=registrado_por_id,
            )
            for benef_id, presente in presencas
        ]
        return self.repo.registrar_chamada(registros)

    def listar_chamada(self, turma_id: UUID, data_ref: date) -> list[RegistroFrequencia]:
        return self.repo.listar_por_turma_e_data(turma_id, data_ref)
