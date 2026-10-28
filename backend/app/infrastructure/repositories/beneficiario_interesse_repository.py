"""Repositório das modalidades de interesse do beneficiário (ainda sem matrícula)."""
from uuid import UUID

from sqlalchemy import delete, exists, select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import (
    BeneficiarioInteresseModel,
    BeneficiarioModel,
    MatriculaModel,
    TurmaModel,
)


class BeneficiarioInteresseRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_modalidades(self, beneficiario_id: UUID) -> list[UUID]:
        stmt = (
            select(BeneficiarioInteresseModel.modalidade_id)
            .where(BeneficiarioInteresseModel.beneficiario_id == beneficiario_id)
            .order_by(BeneficiarioInteresseModel.criado_em)
        )
        return list(self.db.scalars(stmt))

    def adicionar(self, beneficiario_id: UUID, modalidade_ids: list[UUID]) -> None:
        """Idempotente — modalidades já registradas são ignoradas."""
        existentes = set(self.listar_modalidades(beneficiario_id))
        for modalidade_id in dict.fromkeys(modalidade_ids):
            if modalidade_id not in existentes:
                self.db.add(BeneficiarioInteresseModel(beneficiario_id=beneficiario_id, modalidade_id=modalidade_id))
        self.db.commit()

    def substituir(self, beneficiario_id: UUID, modalidade_ids: list[UUID]) -> None:
        manter = set(modalidade_ids)
        self.db.execute(
            delete(BeneficiarioInteresseModel).where(
                BeneficiarioInteresseModel.beneficiario_id == beneficiario_id,
                BeneficiarioInteresseModel.modalidade_id.not_in(manter),
            )
        )
        self.adicionar(beneficiario_id, modalidade_ids)

    def trocar_modalidade(self, beneficiario_ids: list[UUID], antiga_id: UUID, nova_id: UUID) -> None:
        """Troca o interesse na modalidade `antiga_id` pelo interesse em
        `nova_id` — quem já tinha interesse na nova só perde o da antiga."""
        if not beneficiario_ids:
            return
        self.db.execute(
            delete(BeneficiarioInteresseModel).where(
                BeneficiarioInteresseModel.beneficiario_id.in_(beneficiario_ids),
                BeneficiarioInteresseModel.modalidade_id == antiga_id,
            )
        )
        for beneficiario_id in beneficiario_ids:
            self.adicionar(beneficiario_id, [nova_id])
        self.db.commit()

    def resumo_modalidades(self, beneficiario_ids: list[UUID]) -> dict[UUID, tuple[list[UUID], list[UUID]]]:
        """{beneficiario_id: (modalidades com matrícula ativa, modalidades de
        interesse ainda sem matrícula)} — duas consultas pro lote inteiro."""
        resumo: dict[UUID, tuple[list[UUID], list[UUID]]] = {b: ([], []) for b in beneficiario_ids}
        if not beneficiario_ids:
            return resumo
        matriculas = self.db.execute(
            select(MatriculaModel.beneficiario_id, TurmaModel.modalidade_id)
            .join(TurmaModel, TurmaModel.id == MatriculaModel.turma_id)
            .where(
                MatriculaModel.beneficiario_id.in_(beneficiario_ids),
                MatriculaModel.ativo.is_(True),
                TurmaModel.ativo.is_(True),
            )
            .distinct()
        )
        for beneficiario_id, modalidade_id in matriculas:
            resumo[beneficiario_id][0].append(modalidade_id)
        interesses = self.db.execute(
            select(BeneficiarioInteresseModel.beneficiario_id, BeneficiarioInteresseModel.modalidade_id)
            .where(BeneficiarioInteresseModel.beneficiario_id.in_(beneficiario_ids))
            .order_by(BeneficiarioInteresseModel.criado_em)
        )
        for beneficiario_id, modalidade_id in interesses:
            matriculado, interesse = resumo[beneficiario_id]
            if modalidade_id not in matriculado:
                interesse.append(modalidade_id)
        return resumo

    def listar_interessados_sem_turma(self, polo_id: UUID, modalidade_id: UUID) -> list[UUID]:
        """Beneficiários ativos do polo com interesse na modalidade e que ainda
        não têm matrícula ativa em nenhuma turma ativa dela — por ordem de
        registro do interesse (quem demonstrou interesse antes vem primeiro)."""
        ja_matriculado = exists().where(
            MatriculaModel.beneficiario_id == BeneficiarioModel.id,
            MatriculaModel.ativo.is_(True),
            MatriculaModel.turma_id == TurmaModel.id,
            TurmaModel.ativo.is_(True),
            TurmaModel.modalidade_id == modalidade_id,
        )
        stmt = (
            select(BeneficiarioModel.id)
            .join(BeneficiarioInteresseModel, BeneficiarioInteresseModel.beneficiario_id == BeneficiarioModel.id)
            .where(
                BeneficiarioInteresseModel.modalidade_id == modalidade_id,
                BeneficiarioModel.polo_id == polo_id,
                BeneficiarioModel.ativo.is_(True),
                ~ja_matriculado,
            )
            .order_by(BeneficiarioInteresseModel.criado_em, BeneficiarioModel.nome_completo)
        )
        return list(self.db.scalars(stmt))
