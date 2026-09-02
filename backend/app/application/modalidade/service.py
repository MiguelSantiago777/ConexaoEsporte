"""Use cases de Modalidade esportiva."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.modalidade.entities import Modalidade
from app.domain.shared.exceptions import RecursoNaoEncontrado, RegraDeNegocioViolada
from app.infrastructure.repositories.modalidade_repository import ModalidadeRepository
from app.infrastructure.repositories.turma_repository import TurmaRepository


class ModalidadeService:
    def __init__(self, db: Session):
        self.repo = ModalidadeRepository(db)
        self.turma_repo = TurmaRepository(db)

    def listar(self) -> list[Modalidade]:
        return self.repo.listar()

    def criar(self, nome: str, descricao: str | None) -> Modalidade:
        modalidade = Modalidade(id=None, nome=nome, descricao=descricao)
        return self.repo.criar(modalidade)

    def atualizar(self, modalidade_id: UUID, nome: str | None, descricao: str | None) -> Modalidade:
        atualizada = self.repo.atualizar(modalidade_id, nome=nome, descricao=descricao)
        if not atualizada:
            raise RecursoNaoEncontrado("Modalidade não encontrada.")
        return atualizada

    def remover(self, modalidade_id: UUID) -> None:
        if self.turma_repo.contar_por_modalidade(modalidade_id) > 0:
            raise RegraDeNegocioViolada(
                "Não é possível remover: existem turmas cadastradas com esta modalidade."
            )
        if not self.repo.remover(modalidade_id):
            raise RecursoNaoEncontrado("Modalidade não encontrada.")
