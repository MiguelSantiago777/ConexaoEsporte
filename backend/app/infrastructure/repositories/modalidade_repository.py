"""Repositório de Modalidade."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.modalidade.entities import Modalidade
from app.infrastructure.database.models import ModalidadeModel


def _to_entity(m: ModalidadeModel) -> Modalidade:
    return Modalidade(id=m.id, nome=m.nome, descricao=m.descricao)


class ModalidadeRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self) -> list[Modalidade]:
        return [_to_entity(m) for m in self.db.scalars(select(ModalidadeModel).order_by(ModalidadeModel.nome))]

    def buscar_por_id(self, modalidade_id: UUID) -> Modalidade | None:
        m = self.db.get(ModalidadeModel, modalidade_id)
        return _to_entity(m) if m else None

    def criar(self, modalidade: Modalidade) -> Modalidade:
        m = ModalidadeModel(nome=modalidade.nome, descricao=modalidade.descricao)
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def atualizar(self, modalidade_id: UUID, **campos) -> Modalidade | None:
        m = self.db.get(ModalidadeModel, modalidade_id)
        if not m:
            return None
        for k, v in campos.items():
            if v is not None:
                setattr(m, k, v)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def remover(self, modalidade_id: UUID) -> bool:
        m = self.db.get(ModalidadeModel, modalidade_id)
        if not m:
            return False
        self.db.delete(m)
        self.db.commit()
        return True
