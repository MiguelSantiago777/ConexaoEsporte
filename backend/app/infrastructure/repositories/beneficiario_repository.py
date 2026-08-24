"""Repositório de BENEFICIÁRIO (nomenclatura oficial e obrigatória)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.beneficiario.entities import Beneficiario
from app.infrastructure.database.models import BeneficiarioModel, TurmaModel


def _to_entity(m: BeneficiarioModel) -> Beneficiario:
    return Beneficiario(
        id=m.id, nome_completo=m.nome_completo, data_nascimento=m.data_nascimento,
        documento=m.documento, responsavel_legal_nome=m.responsavel_legal_nome,
        responsavel_legal_contato=m.responsavel_legal_contato, contato=m.contato,
        endereco=m.endereco, turma_id=m.turma_id, observacoes_medicas=m.observacoes_medicas,
        ativo=m.ativo,
    )


class BeneficiarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, polo_id: UUID | None = None, turma_id: UUID | None = None) -> list[Beneficiario]:
        stmt = select(BeneficiarioModel)
        if turma_id:
            stmt = stmt.where(BeneficiarioModel.turma_id == turma_id)
        if polo_id:
            stmt = stmt.join(TurmaModel, TurmaModel.id == BeneficiarioModel.turma_id).where(
                TurmaModel.polo_id == polo_id
            )
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def buscar_por_id(self, beneficiario_id: UUID) -> Beneficiario | None:
        m = self.db.get(BeneficiarioModel, beneficiario_id)
        return _to_entity(m) if m else None

    def buscar_por_documento(self, documento: str) -> Beneficiario | None:
        m = self.db.scalar(select(BeneficiarioModel).where(BeneficiarioModel.documento == documento))
        return _to_entity(m) if m else None

    def criar(self, beneficiario: Beneficiario) -> Beneficiario:
        m = BeneficiarioModel(
            nome_completo=beneficiario.nome_completo, data_nascimento=beneficiario.data_nascimento,
            documento=beneficiario.documento, responsavel_legal_nome=beneficiario.responsavel_legal_nome,
            responsavel_legal_contato=beneficiario.responsavel_legal_contato, contato=beneficiario.contato,
            endereco=beneficiario.endereco, turma_id=beneficiario.turma_id,
            observacoes_medicas=beneficiario.observacoes_medicas, ativo=beneficiario.ativo,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def atualizar(self, beneficiario_id: UUID, **campos) -> Beneficiario | None:
        m = self.db.get(BeneficiarioModel, beneficiario_id)
        if not m:
            return None
        for k, v in campos.items():
            if v is not None:
                setattr(m, k, v)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)
