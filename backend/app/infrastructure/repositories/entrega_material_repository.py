"""Repositório de Entrega de Materiais (Termo de Entrega de Materiais)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entrega_material.entities import EntregaMaterial
from app.infrastructure.database.models import EntregaMaterialModel
from app.infrastructure.repositories.paginacao import paginar


def _to_entity(m: EntregaMaterialModel) -> EntregaMaterial:
    return EntregaMaterial(
        id=m.id, polo_id=m.polo_id, data_entrega=m.data_entrega, coordenador_nome=m.coordenador_nome,
        entregue_por=m.entregue_por, itens=m.itens or [], criado_por_id=m.criado_por_id, criado_em=m.criado_em,
    )


class EntregaMaterialRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, polo_id: UUID | None = None) -> list[EntregaMaterial]:
        stmt = select(EntregaMaterialModel).order_by(EntregaMaterialModel.criado_em.desc())
        if polo_id:
            stmt = stmt.where(EntregaMaterialModel.polo_id == polo_id)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def listar_pagina(
        self, pagina: int, tamanho_pagina: int, polo_id: UUID | None = None,
    ) -> tuple[list[EntregaMaterial], int]:
        stmt = select(EntregaMaterialModel).order_by(EntregaMaterialModel.criado_em.desc())
        if polo_id:
            stmt = stmt.where(EntregaMaterialModel.polo_id == polo_id)
        modelos, total = paginar(self.db, stmt, pagina, tamanho_pagina)
        return [_to_entity(m) for m in modelos], total

    def buscar_por_id(self, entrega_id: UUID) -> EntregaMaterial | None:
        m = self.db.get(EntregaMaterialModel, entrega_id)
        return _to_entity(m) if m else None

    def criar(self, entrega: EntregaMaterial) -> EntregaMaterial:
        m = EntregaMaterialModel(
            polo_id=entrega.polo_id, data_entrega=entrega.data_entrega,
            coordenador_nome=entrega.coordenador_nome, entregue_por=entrega.entregue_por, itens=entrega.itens,
            criado_por_id=entrega.criado_por_id,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def atualizar(self, entrega_id: UUID, **campos) -> EntregaMaterial | None:
        m = self.db.get(EntregaMaterialModel, entrega_id)
        if not m:
            return None
        for k, v in campos.items():
            setattr(m, k, v)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)
