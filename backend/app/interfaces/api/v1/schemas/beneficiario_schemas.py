"""
DTOs de BENEFICIÁRIO — nomenclatura oficial do sistema.
Em nenhuma hipótese usar "aluno" aqui ou em qualquer outro lugar do código.
"""
from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class BeneficiarioCreateRequest(BaseModel):
    nome_completo: str = Field(..., min_length=2, max_length=150)
    data_nascimento: date
    documento: str = Field(..., min_length=5, max_length=20, description="CPF ou outro documento de identificação")
    responsavel_legal_nome: str | None = None
    responsavel_legal_contato: str | None = None
    contato: str | None = None
    endereco: str | None = None
    turma_id: UUID | None = None
    observacoes_medicas: str | None = Field(
        default=None, description="Alergias, restrições, condições médicas relevantes."
    )


class BeneficiarioUpdateRequest(BaseModel):
    nome_completo: str | None = Field(default=None, min_length=2, max_length=150)
    responsavel_legal_nome: str | None = None
    responsavel_legal_contato: str | None = None
    contato: str | None = None
    endereco: str | None = None
    turma_id: UUID | None = None
    observacoes_medicas: str | None = None
    ativo: bool | None = None


class BeneficiarioResponse(BaseModel):
    id: UUID
    nome_completo: str
    data_nascimento: date
    documento: str
    responsavel_legal_nome: str | None
    responsavel_legal_contato: str | None
    contato: str | None
    endereco: str | None
    turma_id: UUID | None
    observacoes_medicas: str | None
    ativo: bool

    model_config = {"from_attributes": True}
