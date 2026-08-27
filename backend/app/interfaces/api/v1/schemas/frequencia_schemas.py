"""DTOs de Frequência/Presença dos Beneficiários."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RegistroPresencaItem(BaseModel):
    beneficiario_id: UUID
    presente: bool
    falta_justificada: bool = False
    justificativa: str | None = None


class ChamadaCreateRequest(BaseModel):
    """Lançamento de chamada em lote para uma Turma em uma data."""

    turma_id: UUID
    data: date
    presencas: list[RegistroPresencaItem] = Field(..., min_length=1)


class FrequenciaResponse(BaseModel):
    id: UUID
    turma_id: UUID
    beneficiario_id: UUID
    data: date
    presente: bool
    falta_justificada: bool
    justificativa: str | None
    registrado_por_id: UUID

    model_config = {"from_attributes": True}


class ChamadaEvidenciaResponse(BaseModel):
    """Foto anexada a uma chamada (turma + data) comprovando que a aula aconteceu."""

    id: UUID
    turma_id: UUID
    data: date
    nome_arquivo: str
    content_type: str | None
    tamanho_bytes: int | None
    enviado_por_id: UUID | None
    criado_em: datetime | None

    model_config = {"from_attributes": True}


class ImpeditivoAulaCreateRequest(BaseModel):
    turma_id: UUID
    data: date
    justificativa: str = Field(..., min_length=1, max_length=500)


class ImpeditivoAulaResponse(BaseModel):
    id: UUID
    turma_id: UUID
    data: date
    justificativa: str
    criado_por_id: UUID | None
    criado_em: datetime | None

    model_config = {"from_attributes": True}


# --- Ficha de Chamada (relatório agregado mensal) -----------------------

StatusDia = str
"""Um de: PRESENTE, FALTA, FALTA_JUSTIFICADA, IMPEDITIVO, SEM_MARCACAO."""


class LinhaFichaChamada(BaseModel):
    beneficiario_id: UUID
    nome: str
    idade: int | None
    status_por_data: dict[str, StatusDia]  # chave = data ISO (YYYY-MM-DD)
    frequencia_pct: float


class ResumoFichaChamada(BaseModel):
    presenca: int
    falta: int
    falta_justificada: int
    impeditivo: int
    sem_marcacao: int
    total: int


class FichaChamadaResponse(BaseModel):
    turma_id: UUID
    polo_nome: str
    modalidade_nome: str
    professor_nome: str | None
    horario_inicio: str
    horario_fim: str
    dias_semana: list[str]
    faixa_etaria_min: int | None
    faixa_etaria_max: int | None
    mes: int
    ano: int
    datas: list[date]
    linhas: list[LinhaFichaChamada]
    impeditivos: list[ImpeditivoAulaResponse]
    resumo: ResumoFichaChamada
