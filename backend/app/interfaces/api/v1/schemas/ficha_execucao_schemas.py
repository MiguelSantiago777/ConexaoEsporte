"""DTOs de Ficha de Execução (Ficha Técnica de Execução da Entidade)."""
from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

AjusteStatus = Literal["NAO_SOLICITADO", "APROVADO", "NAO_APROVADO"]


class EtapaMetaItem(BaseModel):
    nome: str = ""
    previsto: str = ""
    executado: str = ""


class MetaItem(BaseModel):
    meta: str
    etapas: list[EtapaMetaItem] = Field(default_factory=list, max_length=5)


class AtividadeComparativoItem(BaseModel):
    item: str
    pactuado: str = ""
    executado: str = ""
    observacoes: str = ""


class ChecklistDocumentoItem(BaseModel):
    documento: str
    situacao: Literal["Inserido", "Não Inserido"] = "Não Inserido"
    observacao: str = ""


class FichaExecucaoCreateRequest(BaseModel):
    polo_id: UUID
    periodo_referencia: str = Field(..., min_length=2, max_length=100, examples=["1º Trimestre 2026"])
    data_documento: date | None = None


class FichaExecucaoUpdateRequest(BaseModel):
    valor_recebido_periodo: str | None = Field(default=None, max_length=50)
    valor_recebido_extenso: str | None = Field(default=None, max_length=255)
    data_recebimento: date | None = None
    ajuste_status: AjusteStatus | None = None
    ajuste_justificativa: str | None = None
    metas: list[MetaItem] | None = Field(default=None, max_length=2)
    atividades_comparativo: list[AtividadeComparativoItem] | None = Field(default=None, max_length=15)
    checklist_documentos: list[ChecklistDocumentoItem] | None = Field(default=None, max_length=16)
    periodo_inscricao_inicio: date | None = None
    periodo_inscricao_fim: date | None = None
    inscricao_todos_nucleos: bool | None = None
    qtd_inscritos: int | None = Field(default=None, ge=0)
    observacoes_inscricao: str | None = None
    quantitativo_beneficiados: str | None = Field(default=None, max_length=50)
    modalidades: str | None = Field(default=None, max_length=255)
    periodo_funcionamento: str | None = Field(default=None, max_length=50, examples=["MANHA,TARDE"])
    descricao_atividades: str | None = None
    dificuldades: str | None = None
    impactos_sociais: str | None = None
    consideracoes_finais: str | None = None


class FichaExecucaoResponse(BaseModel):
    id: UUID
    polo_id: UUID
    periodo_referencia: str
    data_documento: date | None
    valor_recebido_periodo: str | None
    valor_recebido_extenso: str | None
    data_recebimento: date | None
    ajuste_status: str
    ajuste_justificativa: str | None
    metas: list[MetaItem]
    atividades_comparativo: list[AtividadeComparativoItem]
    checklist_documentos: list[ChecklistDocumentoItem]
    periodo_inscricao_inicio: date | None
    periodo_inscricao_fim: date | None
    inscricao_todos_nucleos: bool | None
    qtd_inscritos: int | None
    observacoes_inscricao: str | None
    quantitativo_beneficiados: str | None
    modalidades: str | None
    periodo_funcionamento: str | None
    descricao_atividades: str | None
    dificuldades: str | None
    impactos_sociais: str | None
    consideracoes_finais: str | None
    criado_por_id: UUID | None

    model_config = {"from_attributes": True}
