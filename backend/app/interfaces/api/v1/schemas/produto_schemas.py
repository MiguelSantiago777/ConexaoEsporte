"""DTOs de Produto (catálogo central de Estoque)."""
from uuid import UUID

from pydantic import BaseModel, Field


class ProdutoCreateRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150, examples=["Bola de futebol"])
    unidade_medida: str = Field(..., min_length=1, max_length=30, examples=["unidade", "par", "caixa"])
    descricao: str | None = None


class ProdutoUpdateRequest(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    unidade_medida: str | None = Field(default=None, min_length=1, max_length=30)
    descricao: str | None = None
    ativo: bool | None = None


class ProdutoResponse(BaseModel):
    id: UUID
    nome: str
    unidade_medida: str
    descricao: str | None
    ativo: bool
    saldo_atual: int = 0

    model_config = {"from_attributes": True}


class SaldoAlmoxarifadoItem(BaseModel):
    """Saldo de um Produto num almoxarifado específico — usado pro
    detalhamento no catálogo e pras opções de Saída na Entrega de
    Materiais, já que o mesmo produto pode ter saldos diferentes em cada
    almoxarifado."""

    almoxarifado_id: UUID
    almoxarifado_nome: str
    saldo: int


class SaldoProdutoNoAlmoxarifadoItem(BaseModel):
    """Inverso do item acima: saldo de um Produto num almoxarifado
    específico já conhecido (dashboard do Coordenador de Almoxarifado)."""

    produto_id: UUID
    produto_nome: str
    unidade_medida: str
    saldo: int
