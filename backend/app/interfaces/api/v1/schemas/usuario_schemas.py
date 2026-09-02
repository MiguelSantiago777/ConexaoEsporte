"""DTOs de Usuário (funcionários: MASTER, GESTOR_POLO, PROFESSOR)."""
from datetime import datetime
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
    telefone: str | None = Field(default=None, max_length=20)
    carga_horaria_semanal: str | None = Field(default=None, max_length=20, examples=["20h"])


class UsuarioUpdateRequest(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    ativo: bool | None = None
    polo_id: UUID | None = None
    telefone: str | None = Field(default=None, max_length=20)
    carga_horaria_semanal: str | None = Field(default=None, max_length=20, examples=["20h"])


class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    email: EmailStr
    perfil: PerfilUsuario
    polo_id: UUID | None
    ativo: bool
    telefone: str | None
    carga_horaria_semanal: str | None

    model_config = {"from_attributes": True}


class UsuarioDocumentoResponse(BaseModel):
    id: UUID
    usuario_id: UUID
    tipo: str
    nome_arquivo: str
    content_type: str | None
    tamanho_bytes: int | None
    criado_em: datetime | None

    model_config = {"from_attributes": True}
