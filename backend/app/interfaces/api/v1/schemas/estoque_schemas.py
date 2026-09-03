"""DTOs de Movimento de Estoque (Entrada/Saída) e do Relatório de Estoque."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class MovimentoEstoqueResponse(BaseModel):
    id: UUID
    produto_id: UUID
    almoxarifado_id: UUID
    tipo: str  # ENTRADA | SAIDA
    quantidade: int
    data: date
    observacao: str | None
    entregue_por: str | None
    recebido_por: str | None
    nome_arquivo: str | None
    content_type: str | None
    tamanho_bytes: int | None
    entrega_material_id: UUID | None
    criado_por_id: UUID | None
    criado_em: datetime | None

    model_config = {"from_attributes": True}


class SaldoProdutoItem(BaseModel):
    produto_id: UUID
    produto_nome: str
    unidade_medida: str
    total_entradas: int
    total_saidas: int
    saldo_atual: int


class RelatorioEstoqueResponse(BaseModel):
    data_inicio: date
    data_fim: date
    total_produtos: int
    total_entradas_periodo: int
    total_saidas_periodo: int
    saldos: list[SaldoProdutoItem]
    movimentos: list[MovimentoEstoqueResponse]
