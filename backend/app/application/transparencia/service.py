"""Use cases do Portal Transparência: agrega execução física, resumo
financeiro (Lançamentos Financeiros do Termo de Fomento) e documentos
marcados como públicos pelo MASTER, para exibição sem autenticação ao
órgão fiscalizador e a qualquer visitante. Também expõe o CRUD de
Lançamentos Financeiros, exclusivo do MASTER."""
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.anexo_geral.entities import AnexoGeral
from app.domain.lancamento_financeiro.entities import LancamentoFinanceiro
from app.domain.shared.exceptions import RecursoNaoEncontrado
from app.infrastructure.repositories.anexo_geral_repository import AnexoGeralRepository
from app.infrastructure.repositories.beneficiario_repository import BeneficiarioRepository
from app.infrastructure.repositories.configuracao_geral_repository import ConfiguracaoGeralRepository
from app.infrastructure.repositories.frequencia_repository import FrequenciaRepository
from app.infrastructure.repositories.lancamento_financeiro_repository import LancamentoFinanceiroRepository
from app.infrastructure.repositories.modalidade_repository import ModalidadeRepository
from app.infrastructure.repositories.polo_repository import PoloRepository
from app.infrastructure.repositories.turma_repository import TurmaRepository
from app.interfaces.api.v1.schemas.transparencia_schemas import (
    DocumentoPublicoResponse,
    ExecucaoFisicaPublica,
    InstitucionalPublico,
    PortalTransparenciaResponse,
    ResumoFinanceiroCategoria,
    ResumoFinanceiroPublico,
)

# Janela usada pra "frequência média" do resumo público — a mesma métrica
# calculada pelos Relatórios Gerenciais, mas sem exigir que o visitante
# escolha um período (não há tela de filtro na página pública).
JANELA_FREQUENCIA_DIAS = 90


def _percentual(presentes: int, total: int) -> float:
    return round(100 * presentes / total, 1) if total else 0.0


class TransparenciaService:
    def __init__(self, db: Session):
        self.db = db
        self.lancamento_repo = LancamentoFinanceiroRepository(db)
        self.anexo_repo = AnexoGeralRepository(db)
        self.configuracao_repo = ConfiguracaoGeralRepository(db)
        self.polo_repo = PoloRepository(db)
        self.turma_repo = TurmaRepository(db)
        self.modalidade_repo = ModalidadeRepository(db)
        self.beneficiario_repo = BeneficiarioRepository(db)
        self.frequencia_repo = FrequenciaRepository(db)

    def resumo_publico(self) -> PortalTransparenciaResponse:
        configuracao = self.configuracao_repo.buscar()
        polos = self.polo_repo.listar()
        turmas_ativas = [t for t in self.turma_repo.listar() if t.ativo]
        beneficiarios_ativos = [
            b for polo in polos for b in self.beneficiario_repo.listar(polo_id=polo.id) if b.ativo
        ]

        hoje = date.today()
        registros = self.frequencia_repo.listar_por_periodo(hoje - timedelta(days=JANELA_FREQUENCIA_DIAS), hoje)
        presentes = sum(1 for r in registros if r.presente)

        execucao_fisica = ExecucaoFisicaPublica(
            total_polos=len(polos),
            total_modalidades=len(self.modalidade_repo.listar()),
            total_turmas_ativas=len(turmas_ativas),
            total_beneficiarios_ativos=len(beneficiarios_ativos),
            frequencia_media_pct=_percentual(presentes, len(registros)),
        )

        financeiro = self._resumo_financeiro()

        polos_por_id = {p.id: p.nome for p in polos}
        documentos = [
            DocumentoPublicoResponse(
                id=a.id, titulo=a.titulo, polo_nome=polos_por_id.get(a.polo_id, "—"),
                nome_arquivo=a.nome_arquivo, content_type=a.content_type, criado_em=a.criado_em,
            )
            for a in self.anexo_repo.listar()
            if a.publico
        ]
        documentos.sort(key=lambda d: d.criado_em or datetime.now(timezone.utc), reverse=True)

        return PortalTransparenciaResponse(
            institucional=InstitucionalPublico(
                nome_projeto=configuracao.nome_projeto if configuracao else None,
                numero_convenio=configuracao.numero_convenio if configuracao else None,
                data_inicio_projeto=configuracao.data_inicio_projeto if configuracao else None,
                data_fim_projeto=configuracao.data_fim_projeto if configuracao else None,
            ),
            execucao_fisica=execucao_fisica,
            financeiro=financeiro,
            documentos=documentos,
            atualizado_em=datetime.now(timezone.utc),
        )

    def _resumo_financeiro(self) -> ResumoFinanceiroPublico:
        lancamentos = self.lancamento_repo.listar()
        total_repassado = sum(l.valor for l in lancamentos if l.tipo == "REPASSE")
        total_executado = sum(l.valor for l in lancamentos if l.tipo == "EXECUCAO")

        por_categoria: dict[str, dict[str, float]] = defaultdict(lambda: {"repassado": 0.0, "executado": 0.0})
        for l in lancamentos:
            chave = "repassado" if l.tipo == "REPASSE" else "executado"
            por_categoria[l.categoria][chave] += l.valor

        return ResumoFinanceiroPublico(
            total_repassado=round(total_repassado, 2),
            total_executado=round(total_executado, 2),
            saldo=round(total_repassado - total_executado, 2),
            por_categoria=[
                ResumoFinanceiroCategoria(
                    categoria=categoria, repassado=round(valores["repassado"], 2),
                    executado=round(valores["executado"], 2),
                )
                for categoria, valores in sorted(por_categoria.items())
            ],
        )

    def buscar_documento_publico(self, anexo_id: UUID) -> AnexoGeral:
        anexo = self.anexo_repo.buscar_por_id(anexo_id)
        if not anexo or not anexo.publico:
            raise RecursoNaoEncontrado("Documento não encontrado.")
        return anexo

    def listar_lancamentos(self, polo_id: UUID | None = None) -> list[LancamentoFinanceiro]:
        return self.lancamento_repo.listar(polo_id=polo_id)

    def criar_lancamento(
        self, categoria: str, tipo: str, valor: float, data_lancamento: date,
        descricao: str | None, polo_id: UUID | None, criado_por_id: UUID,
    ) -> LancamentoFinanceiro:
        lancamento = LancamentoFinanceiro(
            id=None, categoria=categoria, tipo=tipo, valor=valor, data_lancamento=data_lancamento,
            descricao=descricao, polo_id=polo_id, criado_por_id=criado_por_id,
        )
        return self.lancamento_repo.criar(lancamento)

    def remover_lancamento(self, lancamento_id: UUID) -> None:
        if not self.lancamento_repo.buscar_por_id(lancamento_id):
            raise RecursoNaoEncontrado("Lançamento não encontrado.")
        self.lancamento_repo.remover(lancamento_id)
