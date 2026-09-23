"""DTOs da Lista de Espera. Tag Swagger: 'Lista de Espera'."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class InscricaoListaEsperaCreateRequest(BaseModel):
    nome_completo: str = Field(..., min_length=1, max_length=150)
    data_nascimento: date
    documento: str = Field(..., min_length=5, max_length=20, examples=["12345678900"])
    nome_responsavel: str | None = Field(default=None, max_length=150)
    documento_responsavel: str | None = Field(default=None, max_length=20, examples=["12345678900"])
    telefone_whatsapp: str = Field(..., min_length=1, max_length=20, examples=["(11) 91234-5678"])
    email: EmailStr
    bairro: str | None = Field(default=None, max_length=100)
    cidade: str | None = Field(default=None, max_length=100)
    modalidade_id: UUID
    polo_id: UUID
    como_conheceu: str | None = Field(default=None, max_length=200)
    tamanho_camisa: str | None = Field(default=None, max_length=5, examples=["10", "M"])
    tamanho_calcado: str | None = Field(default=None, max_length=3, examples=["34"])


class InscricaoListaEsperaResponse(BaseModel):
    id: UUID
    nome_completo: str
    data_nascimento: date
    documento: str
    nome_responsavel: str | None
    documento_responsavel: str | None
    telefone_whatsapp: str
    email: str
    bairro: str | None
    cidade: str | None
    modalidade_id: UUID
    polo_id: UUID
    como_conheceu: str | None
    tamanho_camisa: str | None
    tamanho_calcado: str | None
    criado_em: datetime | None

    model_config = {"from_attributes": True}


class OpcaoResponse(BaseModel):
    id: UUID
    nome: str


class OpcoesPublicasResponse(BaseModel):
    polos: list[OpcaoResponse]
    modalidades: list[OpcaoResponse]


class AceitarInscricaoRequest(BaseModel):
    turma_id: UUID
