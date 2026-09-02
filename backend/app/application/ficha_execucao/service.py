"""Use casos de Ficha de Execução (somente MASTER)."""
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.ficha_execucao.entities import (
    FichaExecucao,
    atividades_comparativo_em_branco,
    checklist_em_branco,
    metas_em_branco,
)
from app.domain.shared.exceptions import RecursoNaoEncontrado
from app.infrastructure.repositories.ficha_execucao_repository import FichaExecucaoRepository
from app.infrastructure.repositories.polo_repository import PoloRepository


class FichaExecucaoService:
    def __init__(self, db: Session):
        self.repo = FichaExecucaoRepository(db)
        self.polo_repo = PoloRepository(db)

    def listar(self, polo_id: UUID | None = None) -> list[FichaExecucao]:
        return self.repo.listar(polo_id=polo_id)

    def listar_pagina(self, pagina: int, tamanho_pagina: int, polo_id: UUID | None = None) -> tuple[list[FichaExecucao], int]:
        return self.repo.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, polo_id=polo_id)

    def buscar(self, ficha_id: UUID) -> FichaExecucao | None:
        return self.repo.buscar_por_id(ficha_id)

    def criar(self, polo_id: UUID, periodo_referencia: str, data_documento: date | None, criado_por_id: UUID | None) -> FichaExecucao:
        if not self.polo_repo.buscar_por_id(polo_id):
            raise RecursoNaoEncontrado("Polo não encontrado.")
        ficha = FichaExecucao(
            id=None, polo_id=polo_id, periodo_referencia=periodo_referencia, data_documento=data_documento,
            valor_recebido_periodo=None, valor_recebido_extenso=None, data_recebimento=None,
            ajuste_status="NAO_SOLICITADO", ajuste_justificativa=None,
            metas=metas_em_branco(), atividades_comparativo=atividades_comparativo_em_branco(),
            checklist_documentos=checklist_em_branco(),
            periodo_inscricao_inicio=None, periodo_inscricao_fim=None, inscricao_todos_nucleos=None,
            qtd_inscritos=None, observacoes_inscricao=None,
            quantitativo_beneficiados=None, modalidades=None, periodo_funcionamento=None,
            descricao_atividades=None, dificuldades=None,
            impactos_sociais=None, consideracoes_finais=None, criado_por_id=criado_por_id,
        )
        return self.repo.criar(ficha)

    def atualizar(self, ficha_id: UUID, **campos) -> FichaExecucao | None:
        return self.repo.atualizar(ficha_id, **campos)
