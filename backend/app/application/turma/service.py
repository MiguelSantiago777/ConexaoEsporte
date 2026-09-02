"""Use cases de Turma."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.enums import PerfilUsuario
from app.domain.shared.exceptions import RegraDeNegocioViolada
from app.domain.turma.entities import Turma
from app.infrastructure.repositories.turma_repository import TurmaRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository


class TurmaService:
    def __init__(self, db: Session):
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

    def criar(
        self, polo_id: UUID, modalidade_id: UUID, professor_id: UUID | None,
        horario_inicio: str, horario_fim: str, dias_semana: list[str], limite_vagas: int,
        coordenador_nome: str | None = None, monitor_nome: str | None = None, periodicidade: str | None = None,
    ) -> dict:
        self._validar_professor(professor_id, polo_id)
        turma = Turma(
            id=None, polo_id=polo_id, modalidade_id=modalidade_id, professor_id=professor_id,
            horario_inicio=horario_inicio, horario_fim=horario_fim,
            dias_semana=dias_semana, limite_vagas=limite_vagas,
            coordenador_nome=coordenador_nome, monitor_nome=monitor_nome, periodicidade=periodicidade,
        )
        criada = self.repo.criar(turma)
        return self._com_vagas(criada)

    def atualizar(self, turma_id: UUID, **campos) -> dict | None:
        if campos.get("professor_id") is not None:
            turma_atual = self.repo.buscar_por_id(turma_id)
            if not turma_atual:
                return None
            self._validar_professor(campos["professor_id"], turma_atual.polo_id)
        t = self.repo.atualizar(turma_id, **campos)
        return self._com_vagas(t) if t else None

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
