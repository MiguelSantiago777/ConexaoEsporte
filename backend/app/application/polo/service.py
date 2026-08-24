"""Use cases de Polo (apenas MASTER cria/edita Polos)."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.polo.entities import Polo
from app.infrastructure.repositories.polo_repository import PoloRepository


class PoloService:
    def __init__(self, db: Session):
        self.repo = PoloRepository(db)

    def listar(self) -> list[Polo]:
        return self.repo.listar()

    def buscar(self, polo_id: UUID) -> Polo | None:
        return self.repo.buscar_por_id(polo_id)

    def criar(self, nome: str, endereco: str | None, gestor_responsavel_id: UUID | None) -> Polo:
        polo = Polo(id=None, nome=nome, endereco=endereco, status="ATIVO",
                    gestor_responsavel_id=gestor_responsavel_id)
        return self.repo.criar(polo)

    def atualizar(self, polo_id: UUID, **campos) -> Polo | None:
        return self.repo.atualizar(polo_id, **campos)
