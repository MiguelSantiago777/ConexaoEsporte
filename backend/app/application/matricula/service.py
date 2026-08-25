"""
Use cases de Matrícula: vincula um BENEFICIÁRIO a uma TURMA (relação N:N —
o mesmo beneficiário pode ter várias matrículas ativas ao mesmo tempo, em
turmas/modalidades diferentes).
"""
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.matricula.entities import Matricula
from app.domain.shared.exceptions import RecursoJaExiste, RecursoNaoEncontrado, RegraDeNegocioViolada
from app.infrastructure.repositories.beneficiario_repository import BeneficiarioRepository
from app.infrastructure.repositories.matricula_repository import MatriculaRepository
from app.infrastructure.repositories.turma_repository import TurmaRepository


class MatriculaService:
    def __init__(self, db: Session):
        self.repo = MatriculaRepository(db)
        self.beneficiario_repo = BeneficiarioRepository(db)
        self.turma_repo = TurmaRepository(db)

    def listar_por_beneficiario(self, beneficiario_id: UUID) -> list[Matricula]:
        return self.repo.listar_por_beneficiario(beneficiario_id)

    def matricular(self, beneficiario_id: UUID, turma_id: UUID) -> Matricula:
        beneficiario = self.beneficiario_repo.buscar_por_id(beneficiario_id)
        if not beneficiario:
            raise RecursoNaoEncontrado("Beneficiário não encontrado.")

        turma = self.turma_repo.buscar_por_id(turma_id)
        if not turma:
            raise RecursoNaoEncontrado("Turma não encontrada.")

        if beneficiario.polo_id and turma.polo_id != beneficiario.polo_id:
            raise RegraDeNegocioViolada("A turma deve pertencer ao mesmo polo do beneficiário.")

        existente = self.repo.buscar_por_beneficiario_e_turma(beneficiario_id, turma_id)
        if existente:
            if existente.ativo:
                raise RecursoJaExiste("Beneficiário já está matriculado nessa turma.")
            # Matrícula encerrada antes — reativa em vez de duplicar a linha.
            reativada = self.repo.atualizar(existente.id, ativo=True)
            assert reativada is not None
            return reativada

        ocupadas = self.turma_repo.contar_beneficiarios_ativos(turma_id)
        if not turma.tem_vaga_disponivel(ocupadas):
            raise RegraDeNegocioViolada("Turma sem vagas disponíveis.")

        matricula = Matricula(id=None, beneficiario_id=beneficiario_id, turma_id=turma_id, ativo=True)
        return self.repo.criar(matricula)

    def desmatricular(self, beneficiario_id: UUID, matricula_id: UUID) -> Matricula:
        matricula = self.repo.buscar_por_id(matricula_id)
        if not matricula or matricula.beneficiario_id != beneficiario_id:
            raise RecursoNaoEncontrado("Matrícula não encontrada.")
        atualizada = self.repo.atualizar(matricula_id, ativo=False)
        assert atualizada is not None
        return atualizada
