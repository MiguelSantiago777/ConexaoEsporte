"""DTOs dos relatórios agregados (gráficos) do Polo e gerais (MASTER)."""
from datetime import date
from uuid import UUID

from pydantic import BaseModel


class SeriePonto(BaseModel):
    """Um ponto de série para gráfico (pizza, barra ou linha): rótulo + valor."""

    label: str
    valor: float


class KPIsPolo(BaseModel):
    beneficiarios_ativos: int
    turmas_ativas: int
    frequencia_media_pct: float
    aulas_registradas: int
    fotos_evidencia: int


class RelatorioPoloResponse(BaseModel):
    polo_id: UUID
    polo_nome: str
    data_inicio: date
    data_fim: date
    kpis: KPIsPolo
    beneficiarios_por_modalidade: list[SeriePonto]
    frequencia_por_semana: list[SeriePonto]
    frequencia_por_turma: list[SeriePonto]


class KPIsGeral(BaseModel):
    total_polos: int
    total_beneficiarios_ativos: int
    total_turmas_ativas: int
    frequencia_media_pct: float


class RankingPolo(BaseModel):
    polo_id: UUID
    polo_nome: str
    frequencia_media_pct: float
    beneficiarios_ativos: int


class RelatorioGeralResponse(BaseModel):
    data_inicio: date
    data_fim: date
    kpis: KPIsGeral
    beneficiarios_por_polo: list[SeriePonto]
    frequencia_por_semana: list[SeriePonto]
    ranking_polos: list[RankingPolo]
