"""Repositório de Produto (catálogo central de Estoque)."""
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.domain.produto.entities import Produto
from app.infrastructure.database.models import AlmoxarifadoModel, MovimentoEstoqueModel, ProdutoModel
from app.infrastructure.repositories.paginacao import paginar


def _to_entity(m: ProdutoModel) -> Produto:
    return Produto(id=m.id, nome=m.nome, unidade_medida=m.unidade_medida, descricao=m.descricao, ativo=m.ativo)


class ProdutoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, apenas_ativos: bool = False) -> list[Produto]:
        stmt = select(ProdutoModel).order_by(ProdutoModel.nome)
        if apenas_ativos:
            stmt = stmt.where(ProdutoModel.ativo.is_(True))
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def listar_pagina(self, pagina: int, tamanho_pagina: int, nome: str | None = None) -> tuple[list[Produto], int]:
        stmt = select(ProdutoModel)
        if nome:
            stmt = stmt.where(ProdutoModel.nome.ilike(f"%{nome}%"))
        stmt = stmt.order_by(ProdutoModel.nome)
        modelos, total = paginar(self.db, stmt, pagina, tamanho_pagina)
        return [_to_entity(m) for m in modelos], total

    def buscar_por_id(self, produto_id: UUID) -> Produto | None:
        m = self.db.get(ProdutoModel, produto_id)
        return _to_entity(m) if m else None

    def saldo_atual(self, produto_id: UUID, almoxarifado_id: UUID | None = None) -> int:
        """Soma de todas as ENTRADAs menos todas as SAÍDAs do produto — no
        total (todos os almoxarifados) quando `almoxarifado_id` não é
        informado, ou só naquele almoxarifado específico."""
        sinal = case((MovimentoEstoqueModel.tipo == "ENTRADA", MovimentoEstoqueModel.quantidade), else_=-MovimentoEstoqueModel.quantidade)
        stmt = select(func.coalesce(func.sum(sinal), 0)).where(MovimentoEstoqueModel.produto_id == produto_id)
        if almoxarifado_id:
            stmt = stmt.where(MovimentoEstoqueModel.almoxarifado_id == almoxarifado_id)
        return int(self.db.scalar(stmt) or 0)

    def saldo_por_almoxarifado(self, produto_id: UUID) -> list[dict]:
        """Saldo do produto em cada almoxarifado que já teve alguma
        movimentação dele — usado pra mostrar o detalhamento no catálogo e
        pra montar as opções de Saída na Entrega de Materiais."""
        sinal = case((MovimentoEstoqueModel.tipo == "ENTRADA", MovimentoEstoqueModel.quantidade), else_=-MovimentoEstoqueModel.quantidade)
        stmt = (
            select(AlmoxarifadoModel.id, AlmoxarifadoModel.nome, func.coalesce(func.sum(sinal), 0))
            .join(MovimentoEstoqueModel, MovimentoEstoqueModel.almoxarifado_id == AlmoxarifadoModel.id)
            .where(MovimentoEstoqueModel.produto_id == produto_id)
            .group_by(AlmoxarifadoModel.id, AlmoxarifadoModel.nome)
            .order_by(AlmoxarifadoModel.nome)
        )
        return [
            {"almoxarifado_id": almoxarifado_id, "almoxarifado_nome": nome, "saldo": int(saldo)}
            for almoxarifado_id, nome, saldo in self.db.execute(stmt)
        ]

    def saldos_por_produto_de(self, almoxarifado_id: UUID) -> list[dict]:
        """Inverso de `saldo_por_almoxarifado`: todos os produtos que já
        tiveram alguma movimentação NESTE almoxarifado, com o saldo de cada
        um — usado no dashboard do Coordenador de Almoxarifado."""
        sinal = case((MovimentoEstoqueModel.tipo == "ENTRADA", MovimentoEstoqueModel.quantidade), else_=-MovimentoEstoqueModel.quantidade)
        stmt = (
            select(ProdutoModel.id, ProdutoModel.nome, ProdutoModel.unidade_medida, func.coalesce(func.sum(sinal), 0))
            .join(MovimentoEstoqueModel, MovimentoEstoqueModel.produto_id == ProdutoModel.id)
            .where(MovimentoEstoqueModel.almoxarifado_id == almoxarifado_id)
            .group_by(ProdutoModel.id, ProdutoModel.nome, ProdutoModel.unidade_medida)
            .order_by(ProdutoModel.nome)
        )
        return [
            {"produto_id": produto_id, "produto_nome": nome, "unidade_medida": unidade, "saldo": int(saldo)}
            for produto_id, nome, unidade, saldo in self.db.execute(stmt)
        ]

    def saldos_em_lote(self, produto_ids: list[UUID]) -> dict[UUID, int]:
        """Mesmo cálculo de `saldo_atual`, mas pra vários produtos numa só
        consulta — usado ao listar o catálogo inteiro (evita N+1)."""
        if not produto_ids:
            return {}
        sinal = case((MovimentoEstoqueModel.tipo == "ENTRADA", MovimentoEstoqueModel.quantidade), else_=-MovimentoEstoqueModel.quantidade)
        stmt = (
            select(MovimentoEstoqueModel.produto_id, func.coalesce(func.sum(sinal), 0))
            .where(MovimentoEstoqueModel.produto_id.in_(produto_ids))
            .group_by(MovimentoEstoqueModel.produto_id)
        )
        saldos = {produto_id: int(total) for produto_id, total in self.db.execute(stmt)}
        return {pid: saldos.get(pid, 0) for pid in produto_ids}

    def criar(self, produto: Produto) -> Produto:
        m = ProdutoModel(
            nome=produto.nome, unidade_medida=produto.unidade_medida,
            descricao=produto.descricao, ativo=produto.ativo,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def atualizar(self, produto_id: UUID, **campos) -> Produto | None:
        m = self.db.get(ProdutoModel, produto_id)
        if not m:
            return None
        for k, v in campos.items():
            if v is not None:
                setattr(m, k, v)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def remover(self, produto_id: UUID) -> bool:
        m = self.db.get(ProdutoModel, produto_id)
        if not m:
            return False
        self.db.delete(m)
        self.db.commit()
        return True
