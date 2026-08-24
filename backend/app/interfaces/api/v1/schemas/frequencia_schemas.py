"""DTOs de Frequência/Presença dos Beneficiários."""
from datetime import date
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
