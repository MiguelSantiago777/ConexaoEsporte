from dataclasses import dataclass
from uuid import UUID


@dataclass
class Modalidade:
    id: UUID | None
    nome: str
    descricao: str | None

    def __post_init__(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ValueError("Nome da Modalidade é obrigatório.")
