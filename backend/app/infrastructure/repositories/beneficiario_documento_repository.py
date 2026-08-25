"""Repositório dos documentos anexados a um BENEFICIÁRIO (certidão, RG, comprovantes)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.beneficiario.entities import BeneficiarioDocumento
from app.infrastructure.database.models import BeneficiarioDocumentoModel


def _to_entity(m: BeneficiarioDocumentoModel) -> BeneficiarioDocumento:
    return BeneficiarioDocumento(
        id=m.id, beneficiario_id=m.beneficiario_id, tipo=m.tipo, nome_arquivo=m.nome_arquivo,
        caminho_arquivo=m.caminho_arquivo, content_type=m.content_type, tamanho_bytes=m.tamanho_bytes,
        enviado_por_id=m.enviado_por_id, criado_em=m.criado_em,
    )


class BeneficiarioDocumentoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_por_beneficiario(self, beneficiario_id: UUID) -> list[BeneficiarioDocumento]:
        stmt = select(BeneficiarioDocumentoModel).where(
            BeneficiarioDocumentoModel.beneficiario_id == beneficiario_id
        )
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def buscar_por_id(self, documento_id: UUID) -> BeneficiarioDocumento | None:
        m = self.db.get(BeneficiarioDocumentoModel, documento_id)
        return _to_entity(m) if m else None

    def criar(self, documento: BeneficiarioDocumento) -> BeneficiarioDocumento:
        m = BeneficiarioDocumentoModel(
            beneficiario_id=documento.beneficiario_id, tipo=documento.tipo,
            nome_arquivo=documento.nome_arquivo, caminho_arquivo=documento.caminho_arquivo,
            content_type=documento.content_type, tamanho_bytes=documento.tamanho_bytes,
            enviado_por_id=documento.enviado_por_id,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)
