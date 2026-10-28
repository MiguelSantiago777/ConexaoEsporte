"""Use cases de Turma."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.beneficiario.interesse_service import BeneficiarioInteresseService
from app.application.matricula.service import MatriculaService
from app.domain.enums import PerfilUsuario
from app.domain.shared.exceptions import RecursoNaoEncontrado, RegraDeNegocioViolada
from app.domain.turma.entities import Turma
from app.infrastructure.repositories.beneficiario_interesse_repository import BeneficiarioInteresseRepository
from app.infrastructure.repositories.inscricao_lista_espera_repository import InscricaoListaEsperaRepository
from app.infrastructure.repositories.matricula_repository import MatriculaRepository
from app.infrastructure.repositories.modalidade_repository import ModalidadeRepository
from app.infrastructure.repositories.turma_repository import TurmaRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository


class TurmaService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TurmaRepository(db)
        self.usuario_repo = UsuarioRepository(db)

    def listar(self, polo_id: UUID | None = None, professor_id: UUID | None = None) -> list[dict]:
        turmas = self.repo.listar(polo_id=polo_id, professor_id=professor_id)
        return [self._com_vagas(t) for t in turmas]

    def listar_pagina(
        self, pagina: int, tamanho_pagina: int, polo_id: UUID | None = None, professor_id: UUID | None = None,
    ) -> tuple[list[dict], int]:
        turmas, total = self.repo.listar_pagina(
            pagina=pagina, tamanho_pagina=tamanho_pagina, polo_id=polo_id, professor_id=professor_id
        )
        return [self._com_vagas(t) for t in turmas], total

    def buscar(self, turma_id: UUID) -> dict | None:
        t = self.repo.buscar_por_id(turma_id)
        return self._com_vagas(t) if t else None

    def _validar_professor(self, professor_id: UUID | None, polo_id: UUID) -> None:
        """Impede vincular à turma um usuário que não seja PROFESSOR do mesmo polo —
        sem isso, um GESTOR_POLO poderia dar acesso de leitura da turma (via
        assert_acesso_a_turma) a um professor de outro polo, ou a um usuário qualquer."""
        if professor_id is None:
            return
        professor = self.usuario_repo.buscar_por_id(professor_id)
        if not professor or professor.perfil != PerfilUsuario.PROFESSOR:
            raise RegraDeNegocioViolada("professor_id deve ser um usuário cadastrado com perfil PROFESSOR.")
        if professor.polo_id != polo_id:
            raise RegraDeNegocioViolada("O professor vinculado deve pertencer ao mesmo polo da turma.")

    def validar(
        self, polo_id: UUID, modalidade_id: UUID, professor_id: UUID | None,
        horario_inicio: str, horario_fim: str, dias_semana: list[str], limite_vagas: int,
        coordenador_nome: str | None = None, monitor_nome: str | None = None, periodicidade: str | None = None,
    ) -> Turma:
        """Monta e valida a turma sem gravar — reaproveitado por `criar` e pela
        prévia de importação em massa (que precisa validar sem persistir)."""
        self._validar_professor(professor_id, polo_id)
        return Turma(
            id=None, polo_id=polo_id, modalidade_id=modalidade_id, professor_id=professor_id,
            horario_inicio=horario_inicio, horario_fim=horario_fim,
            dias_semana=dias_semana, limite_vagas=limite_vagas,
            coordenador_nome=coordenador_nome, monitor_nome=monitor_nome, periodicidade=periodicidade,
        )

    def criar(
        self, polo_id: UUID, modalidade_id: UUID, professor_id: UUID | None,
        horario_inicio: str, horario_fim: str, dias_semana: list[str], limite_vagas: int,
        coordenador_nome: str | None = None, monitor_nome: str | None = None, periodicidade: str | None = None,
        matricular_interessados: bool = False,
    ) -> dict:
        turma = self.validar(
            polo_id=polo_id, modalidade_id=modalidade_id, professor_id=professor_id,
            horario_inicio=horario_inicio, horario_fim=horario_fim,
            dias_semana=dias_semana, limite_vagas=limite_vagas,
            coordenador_nome=coordenador_nome, monitor_nome=monitor_nome, periodicidade=periodicidade,
        )
        criada = self.repo.criar(turma)
        if matricular_interessados:
            self._matricular_interessados(criada)
        return self._com_vagas(criada)

    def contar_interessados(self, polo_id: UUID, modalidade_id: UUID) -> int:
        return len(BeneficiarioInteresseService(self.db).listar_interessados_sem_turma(polo_id, modalidade_id))

    def _matricular_interessados(self, turma: Turma) -> None:
        """Preenche a turma recém-criada com os interessados do polo naquela
        modalidade, por ordem de registro do interesse, até o limite de vagas."""
        assert turma.id is not None
        interessados = BeneficiarioInteresseService(self.db).listar_interessados_sem_turma(
            turma.polo_id, turma.modalidade_id
        )
        matricula_service = MatriculaService(self.db)
        for beneficiario_id in interessados[: turma.limite_vagas]:
            matricula_service.matricular(beneficiario_id, turma.id)

    def atualizar(self, turma_id: UUID, **campos) -> dict | None:
        turma_atual = self.repo.buscar_por_id(turma_id)
        if not turma_atual:
            return None
        if campos.get("professor_id") is not None:
            self._validar_professor(campos["professor_id"], turma_atual.polo_id)
        nova_modalidade_id = campos.get("modalidade_id")
        if nova_modalidade_id is not None and not ModalidadeRepository(self.db).buscar_por_id(nova_modalidade_id):
            raise RecursoNaoEncontrado("Modalidade não encontrada.")
        t = self.repo.atualizar(turma_id, **campos)
        if t and nova_modalidade_id is not None and nova_modalidade_id != turma_atual.modalidade_id:
            self._migrar_modalidade(t, turma_atual.modalidade_id)
        return self._com_vagas(t) if t else None

    def _migrar_modalidade(self, turma: Turma, antiga_id: UUID) -> None:
        """Depois de trocar a modalidade da turma (ex.: "Futsal" → "Futebol de
        Campo"), leva junto o que ainda apontava pra modalidade antiga:
        - o interesse dos matriculados na turma, que senão apareceriam como
          "aguardando turma" da antiga;
        - se o polo ficou sem turma ativa da antiga, também o interesse dos
          demais beneficiários do polo e as inscrições pendentes da lista de
          espera — a antiga deixou de ser oferecida ali e elas ficariam sem
          turma pra serem aceitas."""
        assert turma.id is not None
        interesse_repo = BeneficiarioInteresseRepository(self.db)
        sem_turma_da_antiga = set(interesse_repo.listar_interessados_sem_turma(turma.polo_id, antiga_id))
        polo_ainda_oferece = any(t.modalidade_id == antiga_id for t in self.repo.listar(polo_id=turma.polo_id))
        if polo_ainda_oferece:
            matriculados = {
                b_id for b_id, _ in MatriculaRepository(self.db).listar_beneficiarios_ativos_por_turma(turma.id)
            }
            migrar = sem_turma_da_antiga & matriculados
        else:
            migrar = sem_turma_da_antiga
            InscricaoListaEsperaRepository(self.db).trocar_modalidade_pendentes(
                turma.polo_id, antiga_id, turma.modalidade_id
            )
        interesse_repo.trocar_modalidade(list(migrar), antiga_id, turma.modalidade_id)

    def _com_vagas(self, turma: Turma) -> dict:
        ocupadas = self.repo.contar_beneficiarios_ativos(turma.id) if turma.id else 0
        return {
            "id": turma.id, "polo_id": turma.polo_id, "modalidade_id": turma.modalidade_id,
            "professor_id": turma.professor_id, "horario_inicio": turma.horario_inicio,
            "horario_fim": turma.horario_fim, "dias_semana": turma.dias_semana,
            "limite_vagas": turma.limite_vagas, "vagas_ocupadas": ocupadas,
            "coordenador_nome": turma.coordenador_nome, "monitor_nome": turma.monitor_nome,
            "periodicidade": turma.periodicidade, "ativo": turma.ativo,
        }
