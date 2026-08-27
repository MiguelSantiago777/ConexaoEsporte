"""DTOs de Frequência/Presença dos Beneficiários."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RegistroPresencaItem(BaseModel):
    beneficiario_id: UUID
    presente: bool


class ChamadaCreateRequest(BaseModel):
    """Lançamento de chamada em lote para uma Turma em uma data."""

    turma_id: UUID
    data: date
    presencas: list[RegistroPresencaItem] = Field(..., min_length=1)


class FrequenciaResponse(BaseModel):
    id: UUID
    turma_id: UUID
    beneficiario_id: UUID
    data: date
    presente: bool
    registrado_por_id: UUID

    model_config = {"from_attributes": True}


class ChamadaEvidenciaResponse(BaseModel):
    """Foto anexada a uma chamada (turma + data) comprovando que a aula aconteceu."""

    id: UUID
    turma_id: UUID
    data: date
    nome_arquivo: str
    content_type: str | None
    tamanho_bytes: int | None
    enviado_por_id: UUID | None
    criado_em: datetime | None

    model_config = {"from_attributes": True}
