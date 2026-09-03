"""DTOs de Papel (Central de Acessos — níveis de acesso personalizados)."""
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.domain.enums.modulo_sistema import MODULOS_SISTEMA


def _validar_modulos(modulos: list[str]) -> list[str]:
    invalidos = [m for m in modulos if m not in MODULOS_SISTEMA]
    if invalidos:
        raise ValueError(f"Módulo(s) inválido(s): {', '.join(invalidos)}.")
    return modulos


class PapelCreateRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150, examples=["Financeiro"])
    descricao: str | None = None
    modulos: list[str] = Field(default_factory=list)

    @field_validator("modulos")
    @classmethod
    def _checar_modulos(cls, v: list[str]) -> list[str]:
        return _validar_modulos(v)


class PapelUpdateRequest(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    descricao: str | None = None
    modulos: list[str] | None = None
    ativo: bool | None = None

    @field_validator("modulos")
    @classmethod
    def _checar_modulos(cls, v: list[str] | None) -> list[str] | None:
        return _validar_modulos(v) if v is not None else v


class PapelResponse(BaseModel):
    id: UUID
    nome: str
    descricao: str | None
    modulos: list[str]
    ativo: bool

    model_config = {"from_attributes": True}


class ModuloDisponivelItem(BaseModel):
    chave: str
    label: str
