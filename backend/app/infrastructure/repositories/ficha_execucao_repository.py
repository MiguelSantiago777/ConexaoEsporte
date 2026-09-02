"""Repositório de Ficha de Execução."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.ficha_execucao.entities import FichaExecucao
from app.infrastructure.database.models import FichaExecucaoModel
from app.infrastructure.repositories.paginacao import paginar


def _to_entity(m: FichaExecucaoModel) -> FichaExecucao:
    return FichaExecucao(
        id=m.id, polo_id=m.polo_id, periodo_referencia=m.periodo_referencia, data_documento=m.data_documento,
        valor_recebido_periodo=m.valor_recebido_periodo, valor_recebido_extenso=m.valor_recebido_extenso,
        data_recebimento=m.data_recebimento, ajuste_status=m.ajuste_status,
        ajuste_justificativa=m.ajuste_justificativa, metas=m.metas or [],
        atividades_comparativo=m.atividades_comparativo or [], checklist_documentos=m.checklist_documentos or [],
        periodo_inscricao_inicio=m.periodo_inscricao_inicio, periodo_inscricao_fim=m.periodo_inscricao_fim,
        inscricao_todos_nucleos=m.inscricao_todos_nucleos, qtd_inscritos=m.qtd_inscritos,
        observacoes_inscricao=m.observacoes_inscricao,
        quantitativo_beneficiados=m.quantitativo_beneficiados, modalidades=m.modalidades,
        periodo_funcionamento=m.periodo_funcionamento, descricao_atividades=m.descricao_atividades,
        dificuldades=m.dificuldades,
        impactos_sociais=m.impactos_sociais, consideracoes_finais=m.consideracoes_finais,
        criado_por_id=m.criado_por_id, criado_em=m.criado_em,
    )


class FichaExecucaoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, polo_id: UUID | None = None) -> list[FichaExecucao]:
        stmt = select(FichaExecucaoModel).order_by(FichaExecucaoModel.criado_em.desc())
        if polo_id:
            stmt = stmt.where(FichaExecucaoModel.polo_id == polo_id)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def listar_pagina(
        self, pagina: int, tamanho_pagina: int, polo_id: UUID | None = None,
    ) -> tuple[list[FichaExecucao], int]:
        stmt = select(FichaExecucaoModel).order_by(FichaExecucaoModel.criado_em.desc())
        if polo_id:
            stmt = stmt.where(FichaExecucaoModel.polo_id == polo_id)
        modelos, total = paginar(self.db, stmt, pagina, tamanho_pagina)
        return [_to_entity(m) for m in modelos], total

    def buscar_por_id(self, ficha_id: UUID) -> FichaExecucao | None:
        m = self.db.get(FichaExecucaoModel, ficha_id)
        return _to_entity(m) if m else None

    def criar(self, ficha: FichaExecucao) -> FichaExecucao:
        m = FichaExecucaoModel(
            polo_id=ficha.polo_id,
            periodo_referencia=ficha.periodo_referencia, data_documento=ficha.data_documento,
            valor_recebido_periodo=ficha.valor_recebido_periodo, valor_recebido_extenso=ficha.valor_recebido_extenso,
            data_recebimento=ficha.data_recebimento, ajuste_status=ficha.ajuste_status,
            ajuste_justificativa=ficha.ajuste_justificativa, metas=ficha.metas,
            atividades_comparativo=ficha.atividades_comparativo, checklist_documentos=ficha.checklist_documentos,
            periodo_inscricao_inicio=ficha.periodo_inscricao_inicio, periodo_inscricao_fim=ficha.periodo_inscricao_fim,
            inscricao_todos_nucleos=ficha.inscricao_todos_nucleos, qtd_inscritos=ficha.qtd_inscritos,
            observacoes_inscricao=ficha.observacoes_inscricao,
            quantitativo_beneficiados=ficha.quantitativo_beneficiados, modalidades=ficha.modalidades,
            periodo_funcionamento=ficha.periodo_funcionamento, descricao_atividades=ficha.descricao_atividades,
            dificuldades=ficha.dificuldades,
            impactos_sociais=ficha.impactos_sociais, consideracoes_finais=ficha.consideracoes_finais,
            criado_por_id=ficha.criado_por_id,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def atualizar(self, ficha_id: UUID, **campos) -> FichaExecucao | None:
        m = self.db.get(FichaExecucaoModel, ficha_id)
        if not m:
            return None
        for k, v in campos.items():
            setattr(m, k, v)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)
