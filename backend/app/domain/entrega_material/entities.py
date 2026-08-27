from dataclasses import dataclass, field
from datetime import date
from uuid import UUID


@dataclass
class EntregaMaterial:
    """Termo de Entrega de Materiais — um registro por entrega física de
    materiais/uniformes ao núcleo (polo)."""

    id: UUID | None
    polo_id: UUID
    data_entrega: date | None
    coordenador_nome: str | None
    entregue_por: str | None = None
    itens: list[dict] = field(default_factory=list)  # [{"descricao": "...", "quantidade": "..."}]
    criado_por_id: UUID | None = None
    criado_em: object = None
