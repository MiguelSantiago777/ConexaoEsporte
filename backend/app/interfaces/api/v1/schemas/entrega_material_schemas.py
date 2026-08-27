"""DTOs de Entrega de Materiais (Termo de Entrega de Materiais)."""
from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class ItemEntregaRequest(BaseModel):
    descricao: str = Field(..., min_length=1, max_length=255)
    quantidade: str = Field(..., min_length=1, max_length=20, examples=["10"])


class EntregaMaterialCreateRequest(BaseModel):
    polo_id: UUID
    data_entrega: date | None = None
    entregue_por: str | None = Field(default=None, max_length=150, description="Nome de quem foi levar os materiais.")
    itens: list[ItemEntregaRequest] = Field(default_factory=list, max_length=18)


class EntregaMaterialUpdateRequest(BaseModel):
    data_entrega: date | None = None
    coordenador_nome: str | None = Field(default=None, max_length=150)
    entregue_por: str | None = Field(default=None, max_length=150)
    itens: list[ItemEntregaRequest] | None = Field(default=None, max_length=18)


class EntregaMaterialResponse(BaseModel):
    id: UUID
    polo_id: UUID
    data_entrega: date | None
    coordenador_nome: str | None
    entregue_por: str | None
    itens: list[ItemEntregaRequest]
    criado_por_id: UUID | None

    model_config = {"from_attributes": True}
