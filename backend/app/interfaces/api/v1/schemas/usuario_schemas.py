"""DTOs de Usuário (funcionários: MASTER, GESTOR_POLO, PROFESSOR)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domain.enums import PerfilUsuario


class UsuarioCreateRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    senha: str | None = Field(
        default=None, min_length=8,
        description="Opcional: se omitida, o usuário recebe a senha temporária padrão e é obrigado a "
        "trocá-la no primeiro acesso.",
    )
    perfil: PerfilUsuario
    polo_id: UUID | None = Field(
        default=None, description="Obrigatório quando perfil = GESTOR_POLO ou PROFESSOR."
    )
    almoxarifado_id: UUID | None = Field(
        default=None, description="Obrigatório quando perfil = COORDENADOR_ALMOXARIFADO."
    )
    papel_id: UUID | None = Field(
        default=None, description="Obrigatório quando perfil = PERSONALIZADO (ver Central de Acessos)."
    )
    telefone: str | None = Field(default=None, max_length=20)
    cpf: str | None = Field(default=None, max_length=20)
    carga_horaria_semanal: str | None = Field(default=None, max_length=20, examples=["20h"])


class UsuarioUpdateRequest(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    ativo: bool | None = None
    polo_id: UUID | None = None
    almoxarifado_id: UUID | None = None
    papel_id: UUID | None = None
    telefone: str | None = Field(default=None, max_length=20)
    cpf: str | None = Field(default=None, max_length=20)
    carga_horaria_semanal: str | None = Field(default=None, max_length=20, examples=["20h"])


class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    email: EmailStr
    perfil: PerfilUsuario
    polo_id: UUID | None
    almoxarifado_id: UUID | None
    papel_id: UUID | None
    ativo: bool
    telefone: str | None
    cpf: str | None
    carga_horaria_semanal: str | None
    deve_trocar_senha: bool

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
