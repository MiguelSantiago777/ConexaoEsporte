"""Use casos de Frequência: lançamento de chamada diária, impeditivos de
aula e a Ficha de Chamada mensal agregada (presença/falta/falta
justificada/impeditivo/sem marcação por beneficiário e por data)."""
import calendar
from collections import Counter
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.frequencia.entities import ImpeditivoAula, RegistroFrequencia
from app.domain.shared.exceptions import RecursoJaExiste, RecursoNaoEncontrado, RegraDeNegocioViolada
from app.infrastructure.repositories.beneficiario_repository import BeneficiarioRepository
from app.infrastructure.repositories.frequencia_repository import FrequenciaRepository
from app.infrastructure.repositories.impeditivo_aula_repository import ImpeditivoAulaRepository
from app.infrastructure.repositories.modalidade_repository import ModalidadeRepository
from app.infrastructure.repositories.polo_repository import PoloRepository
from app.infrastructure.repositories.turma_repository import TurmaRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.interfaces.api.v1.schemas.frequencia_schemas import (
    FichaChamadaResponse,
    ImpeditivoAulaResponse,
    LinhaFichaChamada,
    ResumoFichaChamada,
)

DIA_PARA_WEEKDAY = {"SEG": 0, "TER": 1, "QUA": 2, "QUI": 3, "SEX": 4, "SAB": 5, "DOM": 6}


def _idade(data_nascimento: date, referencia: date) -> int:
    anos = referencia.year - data_nascimento.year
    if (referencia.month, referencia.day) < (data_nascimento.month, data_nascimento.day):
        anos -= 1
    return anos


def _datas_do_mes(dias_semana: list[str], mes: int, ano: int) -> list[date]:
    """Todas as datas do mês em que a turma tem aula, segundo os dias da semana cadastrados."""
    weekdays = {DIA_PARA_WEEKDAY[d] for d in dias_semana if d in DIA_PARA_WEEKDAY}
    _, dias_no_mes = calendar.monthrange(ano, mes)
    return [
        date(ano, mes, dia) for dia in range(1, dias_no_mes + 1) if date(ano, mes, dia).weekday() in weekdays
    ]


class FrequenciaService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FrequenciaRepository(db)
        self.impeditivo_repo = ImpeditivoAulaRepository(db)
        self.turma_repo = TurmaRepository(db)
        self.beneficiario_repo = BeneficiarioRepository(db)
        self.polo_repo = PoloRepository(db)
        self.modalidade_repo = ModalidadeRepository(db)
        self.usuario_repo = UsuarioRepository(db)

    def registrar_chamada(
        self, turma_id: UUID, data_ref: date,
        presencas: list[tuple[UUID, bool, bool, str | None]], registrado_por_id: UUID,
    ) -> list[RegistroFrequencia]:
        if self.impeditivo_repo.buscar_por_turma_e_data(turma_id, data_ref):
            raise RegraDeNegocioViolada(
                "Essa data tem um impeditivo de aula cadastrado — remova o impeditivo antes de lançar chamada."
            )
        registros = [
            RegistroFrequencia(
                id=None, turma_id=turma_id, beneficiario_id=benef_id, data=data_ref,
                presente=presente, registrado_por_id=registrado_por_id,
                falta_justificada=falta_justificada, justificativa=justificativa,
            )
            for benef_id, presente, falta_justificada, justificativa in presencas
        ]
        return self.repo.registrar_chamada(registros)

    def listar_chamada(self, turma_id: UUID, data_ref: date) -> list[RegistroFrequencia]:
        return self.repo.listar_por_turma_e_data(turma_id, data_ref)

    def criar_impeditivo(
        self, turma_id: UUID, data_ref: date, justificativa: str, criado_por_id: UUID,
    ) -> ImpeditivoAula:
        if self.impeditivo_repo.buscar_por_turma_e_data(turma_id, data_ref):
            raise RecursoJaExiste("Já existe um impeditivo de aula cadastrado para essa turma nessa data.")
        impeditivo = ImpeditivoAula(
            id=None, turma_id=turma_id, data=data_ref, justificativa=justificativa, criado_por_id=criado_por_id,
        )
        return self.impeditivo_repo.criar(impeditivo)

    def listar_impeditivos(self, turma_id: UUID, mes: int, ano: int) -> list[ImpeditivoAula]:
        _, dias_no_mes = calendar.monthrange(ano, mes)
        return self.impeditivo_repo.listar_por_turma_e_periodo(turma_id, date(ano, mes, 1), date(ano, mes, dias_no_mes))

    def remover_impeditivo(self, impeditivo_id: UUID) -> bool:
        return self.impeditivo_repo.remover(impeditivo_id)

    def montar_ficha_chamada(self, turma_id: UUID, mes: int, ano: int) -> FichaChamadaResponse:
        turma = self.turma_repo.buscar_por_id(turma_id)
        if not turma:
            raise RecursoNaoEncontrado("Turma não encontrada.")
        polo = self.polo_repo.buscar_por_id(turma.polo_id)
        modalidade = self.modalidade_repo.buscar_por_id(turma.modalidade_id)
        professor = self.usuario_repo.buscar_por_id(turma.professor_id) if turma.professor_id else None

        datas = _datas_do_mes(turma.dias_semana, mes, ano)
        hoje = date.today()

        beneficiarios = [b for b in self.beneficiario_repo.listar(turma_id=turma_id) if b.ativo]
        idades = [_idade(b.data_nascimento, hoje) for b in beneficiarios]

        _, dias_no_mes = calendar.monthrange(ano, mes)
        inicio_mes, fim_mes = date(ano, mes, 1), date(ano, mes, dias_no_mes)
        registros = self.repo.listar_por_turma_e_periodo(turma_id, inicio_mes, fim_mes)
        registros_por_chave = {(r.beneficiario_id, r.data): r for r in registros}

        impeditivos = self.impeditivo_repo.listar_por_turma_e_periodo(turma_id, inicio_mes, fim_mes)
        datas_impeditivo = {i.data for i in impeditivos}
        dias_letivos = len([d for d in datas if d not in datas_impeditivo])

        linhas: list[LinhaFichaChamada] = []
        contagem: Counter = Counter()
        for b, idade in zip(beneficiarios, idades):
            status_por_data: dict[str, str] = {}
            presentes = 0
            for d in datas:
                if d in datas_impeditivo:
                    status = "IMPEDITIVO"
                else:
                    registro = registros_por_chave.get((b.id, d))
                    if registro is None:
                        status = "SEM_MARCACAO"
                    elif registro.presente:
                        status = "PRESENTE"
                        presentes += 1
                    elif registro.falta_justificada:
                        status = "FALTA_JUSTIFICADA"
                    else:
                        status = "FALTA"
                status_por_data[d.isoformat()] = status
                contagem[status] += 1
            frequencia_pct = round(100 * presentes / dias_letivos, 2) if dias_letivos else 0.0
            linhas.append(
                LinhaFichaChamada(
                    beneficiario_id=b.id, nome=b.nome_completo, idade=idade,
                    status_por_data=status_por_data, frequencia_pct=frequencia_pct,
                )
            )

        resumo = ResumoFichaChamada(
            presenca=contagem["PRESENTE"], falta=contagem["FALTA"],
            falta_justificada=contagem["FALTA_JUSTIFICADA"], impeditivo=contagem["IMPEDITIVO"],
            sem_marcacao=contagem["SEM_MARCACAO"], total=len(beneficiarios) * len(datas),
        )

        return FichaChamadaResponse(
            turma_id=turma_id,
            polo_nome=polo.nome if polo else "—",
            modalidade_nome=modalidade.nome if modalidade else "—",
            professor_nome=professor.nome if professor else None,
            horario_inicio=turma.horario_inicio, horario_fim=turma.horario_fim,
            dias_semana=turma.dias_semana,
            faixa_etaria_min=min(idades) if idades else None,
            faixa_etaria_max=max(idades) if idades else None,
            mes=mes, ano=ano, datas=datas,
            linhas=linhas,
            impeditivos=[ImpeditivoAulaResponse.model_validate(i) for i in impeditivos],
            resumo=resumo,
        )
