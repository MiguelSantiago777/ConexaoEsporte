from dataclasses import dataclass
from uuid import UUID


@dataclass
class Almoxarifado:
    """Um dos locais físicos onde o estoque central fica guardado (ex.:
    "Almoxarifado Central", "Almoxarifado Zona Norte"). Toda Entrada e Saída
    de um Produto acontece num almoxarifado específico, e o saldo do
    produto é controlado separadamente em cada um — ver
    `ProdutoRepository.saldo_atual`/`saldo_por_almoxarifado`."""

    id: UUID | None
    nome: str
    descricao: str | None = None
    ativo: bool = True

    def __post_init__(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ValueError("Nome do Almoxarifado é obrigatório.")
