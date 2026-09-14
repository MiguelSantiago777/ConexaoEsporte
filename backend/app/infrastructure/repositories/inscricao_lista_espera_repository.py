"""Repositório de INSCRIÇÃO NA LISTA DE ESPERA (inscricoes_lista_espera)."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.lista_espera.entities import InscricaoListaEspera
from app.infrastructure.database.models import InscricaoListaEsperaModel


def _to_entity(m: InscricaoListaEsperaModel) -> InscricaoListaEspera:
    return InscricaoListaEspera(
        id=m.id, nome_completo=m.nome_completo, data_nascimento=m.data_nascimento,
        documento=m.documento, nome_responsavel=m.nome_responsavel,
        documento_responsavel=m.documento_responsavel,
        telefone_whatsapp=m.telefone_whatsapp, email=m.email, bairro=m.bairro, cidade=m.cidade,
        modalidade_id=m.modalidade_id, polo_id=m.polo_id, como_conheceu=m.como_conheceu,
        beneficiario_id=m.beneficiario_id, turma_id=m.turma_id, aceito_por_id=m.aceito_por_id,
        aceito_em=m.aceito_em, criado_em=m.criado_em,
    )


class InscricaoListaEsperaRepository:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, inscricao: InscricaoListaEspera) -> InscricaoListaEspera:
        m = InscricaoListaEsperaModel(
            nome_completo=inscricao.nome_completo, data_nascimento=inscricao.data_nascimento,
            documento=inscricao.documento, nome_responsavel=inscricao.nome_responsavel,
            documento_responsavel=inscricao.documento_responsavel,
            telefone_whatsapp=inscricao.telefone_whatsapp, email=inscricao.email,
            bairro=inscricao.bairro, cidade=inscricao.cidade, modalidade_id=inscricao.modalidade_id,
            polo_id=inscricao.polo_id, como_conheceu=inscricao.como_conheceu,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def buscar_por_id(self, inscricao_id: UUID) -> InscricaoListaEspera | None:
        m = self.db.get(InscricaoListaEsperaModel, inscricao_id)
        return _to_entity(m) if m else None

    def listar_pendentes(self, polo_id: UUID | None = None) -> list[InscricaoListaEspera]:
        stmt = select(InscricaoListaEsperaModel).where(InscricaoListaEsperaModel.beneficiario_id.is_(None))
        if polo_id:
            stmt = stmt.where(InscricaoListaEsperaModel.polo_id == polo_id)
        stmt = stmt.order_by(InscricaoListaEsperaModel.criado_em)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def marcar_aceita(
        self, inscricao_id: UUID, beneficiario_id: UUID, turma_id: UUID, aceito_por_id: UUID,
    ) -> InscricaoListaEspera | None:
        m = self.db.get(InscricaoListaEsperaModel, inscricao_id)
        if not m:
            return None
        m.beneficiario_id = beneficiario_id
        m.turma_id = turma_id
        m.aceito_por_id = aceito_por_id
        m.aceito_em = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)
