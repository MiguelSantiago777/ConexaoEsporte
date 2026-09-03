from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class MovimentoEstoque:
    """Entrada ou Saída de um Produto no estoque central. A ENTRADA é
    lançada manualmente na tela de Estoque, com nota fiscal/comprovante em
    anexo. A SAÍDA nunca é lançada diretamente — ela nasce automaticamente
    quando um item de uma Entrega de Materiais referencia este produto (ver
    app/application/entrega_material/service.py), e por isso carrega
    `entrega_material_id` pra rastrear a origem."""

    id: UUID | None
    produto_id: UUID
    almoxarifado_id: UUID
    tipo: str  # "ENTRADA" | "SAIDA"
    quantidade: int
    data: date
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
