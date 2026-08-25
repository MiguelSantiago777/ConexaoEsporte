"""DTOs de Usuário (funcionários: MASTER, GESTOR_POLO, PROFESSOR)."""
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domain.enums import PerfilUsuario


class UsuarioCreateRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    senha: str = Field(..., min_length=8)
    perfil: PerfilUsuario
    polo_id: UUID | None = Field(
        default=None, description="Obrigatório quando perfil = GESTOR_POLO ou PROFESSOR."
    )


class UsuarioUpdateRequest(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    ativo: bool | None = None
    polo_id: UUID | None = None


class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    email: EmailStr
    perfil: PerfilUsuario
    polo_id: UUID | None
    ativo: bool

    model_config = {"from_attributes": True}
