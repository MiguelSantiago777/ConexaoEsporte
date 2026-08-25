"""
DTOs de BENEFICIÁRIO — nomenclatura oficial do sistema.
Em nenhuma hipótese usar "aluno" aqui ou em qualquer outro lugar do código.

Modalidade/turma NÃO fazem parte do cadastro do beneficiário — um mesmo
beneficiário pode estar matriculado em várias turmas/modalidades ao mesmo
tempo, então isso é tratado à parte via matricula_schemas.py.
"""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BeneficiarioCreateRequest(BaseModel):
    nome_completo: str = Field(..., min_length=2, max_length=150)
    data_nascimento: date
    documento: str = Field(..., min_length=5, max_length=20, description="CPF ou outro documento de identificação")
    polo_id: UUID = Field(..., description="Polo ao qual o beneficiário pertence.")
    responsavel_legal_nome: str | None = None
    responsavel_legal_data_nascimento: date | None = None
    responsavel_legal_tipo_relacao: str | None = None
    responsavel_legal_telefone_1: str | None = None
    responsavel_legal_telefone_2: str | None = None
    responsavel_legal_email: str | None = None
    responsavel_legal_rede_social: str | None = None
    endereco: str | None = None
    autoriza_whatsapp: bool = False
    observacoes_medicas: str | None = Field(
        default=None, description="Alergias, restrições, condições médicas relevantes."
    )


class BeneficiarioUpdateRequest(BaseModel):
    nome_completo: str | None = Field(default=None, min_length=2, max_length=150)
    polo_id: UUID | None = None
    responsavel_legal_nome: str | None = None
    responsavel_legal_data_nascimento: date | None = None
    responsavel_legal_tipo_relacao: str | None = None
    responsavel_legal_telefone_1: str | None = None
    responsavel_legal_telefone_2: str | None = None
    responsavel_legal_email: str | None = None
    responsavel_legal_rede_social: str | None = None
    endereco: str | None = None
    autoriza_whatsapp: bool | None = None
    observacoes_medicas: str | None = None
    ativo: bool | None = None


class BeneficiarioResponse(BaseModel):
    id: UUID
    nome_completo: str
    data_nascimento: date
    documento: str
    polo_id: UUID | None
    responsavel_legal_nome: str | None
    responsavel_legal_data_nascimento: date | None
    responsavel_legal_tipo_relacao: str | None
    responsavel_legal_telefone_1: str | None
    responsavel_legal_telefone_2: str | None
    responsavel_legal_email: str | None
    responsavel_legal_rede_social: str | None
    endereco: str | None
    autoriza_whatsapp: bool
    observacoes_medicas: str | None
    ativo: bool

    model_config = {"from_attributes": True}


class BeneficiarioDocumentoResponse(BaseModel):
    id: UUID
    beneficiario_id: UUID
    tipo: str
    nome_arquivo: str
    content_type: str | None
    tamanho_bytes: int | None
    criado_em: datetime | None

    model_config = {"from_attributes": True}
