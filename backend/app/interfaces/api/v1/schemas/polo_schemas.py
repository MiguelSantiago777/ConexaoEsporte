"""DTOs de Polo."""
from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class TermoAditivoItem(BaseModel):
    numero: str = Field(..., examples=["PRIMEIRO"])
    objeto: str = ""
    data_assinatura: date | None = None


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

    # Dados da parceria (Termo de Fomento) — cada polo é sua própria
    # entidade parceira para fins da Ficha Técnica de Execução. Todos
    # opcionais: o formulário de cadastro é em etapas e o MASTER pode
    # preencher só o básico e completar depois editando o polo.
    processo_sei: str | None = Field(default=None, max_length=50)
    termo_fomento_numero: str | None = Field(default=None, max_length=50)
    nome_entidade: str | None = Field(default=None, max_length=150)
    cnpj: str | None = Field(default=None, max_length=20)
    representante_legal_nome: str | None = Field(default=None, max_length=150)
    representante_legal_cpf: str | None = Field(default=None, max_length=20)
    objeto: str | None = None
    vigencia_inicio: date | None = None
    vigencia_fim: date | None = None
    valor_pactuado: str | None = Field(default=None, max_length=50, examples=["R$ 200.000,00"])
    valor_executado: str | None = Field(default=None, max_length=50, examples=["R$ 120.000,00"])
    parlamentar: str | None = Field(default=None, max_length=150)
    emenda: str | None = Field(default=None, max_length=100)
    termos_aditivos: list[TermoAditivoItem] = Field(
        default_factory=list, max_length=2, description="Até 2 aditivos — PRIMEIRO e SEGUNDO, como no modelo oficial."
    )

    # Contato do núcleo para a seção "Identificação dos Núcleos" da Ficha
    responsavel_nome: str | None = Field(default=None, max_length=150)
    responsavel_email: str | None = Field(default=None, max_length=150)
    responsavel_telefone: str | None = Field(default=None, max_length=20)

    # Dados pessoais do representante legal para o Termo de Responsabilidade
    representante_legal_rg: str | None = Field(default=None, max_length=20)
    representante_legal_endereco: str | None = Field(default=None, max_length=255)
    representante_legal_bairro: str | None = Field(default=None, max_length=100)
    representante_legal_cidade: str | None = Field(default=None, max_length=100)


class PoloUpdateRequest(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    codigo: str | None = Field(default=None, max_length=20)
    endereco: str | None = None
    horario_funcionamento: str | None = Field(default=None, max_length=100)
    status: Literal["ATIVO", "INATIVO"] | None = Field(default=None)
    gestor_responsavel_id: UUID | None = None

    # Dados da parceria (Termo de Fomento) — cada polo é sua própria
    # entidade parceira para fins da Ficha Técnica de Execução.
    processo_sei: str | None = Field(default=None, max_length=50)
    termo_fomento_numero: str | None = Field(default=None, max_length=50)
    nome_entidade: str | None = Field(default=None, max_length=150)
    cnpj: str | None = Field(default=None, max_length=20)
    representante_legal_nome: str | None = Field(default=None, max_length=150)
    representante_legal_cpf: str | None = Field(default=None, max_length=20)
    objeto: str | None = None
    vigencia_inicio: date | None = None
    vigencia_fim: date | None = None
    valor_pactuado: str | None = Field(default=None, max_length=50, examples=["R$ 200.000,00"])
    valor_executado: str | None = Field(default=None, max_length=50, examples=["R$ 120.000,00"])
    parlamentar: str | None = Field(default=None, max_length=150)
    emenda: str | None = Field(default=None, max_length=100)
    termos_aditivos: list[TermoAditivoItem] | None = Field(
        default=None, max_length=2, description="Até 2 aditivos — PRIMEIRO e SEGUNDO, como no modelo oficial."
    )

    # Contato do núcleo para a seção "Identificação dos Núcleos" da Ficha
    responsavel_nome: str | None = Field(default=None, max_length=150)
    responsavel_email: str | None = Field(default=None, max_length=150)
    responsavel_telefone: str | None = Field(default=None, max_length=20)

    # Dados pessoais do representante legal para o Termo de Responsabilidade
    representante_legal_rg: str | None = Field(default=None, max_length=20)
    representante_legal_endereco: str | None = Field(default=None, max_length=255)
    representante_legal_bairro: str | None = Field(default=None, max_length=100)
    representante_legal_cidade: str | None = Field(default=None, max_length=100)


class PoloResponse(BaseModel):
    id: UUID
    nome: str
    codigo: str | None
    endereco: str | None
    horario_funcionamento: str | None
    status: str
    gestor_responsavel_id: UUID | None

    processo_sei: str | None
    termo_fomento_numero: str | None
    nome_entidade: str | None
    cnpj: str | None
    representante_legal_nome: str | None
    representante_legal_cpf: str | None
    objeto: str | None
    vigencia_inicio: date | None
    vigencia_fim: date | None
    valor_pactuado: str | None
    valor_executado: str | None
    parlamentar: str | None
    emenda: str | None
    termos_aditivos: list[TermoAditivoItem]
    responsavel_nome: str | None
    responsavel_email: str | None
    responsavel_telefone: str | None
    representante_legal_rg: str | None
    representante_legal_endereco: str | None
    representante_legal_bairro: str | None
    representante_legal_cidade: str | None

    model_config = {"from_attributes": True}
