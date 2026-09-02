"""DTOs da Configuração Geral (nome do projeto, número de convênio e datas do projeto)."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ConfiguracaoGeralUpdateRequest(BaseModel):
    nome_projeto: str | None = Field(default=None, max_length=200)
    numero_convenio: str | None = Field(default=None, max_length=100)
    data_inicio_projeto: date | None = None
    data_fim_projeto: date | None = None


class ConfiguracaoGeralResponse(BaseModel):
    nome_projeto: str | None
    numero_convenio: str | None
    data_inicio_projeto: date | None
    data_fim_projeto: date | None
    atualizado_por_id: UUID | None
    atualizado_em: datetime | None

    model_config = {"from_attributes": True}
