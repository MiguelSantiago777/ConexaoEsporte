"""Repositório de Polo."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.polo.entities import Polo
from app.infrastructure.database.models import PoloModel


def _to_entity(m: PoloModel) -> Polo:
    return Polo(id=m.id, nome=m.nome, endereco=m.endereco, status=m.status,
                gestor_responsavel_id=m.gestor_responsavel_id)


class PoloRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self) -> list[Polo]:
        return [_to_entity(m) for m in self.db.scalars(select(PoloModel))]

    def buscar_por_id(self, polo_id: UUID) -> Polo | None:
        m = self.db.get(PoloModel, polo_id)
        return _to_entity(m) if m else None

    def criar(self, polo: Polo) -> Polo:
        m = PoloModel(nome=polo.nome, endereco=polo.endereco, status=polo.status,
                      gestor_responsavel_id=polo.gestor_responsavel_id)
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def atualizar(self, polo_id: UUID, **campos) -> Polo | None:
        m = self.db.get(PoloModel, polo_id)
        if not m:
            return None
        for k, v in campos.items():
            if v is not None:
                setattr(m, k, v)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)
