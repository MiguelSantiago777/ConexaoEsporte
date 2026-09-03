"""DTOs de Almoxarifado (locais físicos do estoque central)."""
from uuid import UUID

from pydantic import BaseModel, Field


class AlmoxarifadoCreateRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150, examples=["Almoxarifado Central"])
    descricao: str | None = None


class AlmoxarifadoUpdateRequest(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    descricao: str | None = None
    ativo: bool | None = None


class AlmoxarifadoResponse(BaseModel):
    id: UUID
    nome: str
    descricao: str | None
    ativo: bool

    model_config = {"from_attributes": True}
