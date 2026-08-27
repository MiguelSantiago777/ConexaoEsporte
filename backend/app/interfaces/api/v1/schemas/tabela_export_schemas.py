"""DTO da exportação genérica de tabela(s) já prontas (o frontend já
filtrou/mascarou os dados conforme os toggles da tela) para .xlsx."""
from pydantic import BaseModel, Field


class AbaExportRequest(BaseModel):
    nome: str = Field(..., min_length=1, max_length=31, description="Vira o nome da aba no Excel.")
    colunas: list[str] = Field(..., min_length=1)
    linhas: list[list[str | int | float | None]] = Field(default_factory=list)


class TabelaExportRequest(BaseModel):
    titulo: str | None = Field(default=None, max_length=150)
    abas: list[AbaExportRequest] = Field(..., min_length=1, max_length=20)
