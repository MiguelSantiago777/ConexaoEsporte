"""DTOs de Turma."""
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

DIAS_VALIDOS = {"SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"}


class TurmaCreateRequest(BaseModel):
    polo_id: UUID
    modalidade_id: UUID
    professor_id: UUID | None = None
    horario_inicio: str = Field(..., examples=["08:00"])
    horario_fim: str = Field(..., examples=["09:30"])
    dias_semana: list[str] = Field(..., examples=[["SEG", "QUA", "SEX"]])
    limite_vagas: int = Field(..., gt=0, examples=[20])

    @field_validator("dias_semana")
    @classmethod
    def validar_dias(cls, v: list[str]) -> list[str]:
        invalidos = set(v) - DIAS_VALIDOS
        if invalidos:
            raise ValueError(f"Dias inválidos: {invalidos}. Use: {DIAS_VALIDOS}")
        return v


class TurmaUpdateRequest(BaseModel):
    professor_id: UUID | None = None
    horario_inicio: str | None = None
    horario_fim: str | None = None
    dias_semana: list[str] | None = None
    limite_vagas: int | None = Field(default=None, gt=0)


class TurmaResponse(BaseModel):
    id: UUID
    polo_id: UUID
    modalidade_id: UUID
    professor_id: UUID | None
    horario_inicio: str
    horario_fim: str
    dias_semana: list[str]
    limite_vagas: int
    vagas_ocupadas: int = 0

    model_config = {"from_attributes": True}
