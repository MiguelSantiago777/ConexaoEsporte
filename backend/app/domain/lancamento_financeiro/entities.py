"""Entidade de domínio LANÇAMENTO FINANCEIRO — valor repassado ou executado
do Termo de Fomento, lançado manualmente pelo MASTER. Compõe o resumo
financeiro do Portal Transparência (ver app/application/transparencia/service.py)."""
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

TIPOS_VALIDOS = {"REPASSE", "EXECUCAO"}


@dataclass
class LancamentoFinanceiro:
    id: UUID | None
    categoria: str
    tipo: str
    valor: float
    data_lancamento: date
    descricao: str | None
    polo_id: UUID | None
    criado_por_id: UUID | None
    criado_em: datetime | None = None

    def __post_init__(self) -> None:
        if not self.categoria or not self.categoria.strip():
            raise ValueError("Categoria do lançamento é obrigatória.")
        if self.tipo not in TIPOS_VALIDOS:
            raise ValueError("Tipo de lançamento inválido. Use REPASSE ou EXECUCAO.")
        if self.valor <= 0:
            raise ValueError("Valor do lançamento deve ser maior que zero.")
