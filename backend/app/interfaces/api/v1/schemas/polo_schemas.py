"""DTOs de Polo."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PoloCreateRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150, examples=["Polo Zona Norte"])
    codigo: str | None = Field(
        default=None, max_length=20, examples=["ZN01"], description="Código curto de identificação do polo."
    )
    endereco: str | None = Field(default=None, max_length=255)
    horario_funcionamento: str | None = Field(
        default=None, max_length=100, examples=["Seg a Sex, 08h às 18h"], description="Horário de funcionamento do polo."
    )
    gestor_responsavel_id: UUID | None = Field(
        default=None, description="ID do usuário GESTOR_POLO responsável (pode ser vinculado depois)."
    )


class PoloUpdateRequest(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    codigo: str | None = Field(default=None, max_length=20)
    endereco: str | None = None
    horario_funcionamento: str | None = Field(default=None, max_length=100)
    status: Literal["ATIVO", "INATIVO"] | None = Field(default=None)
    gestor_responsavel_id: UUID | None = None


class PoloResponse(BaseModel):
    id: UUID
    nome: str
    codigo: str | None
    endereco: str | None
    horario_funcionamento: str | None
    status: str
    gestor_responsavel_id: UUID | None

    model_config = {"from_attributes": True}
