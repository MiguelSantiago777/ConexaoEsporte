"""Use casos de Entrega de Materiais (MASTER e GESTOR_POLO do próprio polo)."""
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entrega_material.entities import EntregaMaterial
from app.domain.shared.exceptions import RecursoNaoEncontrado
from app.infrastructure.repositories.entrega_material_repository import EntregaMaterialRepository
from app.infrastructure.repositories.polo_repository import PoloRepository


class EntregaMaterialService:
    def __init__(self, db: Session):
        self.repo = EntregaMaterialRepository(db)
        self.polo_repo = PoloRepository(db)

    def listar(self, polo_id: UUID | None = None) -> list[EntregaMaterial]:
        return self.repo.listar(polo_id=polo_id)

    def buscar(self, entrega_id: UUID) -> EntregaMaterial | None:
        return self.repo.buscar_por_id(entrega_id)

    def criar(
        self, polo_id: UUID, data_entrega: date | None, itens: list[dict], criado_por_id: UUID | None,
    ) -> EntregaMaterial:
        polo = self.polo_repo.buscar_por_id(polo_id)
        if not polo:
            raise RecursoNaoEncontrado("Polo não encontrado.")
        entrega = EntregaMaterial(
            id=None, polo_id=polo_id, data_entrega=data_entrega,
            coordenador_nome=polo.responsavel_nome, itens=itens, criado_por_id=criado_por_id,
        )
        return self.repo.criar(entrega)

    def atualizar(self, entrega_id: UUID, **campos) -> EntregaMaterial | None:
        return self.repo.atualizar(entrega_id, **campos)
