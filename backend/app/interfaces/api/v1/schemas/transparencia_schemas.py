"""DTOs do Portal Transparência: resumo público (execução física +
financeiro + documentos, sem autenticação) e CRUD de Lançamentos
Financeiros (exclusivo do MASTER)."""
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

TipoLancamento = Literal["REPASSE", "EXECUCAO"]


class LancamentoFinanceiroCreateRequest(BaseModel):
    categoria: str = Field(min_length=1, max_length=100)
    tipo: TipoLancamento
    valor: float = Field(gt=0)
    data_lancamento: date
    descricao: str | None = Field(default=None, max_length=500)
    polo_id: UUID | None = None


class LancamentoFinanceiroResponse(BaseModel):
    id: UUID
    polo_id: UUID | None
    categoria: str
    tipo: TipoLancamento
    valor: float
    data_lancamento: date
    descricao: str | None
    criado_em: datetime | None

    model_config = {"from_attributes": True}


class InstitucionalPublico(BaseModel):
    nome_projeto: str | None
    numero_convenio: str | None
    data_inicio_projeto: date | None
    data_fim_projeto: date | None


class ExecucaoFisicaPublica(BaseModel):
    total_polos: int
    total_modalidades: int
    total_turmas_ativas: int
    total_beneficiarios_ativos: int
    frequencia_media_pct: float


class ResumoFinanceiroCategoria(BaseModel):
    categoria: str
    repassado: float
    executado: float


class ResumoFinanceiroPublico(BaseModel):
    total_repassado: float
    total_executado: float
    saldo: float
    por_categoria: list[ResumoFinanceiroCategoria]


class DocumentoPublicoResponse(BaseModel):
    id: UUID
    titulo: str
    polo_nome: str
    nome_arquivo: str
    content_type: str | None
    criado_em: datetime | None


class PortalTransparenciaResponse(BaseModel):
    institucional: InstitucionalPublico
    execucao_fisica: ExecucaoFisicaPublica
    financeiro: ResumoFinanceiroPublico
    documentos: list[DocumentoPublicoResponse]
    atualizado_em: datetime
