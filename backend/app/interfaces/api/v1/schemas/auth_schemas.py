"""DTOs de Autenticação — exibidos no Swagger sob a tag 'Autenticação'."""
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["gestor.polo1@conexaoesporte.org"])
    senha: str = Field(..., min_length=6, examples=["senha-forte-123"])


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UsuarioLogadoResponse(BaseModel):
    id: UUID
    nome: str
    email: EmailStr
    perfil: str
    polo_id: UUID | None = None

    model_config = {"from_attributes": True}
