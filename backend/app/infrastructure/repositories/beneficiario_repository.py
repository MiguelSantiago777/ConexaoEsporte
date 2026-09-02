"""Repositório de BENEFICIÁRIO (nomenclatura oficial e obrigatória)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.beneficiario.entities import Beneficiario
from app.infrastructure.database.models import BeneficiarioModel, MatriculaModel
from app.infrastructure.repositories.paginacao import paginar


def _to_entity(m: BeneficiarioModel) -> Beneficiario:
    return Beneficiario(
        id=m.id, nome_completo=m.nome_completo, data_nascimento=m.data_nascimento,
        documento=m.documento, polo_id=m.polo_id, responsavel_legal_nome=m.responsavel_legal_nome,
        responsavel_legal_data_nascimento=m.responsavel_legal_data_nascimento,
        responsavel_legal_tipo_relacao=m.responsavel_legal_tipo_relacao,
        responsavel_legal_telefone_1=m.responsavel_legal_telefone_1,
        responsavel_legal_telefone_2=m.responsavel_legal_telefone_2,
        responsavel_legal_email=m.responsavel_legal_email,
        responsavel_legal_rede_social=m.responsavel_legal_rede_social,
        endereco=m.endereco, autoriza_whatsapp=m.autoriza_whatsapp,
        observacoes_medicas=m.observacoes_medicas, ativo=m.ativo,
    )


class BeneficiarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, polo_id: UUID | None = None, turma_id: UUID | None = None) -> list[Beneficiario]:
        stmt = select(BeneficiarioModel)
        if turma_id:
            stmt = stmt.join(MatriculaModel, MatriculaModel.beneficiario_id == BeneficiarioModel.id).where(
                MatriculaModel.turma_id == turma_id, MatriculaModel.ativo.is_(True)
            )
        if polo_id:
            stmt = stmt.where(BeneficiarioModel.polo_id == polo_id)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def listar_pagina(
        self, pagina: int, tamanho_pagina: int, polo_id: UUID | None = None,
        nome: str | None = None, apenas_ativos: bool = True,
    ) -> tuple[list[Beneficiario], int]:
        stmt = select(BeneficiarioModel)
        if apenas_ativos:
            stmt = stmt.where(BeneficiarioModel.ativo.is_(True))
        if polo_id:
            stmt = stmt.where(BeneficiarioModel.polo_id == polo_id)
        if nome:
            stmt = stmt.where(BeneficiarioModel.nome_completo.ilike(f"%{nome}%"))
        stmt = stmt.order_by(BeneficiarioModel.nome_completo)
        modelos, total = paginar(self.db, stmt, pagina, tamanho_pagina)
        return [_to_entity(m) for m in modelos], total

    def buscar_por_id(self, beneficiario_id: UUID) -> Beneficiario | None:
        m = self.db.get(BeneficiarioModel, beneficiario_id)
        return _to_entity(m) if m else None

    def buscar_por_documento(self, documento: str) -> Beneficiario | None:
        m = self.db.scalar(select(BeneficiarioModel).where(BeneficiarioModel.documento == documento))
        return _to_entity(m) if m else None

    def criar(self, beneficiario: Beneficiario) -> Beneficiario:
        m = BeneficiarioModel(
            nome_completo=beneficiario.nome_completo, data_nascimento=beneficiario.data_nascimento,
            documento=beneficiario.documento, polo_id=beneficiario.polo_id,
            responsavel_legal_nome=beneficiario.responsavel_legal_nome,
            responsavel_legal_data_nascimento=beneficiario.responsavel_legal_data_nascimento,
            responsavel_legal_tipo_relacao=beneficiario.responsavel_legal_tipo_relacao,
            responsavel_legal_telefone_1=beneficiario.responsavel_legal_telefone_1,
            responsavel_legal_telefone_2=beneficiario.responsavel_legal_telefone_2,
            responsavel_legal_email=beneficiario.responsavel_legal_email,
            responsavel_legal_rede_social=beneficiario.responsavel_legal_rede_social,
            endereco=beneficiario.endereco, autoriza_whatsapp=beneficiario.autoriza_whatsapp,
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
