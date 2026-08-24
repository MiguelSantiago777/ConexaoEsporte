from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass
class RegistroFrequencia:
    id: UUID | None
    turma_id: UUID
    beneficiario_id: UUID
    data: date
    presente: bool
    registrado_por_id: UUID
