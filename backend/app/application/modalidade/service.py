"""Use cases de Modalidade esportiva."""
from sqlalchemy.orm import Session

from app.domain.modalidade.entities import Modalidade
from app.infrastructure.repositories.modalidade_repository import ModalidadeRepository


class ModalidadeService:
    def __init__(self, db: Session):
        self.repo = ModalidadeRepository(db)

    def listar(self) -> list[Modalidade]:
        return self.repo.listar()

    def criar(self, nome: str, descricao: str | None) -> Modalidade:
        modalidade = Modalidade(id=None, nome=nome, descricao=descricao)
        return self.repo.criar(modalidade)
