from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class MovimentoEstoque:
    """Entrada ou Saída de um Produto no estoque central (único). A ENTRADA
    é lançada na tela de Estoque — no próprio cadastro do produto (quantidade
    inicial), pelo botão de entrada ou pela importação em planilha; o
    comprovante é opcional. A SAÍDA nasce de uma Baixa direta na tela de
    Estoque (com o polo de destino em `polo_id`) ou de um item de Entrega de
    Materiais que referencia o produto (rastreado em `entrega_material_id`)."""

    id: UUID | None
    produto_id: UUID
    almoxarifado_id: UUID | None  # None = estoque único (movimentos novos)
    tipo: str  # "ENTRADA" | "SAIDA"
    quantidade: int
    data: date
    polo_id: UUID | None = None
    observacao: str | None = None
    entregue_por: str | None = None
    recebido_por: str | None = None
    nome_arquivo: str | None = None
    caminho_arquivo: str | None = None
    content_type: str | None = None
    tamanho_bytes: int | None = None
    entrega_material_id: UUID | None = None
    criado_por_id: UUID | None = None
    criado_em: datetime | None = None

    def __post_init__(self) -> None:
        if self.tipo not in ("ENTRADA", "SAIDA"):
            raise ValueError("Tipo de movimento de estoque deve ser ENTRADA ou SAIDA.")
        if self.quantidade <= 0:
            raise ValueError("Quantidade do movimento de estoque deve ser positiva.")
