"""Importação em massa de TURMAS a partir de planilha (.xlsx). Reaproveita
`TurmaService.validar`/`criar` — inclusive a checagem de que o professor
vinculado é de fato PROFESSOR do mesmo polo."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.importacao.campos import hora, numero_inteiro, resolver_por_nome, texto, texto_obrigatorio
from app.application.importacao.executor import executar_importacao
from app.application.importacao.planilha import ColunaModelo, gerar_modelo
from app.application.importacao.resultado import ResultadoImportacao
from app.application.turma.service import TurmaService
from app.domain.shared.exceptions import RegraDeNegocioViolada
from app.infrastructure.repositories.modalidade_repository import ModalidadeRepository
from app.infrastructure.repositories.polo_repository import PoloRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.interfaces.api.v1.schemas.turma_schemas import DIAS_VALIDOS

COL_POLO = "Polo*"
COL_MODALIDADE = "Modalidade*"
COL_PROFESSOR = "E-mail do professor"
COL_INICIO = "Horário de início (HH:MM)*"
COL_FIM = "Horário de fim (HH:MM)*"
COL_DIAS = "Dias da semana*"
COL_VAGAS = "Limite de vagas*"
COL_COORDENADOR = "Coordenador"
COL_MONITOR = "Monitor"
COL_PERIODICIDADE = "Periodicidade"

_DIAS_EXEMPLO = "SEG,QUA,SEX"
_DIAS_AJUDA = f"Separados por vírgula, usando: {', '.join(sorted(DIAS_VALIDOS))}."


def _colunas(incluir_polo: bool) -> list[ColunaModelo]:
    colunas = []
    if incluir_polo:
        colunas.append(ColunaModelo(COL_POLO, True, "Polo Zona Norte", "Nome exato de um polo já cadastrado."))
    colunas += [
        ColunaModelo(COL_MODALIDADE, True, "Judô", "Nome exato de uma modalidade já cadastrada."),
        ColunaModelo(COL_PROFESSOR, False, "professor@email.com", "E-mail de um usuário já cadastrado com perfil PROFESSOR, no mesmo polo da turma."),
        ColunaModelo(COL_INICIO, True, "08:00"),
        ColunaModelo(COL_FIM, True, "09:30"),
        ColunaModelo(COL_DIAS, True, _DIAS_EXEMPLO, _DIAS_AJUDA),
        ColunaModelo(COL_VAGAS, True, "20"),
        ColunaModelo(COL_COORDENADOR, False, ""),
        ColunaModelo(COL_MONITOR, False, ""),
        ColunaModelo(COL_PERIODICIDADE, False, "Semanal"),
    ]
    return colunas


def _parse_dias(valor: str | None) -> list[str]:
    if not valor or not valor.strip():
        raise RegraDeNegocioViolada(f'Coluna "{COL_DIAS}" é obrigatória.')
    dias = [d.strip().upper() for d in valor.split(",") if d.strip()]
    invalidos = set(dias) - DIAS_VALIDOS
    if invalidos:
        raise RegraDeNegocioViolada(f'Coluna "{COL_DIAS}": dias inválidos {sorted(invalidos)}. Use: {sorted(DIAS_VALIDOS)}.')
    return dias


class TurmaImportacaoService:
    def __init__(self, db: Session):
        self.db = db
        self.service = TurmaService(db)
        self.polo_repo = PoloRepository(db)
        self.modalidade_repo = ModalidadeRepository(db)
        self.usuario_repo = UsuarioRepository(db)

    def gerar_modelo(self, polo_fixo_id: UUID | None):
        return gerar_modelo("Modelo de Importação — Turmas", _colunas(incluir_polo=polo_fixo_id is None))

    def importar(self, linhas: list[dict], confirmar: bool, polo_fixo_id: UUID | None) -> ResultadoImportacao:
        opcoes_polo = [(p.id, p.nome) for p in self.polo_repo.listar()] if polo_fixo_id is None else []
        opcoes_modalidade = [(m.id, m.nome) for m in self.modalidade_repo.listar()]

        def resolver_professor(email: str | None) -> UUID | None:
            if not email or not email.strip():
                return None
            professor = self.usuario_repo.buscar_por_email(email.strip())
            if not professor:
                raise RegraDeNegocioViolada(f'Coluna "{COL_PROFESSOR}": "{email}" não encontrado entre os usuários cadastrados.')
            return professor.id

        def processar(linha: dict) -> str:
            polo_id = polo_fixo_id or resolver_por_nome(COL_POLO, texto(linha, COL_POLO), opcoes_polo)
            modalidade_nome = texto_obrigatorio(linha, COL_MODALIDADE)
            modalidade_id = resolver_por_nome(COL_MODALIDADE, modalidade_nome, opcoes_modalidade)
            dados = dict(
                polo_id=polo_id,
                modalidade_id=modalidade_id,
                professor_id=resolver_professor(texto(linha, COL_PROFESSOR)),
                horario_inicio=hora(linha, COL_INICIO),
                horario_fim=hora(linha, COL_FIM),
                dias_semana=_parse_dias(texto(linha, COL_DIAS)),
                limite_vagas=numero_inteiro(linha, COL_VAGAS),
                coordenador_nome=texto(linha, COL_COORDENADOR),
                monitor_nome=texto(linha, COL_MONITOR),
                periodicidade=texto(linha, COL_PERIODICIDADE),
            )
            if confirmar:
                self.service.criar(**dados)
            else:
                self.service.validar(**dados)
            return f"{modalidade_nome} — {dados['horario_inicio']}-{dados['horario_fim']}"

        return executar_importacao(self.db, linhas, processar, confirmar)
