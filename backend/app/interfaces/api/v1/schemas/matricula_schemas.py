"""DTOs de Matrícula (vínculo N:N beneficiário↔turma)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MatriculaCreateRequest(BaseModel):
    turma_id: UUID


class MatriculaResponse(BaseModel):
    id: UUID
    beneficiario_id: UUID
    turma_id: UUID
    ativo: bool
    criado_em: datetime | None

    model_config = {"from_attributes": True}
