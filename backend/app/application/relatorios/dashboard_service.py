"""Orquestra a agregação de dados (frequência, beneficiários por modalidade,
ranking de turmas/polos) para os relatórios gerenciais com gráficos — do
Polo (MASTER/GESTOR_POLO) e Geral, entre todos os polos (somente MASTER).

Diferente de `relatorios/service.py` (que preenche os 6 documentos oficiais
em .xlsx/.docx), este serviço devolve dados agregados em JSON, consumidos
pelo frontend para desenhar os gráficos e permitir impressão pelo navegador.
"""
from collections import Counter, defaultdict
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.shared.exceptions import RecursoNaoEncontrado
from app.infrastructure.repositories.beneficiario_repository import BeneficiarioRepository
from app.infrastructure.repositories.chamada_evidencia_repository import ChamadaEvidenciaRepository
from app.infrastructure.repositories.frequencia_repository import FrequenciaRepository
from app.infrastructure.repositories.matricula_repository import MatriculaRepository
from app.infrastructure.repositories.modalidade_repository import ModalidadeRepository
from app.infrastructure.repositories.polo_repository import PoloRepository
from app.infrastructure.repositories.turma_repository import TurmaRepository
from app.interfaces.api.v1.schemas.dashboard_schemas import (
    KPIsGeral,
    KPIsPolo,
    RankingPolo,
    RelatorioGeralResponse,
    RelatorioPoloResponse,
    SeriePonto,
)


def _semana_label(dia: date) -> str:
    ano_iso, semana_iso, _ = dia.isocalendar()
    return f"{ano_iso}-S{semana_iso:02d}"


def _percentual(presentes: int, total: int) -> float:
    return round(100 * presentes / total, 1) if total else 0.0


class DashboardService:
    def __init__(self, db: Session):
        self.turma_repo = TurmaRepository(db)
        self.polo_repo = PoloRepository(db)
        self.modalidade_repo = ModalidadeRepository(db)
        self.matricula_repo = MatriculaRepository(db)
        self.frequencia_repo = FrequenciaRepository(db)
        self.beneficiario_repo = BeneficiarioRepository(db)
        self.evidencia_repo = ChamadaEvidenciaRepository(db)

    def relatorio_polo(self, polo_id: UUID, data_inicio: date, data_fim: date) -> RelatorioPoloResponse:
        polo = self.polo_repo.buscar_por_id(polo_id)
        if not polo:
            raise RecursoNaoEncontrado("Polo não encontrado.")

        turmas = self.turma_repo.listar(polo_id=polo_id)
        turma_ids = [t.id for t in turmas]
        modalidades = {m.id: m.nome for m in self.modalidade_repo.listar()}

        beneficiarios_ativos = [b for b in self.beneficiario_repo.listar(polo_id=polo_id) if b.ativo]

        contagem_modalidade: Counter = Counter()
        for b in beneficiarios_ativos:
            matriculas_ativas = [m for m in self.matricula_repo.listar_por_beneficiario(b.id) if m.ativo]
            nomes_modalidade = set()
            for m in matriculas_ativas:
                turma = next((t for t in turmas if t.id == m.turma_id), None)
                if turma:
                    nomes_modalidade.add(modalidades.get(turma.modalidade_id, "Outra"))
            for nome in nomes_modalidade:
                contagem_modalidade[nome] += 1

        registros = self.frequencia_repo.listar_por_turmas_e_periodo(turma_ids, data_inicio, data_fim)
        total = len(registros)
        presentes = sum(1 for r in registros if r.presente)
        aulas_registradas = len({(r.turma_id, r.data) for r in registros})

        por_semana: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for r in registros:
            chave = por_semana[_semana_label(r.data)]
            chave[1] += 1
            if r.presente:
                chave[0] += 1
        frequencia_por_semana = [
            SeriePonto(label=semana, valor=_percentual(v[0], v[1])) for semana, v in sorted(por_semana.items())
        ]

        por_turma: dict[UUID, list[int]] = defaultdict(lambda: [0, 0])
        for r in registros:
            chave = por_turma[r.turma_id]
            chave[1] += 1
            if r.presente:
                chave[0] += 1
        frequencia_por_turma = []
        for t in sorted(turmas, key=lambda t: t.horario_inicio):
            v = por_turma.get(t.id, [0, 0])
            frequencia_por_turma.append(
                SeriePonto(
                    label=f"{modalidades.get(t.modalidade_id, 'Turma')} {t.horario_inicio}",
                    valor=_percentual(v[0], v[1]),
                )
            )

        fotos_evidencia = self.evidencia_repo.contar_por_turmas_e_periodo(turma_ids, data_inicio, data_fim)

        return RelatorioPoloResponse(
            polo_id=polo.id, polo_nome=polo.nome, data_inicio=data_inicio, data_fim=data_fim,
            kpis=KPIsPolo(
                beneficiarios_ativos=len(beneficiarios_ativos),
                turmas_ativas=len(turmas),
                frequencia_media_pct=_percentual(presentes, total),
                aulas_registradas=aulas_registradas,
                fotos_evidencia=fotos_evidencia,
            ),
            beneficiarios_por_modalidade=[
                SeriePonto(label=nome, valor=qtd) for nome, qtd in contagem_modalidade.items()
            ],
            frequencia_por_semana=frequencia_por_semana,
            frequencia_por_turma=frequencia_por_turma,
        )

    def relatorio_geral(self, data_inicio: date, data_fim: date) -> RelatorioGeralResponse:
        polos = self.polo_repo.listar()
        todas_turmas = self.turma_repo.listar()
        turmas_por_polo: dict[UUID, list[UUID]] = defaultdict(list)
        for t in todas_turmas:
            turmas_por_polo[t.polo_id].append(t.id)

        registros_geral = self.frequencia_repo.listar_por_periodo(data_inicio, data_fim)
        total_geral = len(registros_geral)
        presentes_geral = sum(1 for r in registros_geral if r.presente)

        por_semana: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for r in registros_geral:
            chave = por_semana[_semana_label(r.data)]
            chave[1] += 1
            if r.presente:
                chave[0] += 1
        frequencia_por_semana = [
            SeriePonto(label=semana, valor=_percentual(v[0], v[1])) for semana, v in sorted(por_semana.items())
        ]

        registros_por_turma: dict[UUID, list[int]] = defaultdict(lambda: [0, 0])
        for r in registros_geral:
            chave = registros_por_turma[r.turma_id]
            chave[1] += 1
            if r.presente:
                chave[0] += 1

        beneficiarios_por_polo = []
        ranking_polos = []
        total_beneficiarios_ativos = 0
        total_turmas_ativas = len(todas_turmas)
        for polo in polos:
            beneficiarios_polo = [b for b in self.beneficiario_repo.listar(polo_id=polo.id) if b.ativo]
            total_beneficiarios_ativos += len(beneficiarios_polo)
            beneficiarios_por_polo.append(SeriePonto(label=polo.nome, valor=len(beneficiarios_polo)))

            presentes_polo = 0
            total_polo = 0
            for turma_id in turmas_por_polo.get(polo.id, []):
                v = registros_por_turma.get(turma_id, [0, 0])
                presentes_polo += v[0]
                total_polo += v[1]
            ranking_polos.append(
                RankingPolo(
                    polo_id=polo.id, polo_nome=polo.nome,
                    frequencia_media_pct=_percentual(presentes_polo, total_polo),
                    beneficiarios_ativos=len(beneficiarios_polo),
                )
            )

        ranking_polos.sort(key=lambda r: r.frequencia_media_pct, reverse=True)

        return RelatorioGeralResponse(
            data_inicio=data_inicio, data_fim=data_fim,
            kpis=KPIsGeral(
                total_polos=len(polos),
                total_beneficiarios_ativos=total_beneficiarios_ativos,
                total_turmas_ativas=total_turmas_ativas,
                frequencia_media_pct=_percentual(presentes_geral, total_geral),
            ),
            beneficiarios_por_polo=beneficiarios_por_polo,
            frequencia_por_semana=frequencia_por_semana,
            ranking_polos=ranking_polos,
        )
