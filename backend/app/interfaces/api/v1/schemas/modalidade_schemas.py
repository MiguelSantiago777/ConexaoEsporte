"""DTOs de Modalidade esportiva."""
from uuid import UUID

from pydantic import BaseModel, Field


class ModalidadeCreateRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100, examples=["Judô"])
    descricao: str | None = None


class ModalidadeUpdateRequest(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=100)
    descricao: str | None = None


class ModalidadeResponse(BaseModel):
    id: UUID
    nome: str
    descricao: str | None

    model_config = {"from_attributes": True}
