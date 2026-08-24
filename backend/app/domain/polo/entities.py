from dataclasses import dataclass
from uuid import UUID


@dataclass
class Polo:
    id: UUID | None
    nome: str
    endereco: str | None
    status: str  # "ATIVO" | "INATIVO"
    gestor_responsavel_id: UUID | None

    def __post_init__(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ValueError("Nome do Polo é obrigatório.")
        if self.status not in ("ATIVO", "INATIVO"):
            raise ValueError("Status do Polo deve ser ATIVO ou INATIVO.")
