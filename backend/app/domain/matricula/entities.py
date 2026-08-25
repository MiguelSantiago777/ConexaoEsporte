"""
Entidade de domínio MATRÍCULA — vínculo N:N entre um BENEFICIÁRIO e uma
TURMA. Um mesmo beneficiário pode ter várias matrículas ativas ao mesmo
tempo (ex.: judô numa turma e natação em outra); cada matrícula é
independente e pode ser encerrada sem afetar as demais.
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Matricula:
    id: UUID | None
    beneficiario_id: UUID
    turma_id: UUID
    ativo: bool = True
    criado_em: datetime | None = None
