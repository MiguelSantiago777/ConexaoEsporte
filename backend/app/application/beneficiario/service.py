"""
Use cases de BENEFICIÁRIO (nomenclatura oficial e obrigatória).
Aplica regras de negócio: documento único, responsável legal se menor,
e checagem de vaga na turma.
"""
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.beneficiario.entities import Beneficiario
from app.domain.shared.exceptions import RegraDeNegocioViolada
from app.infrastructure.repositories.beneficiario_repository import BeneficiarioRepository
from app.infrastructure.repositories.turma_repository import TurmaRepository


class BeneficiarioService:
    def __init__(self, db: Session):
        self.repo = BeneficiarioRepository(db)
        self.turma_repo = TurmaRepository(db)

    def listar(self, polo_id: UUID | None = None, turma_id: UUID | None = None) -> list[Beneficiario]:
        return self.repo.listar(polo_id=polo_id, turma_id=turma_id)

    def buscar(self, beneficiario_id: UUID) -> Beneficiario | None:
        return self.repo.buscar_por_id(beneficiario_id)

    def criar(
        self, nome_completo: str, data_nascimento: date, documento: str,
        responsavel_legal_nome: str | None, responsavel_legal_contato: str | None,
        contato: str | None, endereco: str | None, turma_id: UUID | None,
        observacoes_medicas: str | None,
    ) -> Beneficiario:
        if self.repo.buscar_por_documento(documento):
            raise RegraDeNegocioViolada("Já existe um beneficiário com este documento.")

        beneficiario = Beneficiario(
            id=None, nome_completo=nome_completo, data_nascimento=data_nascimento,
            documento=documento, responsavel_legal_nome=responsavel_legal_nome,
            responsavel_legal_contato=responsavel_legal_contato, contato=contato,
            endereco=endereco, turma_id=turma_id, observacoes_medicas=observacoes_medicas,
        )
        beneficiario.validar_responsavel_legal_se_menor()

        if turma_id:
            self._validar_vaga(turma_id)

        return self.repo.criar(beneficiario)

    def atualizar(self, beneficiario_id: UUID, **campos) -> Beneficiario | None:
        novo_turma_id = campos.get("turma_id")
        if novo_turma_id:
            self._validar_vaga(novo_turma_id)
        return self.repo.atualizar(beneficiario_id, **campos)

    def _validar_vaga(self, turma_id: UUID) -> None:
        turma = self.turma_repo.buscar_por_id(turma_id)
        if not turma:
            raise RegraDeNegocioViolada("Turma informada não existe.")
        ocupadas = self.turma_repo.contar_beneficiarios_ativos(turma_id)
        if not turma.tem_vaga_disponivel(ocupadas):
            raise RegraDeNegocioViolada("Turma sem vagas disponíveis.")
