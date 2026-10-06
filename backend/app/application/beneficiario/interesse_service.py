"""
Modalidades de INTERESSE do beneficiário — usadas enquanto o polo ainda não
tem turma formada naquela modalidade. Diferente da matrícula (vínculo com
uma turma concreta), o interesse é só a intenção; ao criar a turma, os
interessados podem ser matriculados de uma vez (ver TurmaService.criar).
"""
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.shared.exceptions import RecursoNaoEncontrado
from app.infrastructure.repositories.beneficiario_interesse_repository import BeneficiarioInteresseRepository
from app.infrastructure.repositories.beneficiario_repository import BeneficiarioRepository
from app.infrastructure.repositories.modalidade_repository import ModalidadeRepository


class BeneficiarioInteresseService:
    def __init__(self, db: Session):
        self.repo = BeneficiarioInteresseRepository(db)
        self.beneficiario_repo = BeneficiarioRepository(db)
        self.modalidade_repo = ModalidadeRepository(db)

    def listar(self, beneficiario_id: UUID) -> list[UUID]:
        return self.repo.listar_modalidades(beneficiario_id)

    def definir(self, beneficiario_id: UUID, modalidade_ids: list[UUID]) -> list[UUID]:
        """Substitui o conjunto inteiro de interesses do beneficiário."""
        self._validar(beneficiario_id, modalidade_ids)
        self.repo.substituir(beneficiario_id, modalidade_ids)
        return self.listar(beneficiario_id)

    def adicionar(self, beneficiario_id: UUID, modalidade_ids: list[UUID]) -> None:
        """Soma aos interesses já registrados (usado pela importação em massa)."""
        self._validar(beneficiario_id, modalidade_ids)
        self.repo.adicionar(beneficiario_id, modalidade_ids)

    def resumo_modalidades(self, beneficiario_ids: list[UUID]) -> dict[UUID, tuple[list[UUID], list[UUID]]]:
        return self.repo.resumo_modalidades(beneficiario_ids)

    def listar_interessados_sem_turma(self, polo_id: UUID, modalidade_id: UUID) -> list[UUID]:
        return self.repo.listar_interessados_sem_turma(polo_id, modalidade_id)

    def _validar(self, beneficiario_id: UUID, modalidade_ids: list[UUID]) -> None:
        if not self.beneficiario_repo.buscar_por_id(beneficiario_id):
            raise RecursoNaoEncontrado("Beneficiário não encontrado.")
        for modalidade_id in modalidade_ids:
            if not self.modalidade_repo.buscar_por_id(modalidade_id):
                raise RecursoNaoEncontrado("Modalidade não encontrada.")
