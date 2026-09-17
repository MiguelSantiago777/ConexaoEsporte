"""Repositório de Lançamentos Financeiros do Termo de Fomento (compõe o
resumo financeiro do Portal Transparência)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.lancamento_financeiro.entities import LancamentoFinanceiro
from app.infrastructure.database.models import LancamentoFinanceiroModel


def _to_entity(m: LancamentoFinanceiroModel) -> LancamentoFinanceiro:
    return LancamentoFinanceiro(
        id=m.id, categoria=m.categoria, tipo=m.tipo, valor=float(m.valor),
        data_lancamento=m.data_lancamento, descricao=m.descricao, polo_id=m.polo_id,
        criado_por_id=m.criado_por_id, criado_em=m.criado_em,
    )


class LancamentoFinanceiroRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, polo_id: UUID | None = None) -> list[LancamentoFinanceiro]:
        stmt = select(LancamentoFinanceiroModel).order_by(LancamentoFinanceiroModel.data_lancamento.desc())
        if polo_id:
            stmt = stmt.where(LancamentoFinanceiroModel.polo_id == polo_id)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def buscar_por_id(self, lancamento_id: UUID) -> LancamentoFinanceiro | None:
        m = self.db.get(LancamentoFinanceiroModel, lancamento_id)
        return _to_entity(m) if m else None

    def criar(self, lancamento: LancamentoFinanceiro) -> LancamentoFinanceiro:
        m = LancamentoFinanceiroModel(
            polo_id=lancamento.polo_id, categoria=lancamento.categoria, tipo=lancamento.tipo,
            valor=lancamento.valor, data_lancamento=lancamento.data_lancamento,
            descricao=lancamento.descricao, criado_por_id=lancamento.criado_por_id,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def remover(self, lancamento_id: UUID) -> None:
        m = self.db.get(LancamentoFinanceiroModel, lancamento_id)
        if m:
            self.db.delete(m)
            self.db.commit()
