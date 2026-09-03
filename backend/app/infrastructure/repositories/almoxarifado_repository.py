"""Repositório de Almoxarifado (locais físicos do estoque central)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.almoxarifado.entities import Almoxarifado
from app.infrastructure.database.models import AlmoxarifadoModel
from app.infrastructure.repositories.paginacao import paginar


def _to_entity(m: AlmoxarifadoModel) -> Almoxarifado:
    return Almoxarifado(id=m.id, nome=m.nome, descricao=m.descricao, ativo=m.ativo)


class AlmoxarifadoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, apenas_ativos: bool = False) -> list[Almoxarifado]:
        stmt = select(AlmoxarifadoModel).order_by(AlmoxarifadoModel.nome)
        if apenas_ativos:
            stmt = stmt.where(AlmoxarifadoModel.ativo.is_(True))
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def listar_pagina(self, pagina: int, tamanho_pagina: int, nome: str | None = None) -> tuple[list[Almoxarifado], int]:
        stmt = select(AlmoxarifadoModel)
        if nome:
            stmt = stmt.where(AlmoxarifadoModel.nome.ilike(f"%{nome}%"))
        stmt = stmt.order_by(AlmoxarifadoModel.nome)
        modelos, total = paginar(self.db, stmt, pagina, tamanho_pagina)
        return [_to_entity(m) for m in modelos], total

    def buscar_por_id(self, almoxarifado_id: UUID) -> Almoxarifado | None:
        m = self.db.get(AlmoxarifadoModel, almoxarifado_id)
        return _to_entity(m) if m else None

    def criar(self, almoxarifado: Almoxarifado) -> Almoxarifado:
        m = AlmoxarifadoModel(nome=almoxarifado.nome, descricao=almoxarifado.descricao, ativo=almoxarifado.ativo)
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def atualizar(self, almoxarifado_id: UUID, **campos) -> Almoxarifado | None:
        m = self.db.get(AlmoxarifadoModel, almoxarifado_id)
        if not m:
            return None
        for k, v in campos.items():
            if v is not None:
                setattr(m, k, v)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def remover(self, almoxarifado_id: UUID) -> bool:
        m = self.db.get(AlmoxarifadoModel, almoxarifado_id)
        if not m:
            return False
        self.db.delete(m)
        self.db.commit()
        return True
