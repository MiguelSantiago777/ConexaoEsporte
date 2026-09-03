"""Repositório de Papel (níveis de acesso personalizados da Central de Acessos)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.papel.entities import Papel
from app.infrastructure.database.models import PapelModel
from app.infrastructure.repositories.paginacao import paginar


def _to_entity(m: PapelModel) -> Papel:
    return Papel(id=m.id, nome=m.nome, descricao=m.descricao, modulos=list(m.modulos or []), ativo=m.ativo)


class PapelRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, apenas_ativos: bool = False) -> list[Papel]:
        stmt = select(PapelModel).order_by(PapelModel.nome)
        if apenas_ativos:
            stmt = stmt.where(PapelModel.ativo.is_(True))
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def listar_pagina(self, pagina: int, tamanho_pagina: int, nome: str | None = None) -> tuple[list[Papel], int]:
        stmt = select(PapelModel)
        if nome:
            stmt = stmt.where(PapelModel.nome.ilike(f"%{nome}%"))
        stmt = stmt.order_by(PapelModel.nome)
        modelos, total = paginar(self.db, stmt, pagina, tamanho_pagina)
        return [_to_entity(m) for m in modelos], total

    def buscar_por_id(self, papel_id: UUID) -> Papel | None:
        m = self.db.get(PapelModel, papel_id)
        return _to_entity(m) if m else None

    def criar(self, papel: Papel) -> Papel:
        m = PapelModel(nome=papel.nome, descricao=papel.descricao, modulos=papel.modulos, ativo=papel.ativo)
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def atualizar(self, papel_id: UUID, **campos) -> Papel | None:
        m = self.db.get(PapelModel, papel_id)
        if not m:
            return None
        for k, v in campos.items():
            if v is not None:
                setattr(m, k, v)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def remover(self, papel_id: UUID) -> bool:
        m = self.db.get(PapelModel, papel_id)
        if not m:
            return False
        self.db.delete(m)
        self.db.commit()
        return True

    def contar_usuarios_vinculados(self, papel_id: UUID) -> int:
        from app.infrastructure.database.models import UsuarioModel

        stmt = select(UsuarioModel).where(UsuarioModel.papel_id == papel_id)
        return len(list(self.db.scalars(stmt)))
