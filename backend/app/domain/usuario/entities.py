from dataclasses import dataclass
from uuid import UUID

from app.domain.enums import PerfilUsuario


@dataclass
class Usuario:
    id: UUID | None
    nome: str
    email: str
    senha_hash: str
    perfil: PerfilUsuario
    polo_id: UUID | None  # obrigatório apenas para GESTOR_POLO; usado também por PROFESSOR do polo
    ativo: bool = True

    def __post_init__(self) -> None:
        if self.perfil == PerfilUsuario.GESTOR_POLO and self.polo_id is None:
            raise ValueError("GESTOR_POLO precisa estar vinculado a um polo_id.")
