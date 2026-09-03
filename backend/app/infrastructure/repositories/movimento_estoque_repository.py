"""Repositório de Movimento de Estoque (Entrada/Saída de um Produto, num almoxarifado)."""
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.estoque.entities import MovimentoEstoque
from app.infrastructure.database.models import MovimentoEstoqueModel
from app.infrastructure.repositories.paginacao import paginar


def _to_entity(m: MovimentoEstoqueModel) -> MovimentoEstoque:
    return MovimentoEstoque(
        id=m.id, produto_id=m.produto_id, almoxarifado_id=m.almoxarifado_id,
        tipo=m.tipo, quantidade=m.quantidade, data=m.data,
        observacao=m.observacao, entregue_por=m.entregue_por, recebido_por=m.recebido_por,
        nome_arquivo=m.nome_arquivo, caminho_arquivo=m.caminho_arquivo,
        content_type=m.content_type, tamanho_bytes=m.tamanho_bytes,
        entrega_material_id=m.entrega_material_id, criado_por_id=m.criado_por_id, criado_em=m.criado_em,
    )


class MovimentoEstoqueRepository:
    def __init__(self, db: Session):
        self.db = db

    def _stmt_filtrado(
        self, produto_id: UUID | None, tipo: str | None, data_inicio: date | None, data_fim: date | None,
        almoxarifado_id: UUID | None = None,
    ):
        stmt = select(MovimentoEstoqueModel).order_by(MovimentoEstoqueModel.criado_em.desc())
        if produto_id:
            stmt = stmt.where(MovimentoEstoqueModel.produto_id == produto_id)
        if almoxarifado_id:
            stmt = stmt.where(MovimentoEstoqueModel.almoxarifado_id == almoxarifado_id)
        if tipo:
            stmt = stmt.where(MovimentoEstoqueModel.tipo == tipo)
        if data_inicio:
            stmt = stmt.where(MovimentoEstoqueModel.data >= data_inicio)
        if data_fim:
            stmt = stmt.where(MovimentoEstoqueModel.data <= data_fim)
        return stmt

    def listar(
        self, produto_id: UUID | None = None, tipo: str | None = None,
        data_inicio: date | None = None, data_fim: date | None = None, almoxarifado_id: UUID | None = None,
    ) -> list[MovimentoEstoque]:
        stmt = self._stmt_filtrado(produto_id, tipo, data_inicio, data_fim, almoxarifado_id)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def listar_pagina(
        self, pagina: int, tamanho_pagina: int,
        produto_id: UUID | None = None, tipo: str | None = None,
        data_inicio: date | None = None, data_fim: date | None = None, almoxarifado_id: UUID | None = None,
    ) -> tuple[list[MovimentoEstoque], int]:
        stmt = self._stmt_filtrado(produto_id, tipo, data_inicio, data_fim, almoxarifado_id)
        modelos, total = paginar(self.db, stmt, pagina, tamanho_pagina)
        return [_to_entity(m) for m in modelos], total

    def listar_por_periodo(
        self, data_inicio: date, data_fim: date, almoxarifado_id: UUID | None = None
    ) -> list[MovimentoEstoque]:
        """Sem paginação — usado pelo Relatório de Estoque, que precisa do
        período inteiro pra agregar por produto (opcionalmente restrito a um
        único almoxarifado, pro Coordenador de Almoxarifado)."""
        stmt = (
            select(MovimentoEstoqueModel)
            .where(MovimentoEstoqueModel.data >= data_inicio, MovimentoEstoqueModel.data <= data_fim)
            .order_by(MovimentoEstoqueModel.data)
        )
        if almoxarifado_id:
            stmt = stmt.where(MovimentoEstoqueModel.almoxarifado_id == almoxarifado_id)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def buscar_por_id(self, movimento_id: UUID) -> MovimentoEstoque | None:
        m = self.db.get(MovimentoEstoqueModel, movimento_id)
        return _to_entity(m) if m else None

    def criar(self, movimento: MovimentoEstoque) -> MovimentoEstoque:
        m = MovimentoEstoqueModel(
            produto_id=movimento.produto_id, almoxarifado_id=movimento.almoxarifado_id,
            tipo=movimento.tipo, quantidade=movimento.quantidade,
            data=movimento.data, observacao=movimento.observacao,
            entregue_por=movimento.entregue_por, recebido_por=movimento.recebido_por,
            nome_arquivo=movimento.nome_arquivo, caminho_arquivo=movimento.caminho_arquivo,
            content_type=movimento.content_type, tamanho_bytes=movimento.tamanho_bytes,
            entrega_material_id=movimento.entrega_material_id, criado_por_id=movimento.criado_por_id,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)
