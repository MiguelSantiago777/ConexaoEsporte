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
