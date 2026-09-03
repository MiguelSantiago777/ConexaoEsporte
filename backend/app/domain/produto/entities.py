from dataclasses import dataclass
from uuid import UUID


@dataclass
class Produto:
    """Item do catálogo central de Estoque (bolas, uniformes, materiais em
    geral) — a quantidade em si nunca fica neste registro; ela é sempre
    calculada a partir da soma dos Movimentos de Estoque (ver
    app/domain/estoque/entities.py)."""

    id: UUID | None
    nome: str
    unidade_medida: str
    descricao: str | None = None
    ativo: bool = True

    def __post_init__(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ValueError("Nome do Produto é obrigatório.")
        if not self.unidade_medida or not self.unidade_medida.strip():
            raise ValueError("Unidade de medida do Produto é obrigatória.")
