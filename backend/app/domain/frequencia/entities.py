from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class RegistroFrequencia:
    id: UUID | None
    turma_id: UUID
    beneficiario_id: UUID
    data: date
    presente: bool
    registrado_por_id: UUID
    falta_justificada: bool = False
    justificativa: str | None = None


@dataclass
class ImpeditivoAula:
    """Dia em que a turma inteira não teve aula (feriado, ponto facultativo
    etc.) — diferente de falta individual, vale para todos os beneficiários
    matriculados naquela data."""

    id: UUID | None
    turma_id: UUID
    data: date
    justificativa: str
    criado_por_id: UUID | None = None
    criado_em: datetime | None = None


@dataclass
class ChamadaEvidencia:
    """Foto anexada a uma chamada (turma + data) comprovando que a aula aconteceu."""

    id: UUID | None
    turma_id: UUID
    data: date
    nome_arquivo: str
    caminho_arquivo: str
    content_type: str | None
    tamanho_bytes: int | None
    enviado_por_id: UUID | None
    criado_em: datetime | None = None
