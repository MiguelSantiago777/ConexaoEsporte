from dataclasses import dataclass
from uuid import UUID


@dataclass
class Turma:
    id: UUID | None
    polo_id: UUID
    modalidade_id: UUID
    professor_id: UUID | None
    horario_inicio: str
    horario_fim: str
    dias_semana: list[str]  # ex.: ["SEG", "QUA", "SEX"]
    limite_vagas: int
    coordenador_nome: str | None = None
    monitor_nome: str | None = None
    periodicidade: str | None = None  # ex.: "Semanal", "Fim de Semana" — usado na Lista de Presença

    def __post_init__(self) -> None:
        if self.limite_vagas <= 0:
            raise ValueError("Limite de vagas da Turma deve ser positivo.")
        if self.horario_inicio >= self.horario_fim:
            raise ValueError("Horário de início deve ser anterior ao horário de fim.")

    def tem_vaga_disponivel(self, total_beneficiarios_atuais: int) -> bool:
        return total_beneficiarios_atuais < self.limite_vagas
