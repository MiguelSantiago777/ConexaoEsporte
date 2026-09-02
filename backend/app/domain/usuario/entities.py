from dataclasses import dataclass
from datetime import datetime
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
    telefone: str | None = None
    carga_horaria_semanal: str | None = None

    def __post_init__(self) -> None:
        if self.perfil == PerfilUsuario.GESTOR_POLO and self.polo_id is None:
            raise ValueError("GESTOR_POLO precisa estar vinculado a um polo_id.")


# Tipos de anexo aceitos no cadastro de professor.
TIPOS_DOCUMENTO_USUARIO = ("FOTO", "DOCUMENTO", "CONTRATO")


@dataclass
class UsuarioDocumento:
    """Anexo do cadastro de professor: foto, documento ou contrato."""

    id: UUID | None
    usuario_id: UUID
    tipo: str
    nome_arquivo: str
    caminho_arquivo: str
    content_type: str | None
    tamanho_bytes: int | None
    enviado_por_id: UUID | None
    criado_em: datetime | None = None

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS_DOCUMENTO_USUARIO:
            raise ValueError(f"Tipo de anexo inválido: {self.tipo}")
