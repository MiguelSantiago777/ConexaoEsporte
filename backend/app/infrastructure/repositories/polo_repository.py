"""Repositório de Polo."""
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domain.polo.entities import Polo
from app.infrastructure.database.models import PoloModel
from app.infrastructure.repositories.paginacao import paginar


def _to_entity(m: PoloModel) -> Polo:
    return Polo(
        id=m.id, nome=m.nome, codigo=m.codigo, endereco=m.endereco,
        horario_funcionamento=m.horario_funcionamento, status=m.status,
        gestor_responsavel_id=m.gestor_responsavel_id,
        representante_legal_nome=m.representante_legal_nome,
        representante_legal_cpf=m.representante_legal_cpf,
        representante_legal_rg=m.representante_legal_rg,
        responsavel_nome=m.responsavel_nome, responsavel_email=m.responsavel_email,
        responsavel_telefone=m.responsavel_telefone,
        latitude=m.latitude, longitude=m.longitude,
    )


class PoloRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self) -> list[Polo]:
        return [_to_entity(m) for m in self.db.scalars(select(PoloModel))]

    def listar_pagina(self, pagina: int, tamanho_pagina: int, nome: str | None = None) -> tuple[list[Polo], int]:
        stmt = select(PoloModel)
        if nome:
            stmt = stmt.where(PoloModel.nome.ilike(f"%{nome}%"))
        stmt = stmt.order_by(PoloModel.nome)
        modelos, total = paginar(self.db, stmt, pagina, tamanho_pagina)
        return [_to_entity(m) for m in modelos], total

    def buscar_por_id(self, polo_id: UUID) -> Polo | None:
        m = self.db.get(PoloModel, polo_id)
        return _to_entity(m) if m else None

    def buscar_por_codigo(self, codigo: str) -> Polo | None:
        m = self.db.scalar(select(PoloModel).where(PoloModel.codigo == codigo))
        return _to_entity(m) if m else None

    def criar(self, polo: Polo) -> Polo:
        m = PoloModel(
            nome=polo.nome, codigo=polo.codigo, endereco=polo.endereco,
            horario_funcionamento=polo.horario_funcionamento, status=polo.status,
            gestor_responsavel_id=polo.gestor_responsavel_id,
            representante_legal_nome=polo.representante_legal_nome,
            representante_legal_cpf=polo.representante_legal_cpf,
            representante_legal_rg=polo.representante_legal_rg,
            responsavel_nome=polo.responsavel_nome, responsavel_email=polo.responsavel_email,
            responsavel_telefone=polo.responsavel_telefone,
            latitude=polo.latitude, longitude=polo.longitude,
        )
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

    def remover(self, polo_id: UUID) -> None:
        m = self.db.get(PoloModel, polo_id)
        if m:
            self.db.delete(m)
            self.db.commit()

    def limpar_gestor_responsavel(self, usuario_id: UUID) -> None:
        """Desvincula `usuario_id` de qualquer polo que o tenha como
        gestor_responsavel_id — chamado antes de excluir um Gestor de Polo
        de verdade, pra não esbarrar na constraint de chave estrangeira."""
        self.db.execute(
            update(PoloModel)
            .where(PoloModel.gestor_responsavel_id == usuario_id)
            .values(gestor_responsavel_id=None)
        )
        self.db.commit()
