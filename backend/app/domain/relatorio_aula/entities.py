from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass
class RelatorioAula:
    id: UUID | None
    turma_id: UUID
    professor_id: UUID
    data: date
    conteudo_trabalhado: str
    observacoes: str | None

    def __post_init__(self) -> None:
        if not self.conteudo_trabalhado or not self.conteudo_trabalhado.strip():
            raise ValueError("Conteúdo trabalhado é obrigatório no Relatório de Aula.")
