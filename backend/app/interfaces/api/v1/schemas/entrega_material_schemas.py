"""DTOs de Entrega de Materiais (Termo de Entrega de Materiais)."""
from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class ItemEntregaRequest(BaseModel):
    descricao: str = Field(..., min_length=1, max_length=255)
    quantidade: str = Field(..., min_length=1, max_length=20, examples=["10"])
    produto_id: UUID | None = Field(
        default=None,
        description="Quando informado, o item vem do catálogo de Estoque e a criação da entrega "
        "registra automaticamente uma Saída desse produto (quantidade precisa ser um inteiro).",
    )
    almoxarifado_id: UUID | None = Field(
        default=None,
        description="Obrigatório quando produto_id é informado — de qual almoxarifado a Saída sai.",
    )


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
    comprovante_nome_arquivo: str | None = None
    comprovante_content_type: str | None = None
    comprovante_tamanho_bytes: int | None = None
    criado_por_id: UUID | None

    model_config = {"from_attributes": True}
