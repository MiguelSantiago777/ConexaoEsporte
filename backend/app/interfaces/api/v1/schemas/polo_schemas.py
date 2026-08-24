"""DTOs de Polo."""
from uuid import UUID

from pydantic import BaseModel, Field


class PoloCreateRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150, examples=["Polo Zona Norte"])
    endereco: str | None = Field(default=None, max_length=255)
    gestor_responsavel_id: UUID | None = Field(
        default=None, description="ID do usuário GESTOR_POLO responsável (pode ser vinculado depois)."
    )


class PoloUpdateRequest(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    endereco: str | None = None
    status: str | None = Field(default=None, description="ATIVO ou INATIVO")
    gestor_responsavel_id: UUID | None = None


class PoloResponse(BaseModel):
    id: UUID
    nome: str
    endereco: str | None
    status: str
    gestor_responsavel_id: UUID | None

    model_config = {"from_attributes": True}
