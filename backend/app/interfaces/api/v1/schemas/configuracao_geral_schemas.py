"""DTOs da Configuração Geral: nome do projeto, número de convênio, datas
do projeto e Termo de Fomento (entidade parceira, CNPJ, vigência, valores,
parlamentar/emenda e termos aditivos) — um só registro pra todo o projeto,
já que a entidade parceira é a mesma em todos os polos. O representante
legal fica no cadastro de Polo (polo_schemas.py), não aqui."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TermoAditivoItem(BaseModel):
    numero: str
    objeto: str = ""
    data_assinatura: date | None = None


class ConfiguracaoGeralUpdateRequest(BaseModel):
    nome_projeto: str | None = Field(default=None, max_length=200)
    numero_convenio: str | None = Field(default=None, max_length=100)
    data_inicio_projeto: date | None = None
    data_fim_projeto: date | None = None

    # Termo de Fomento — dados da entidade parceira, únicos pro projeto inteiro.
    processo_sei: str | None = Field(default=None, max_length=50)
    termo_fomento_numero: str | None = Field(default=None, max_length=50)
    nome_entidade: str | None = Field(default=None, max_length=150)
    cnpj: str | None = Field(default=None, max_length=20)
    objeto: str | None = None
    vigencia_inicio: date | None = None
    vigencia_fim: date | None = None
    valor_pactuado: str | None = Field(default=None, max_length=50)
    valor_executado: str | None = Field(default=None, max_length=50)
    parlamentar: str | None = Field(default=None, max_length=150)
    emenda: str | None = Field(default=None, max_length=100)
    termos_aditivos: list[TermoAditivoItem] = Field(default_factory=list, max_length=2)


class ConfiguracaoGeralResponse(BaseModel):
    nome_projeto: str | None
    numero_convenio: str | None
    data_inicio_projeto: date | None
    data_fim_projeto: date | None
    processo_sei: str | None
    termo_fomento_numero: str | None
    nome_entidade: str | None
    cnpj: str | None
    objeto: str | None
    vigencia_inicio: date | None
    vigencia_fim: date | None
    valor_pactuado: str | None
    valor_executado: str | None
    parlamentar: str | None
    emenda: str | None
    termos_aditivos: list[TermoAditivoItem]
    atualizado_por_id: UUID | None
    atualizado_em: datetime | None

    model_config = {"from_attributes": True}
