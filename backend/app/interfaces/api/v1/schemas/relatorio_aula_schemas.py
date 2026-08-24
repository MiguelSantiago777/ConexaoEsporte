"""DTOs de Relatório de Aula."""
from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class RelatorioAulaCreateRequest(BaseModel):
    turma_id: UUID
    data: date
    conteudo_trabalhado: str = Field(..., min_length=3)
    observacoes: str | None = None


class RelatorioAulaResponse(BaseModel):
    id: UUID
    turma_id: UUID
    professor_id: UUID
    data: date
    conteudo_trabalhado: str
    observacoes: str | None

    model_config = {"from_attributes": True}
