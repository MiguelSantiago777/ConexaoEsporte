"""DTOs de Autenticação — exibidos no Swagger sob a tag 'Autenticação'."""
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AlterarSenhaRequest(BaseModel):
    # senha_atual não leva min_length=8: é só comparada contra o hash existente,
    # que pode ter sido criado sob uma política de senha mais antiga/curta.
    senha_atual: str = Field(..., min_length=1)
    nova_senha: str = Field(..., min_length=8, examples=["nova-senha-forte-456"])


class UsuarioLogadoResponse(BaseModel):
    id: UUID
    nome: str
    email: EmailStr
    perfil: str
    polo_id: UUID | None = None
    polo_nome: str | None = None
    polo_codigo: str | None = None
    almoxarifado_id: UUID | None = None
    almoxarifado_nome: str | None = None
    # Só populado pra perfil PERSONALIZADO (ver Papel/Central de Acessos) — os
    # módulos do sistema que o Papel vinculado libera pra este usuário.
    modulos: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}
