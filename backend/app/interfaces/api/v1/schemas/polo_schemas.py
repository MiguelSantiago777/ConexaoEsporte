"""DTOs de Polo."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PoloCreateRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150, examples=["Polo Zona Norte"])
    codigo: str | None = Field(
        default=None, max_length=20, examples=["ZN01"], description="Código curto de identificação do polo."
    )
    endereco: str | None = Field(default=None, max_length=255)
    horario_funcionamento: str | None = Field(
        default=None, max_length=100, examples=["Seg a Sex, 08h às 18h"], description="Horário de funcionamento do polo."
    )
    gestor_responsavel_id: UUID | None = Field(
        default=None, description="ID do usuário GESTOR_POLO responsável (pode ser vinculado depois)."
    )

    # Representante legal do polo, pro Termo de Responsabilidade — é por
    # polo (mais de um polo pode ter o mesmo representante, sem problema).
    representante_legal_nome: str | None = Field(default=None, max_length=150)
    representante_legal_cpf: str | None = Field(default=None, max_length=20)
    representante_legal_rg: str | None = Field(default=None, max_length=20)

    # Contato do núcleo para a seção "Identificação dos Núcleos" da Ficha
    responsavel_nome: str | None = Field(default=None, max_length=150)
    responsavel_email: str | None = Field(default=None, max_length=150)
    responsavel_telefone: str | None = Field(default=None, max_length=20)

    # Coordenadas do endereço, para exibir o polo no mapa do Dashboard.
    latitude: float | None = None
    longitude: float | None = None


class PoloUpdateRequest(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    codigo: str | None = Field(default=None, max_length=20)
    endereco: str | None = None
    horario_funcionamento: str | None = Field(default=None, max_length=100)
    status: Literal["ATIVO", "INATIVO"] | None = Field(default=None)
    gestor_responsavel_id: UUID | None = None

    representante_legal_nome: str | None = Field(default=None, max_length=150)
    representante_legal_cpf: str | None = Field(default=None, max_length=20)
    representante_legal_rg: str | None = Field(default=None, max_length=20)

    # Contato do núcleo para a seção "Identificação dos Núcleos" da Ficha
    responsavel_nome: str | None = Field(default=None, max_length=150)
    responsavel_email: str | None = Field(default=None, max_length=150)
    responsavel_telefone: str | None = Field(default=None, max_length=20)

    # Coordenadas do endereço, para exibir o polo no mapa do Dashboard.
    latitude: float | None = None
    longitude: float | None = None


class PoloResponse(BaseModel):
    id: UUID
    nome: str
    codigo: str | None
    endereco: str | None
    horario_funcionamento: str | None
    status: str
    gestor_responsavel_id: UUID | None

    representante_legal_nome: str | None
    representante_legal_cpf: str | None
    representante_legal_rg: str | None

    responsavel_nome: str | None
    responsavel_email: str | None
    responsavel_telefone: str | None
    latitude: float | None
    longitude: float | None

    model_config = {"from_attributes": True}


class LocalizarPoloResponse(BaseModel):
    """Resultado de `POST /polos/{id}/localizar` — o polo (já com latitude/
    longitude, se achou) e como foi a busca pelo endereço."""

    polo: PoloResponse
    situacao: Literal["localizado", "aproximado", "nao_encontrado"]
