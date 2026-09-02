"""Repositório dos documentos anexados a um USUÁRIO (foto, documentos e
contrato do cadastro de professor)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.usuario.entities import UsuarioDocumento
from app.infrastructure.database.models import UsuarioDocumentoModel


def _to_entity(m: UsuarioDocumentoModel) -> UsuarioDocumento:
    return UsuarioDocumento(
        id=m.id, usuario_id=m.usuario_id, tipo=m.tipo, nome_arquivo=m.nome_arquivo,
        caminho_arquivo=m.caminho_arquivo, content_type=m.content_type, tamanho_bytes=m.tamanho_bytes,
        enviado_por_id=m.enviado_por_id, criado_em=m.criado_em,
    )


class UsuarioDocumentoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_por_usuario(self, usuario_id: UUID) -> list[UsuarioDocumento]:
        stmt = select(UsuarioDocumentoModel).where(UsuarioDocumentoModel.usuario_id == usuario_id)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def buscar_por_id(self, documento_id: UUID) -> UsuarioDocumento | None:
        m = self.db.get(UsuarioDocumentoModel, documento_id)
        return _to_entity(m) if m else None

    def criar(self, documento: UsuarioDocumento) -> UsuarioDocumento:
        m = UsuarioDocumentoModel(
            usuario_id=documento.usuario_id, tipo=documento.tipo,
            nome_arquivo=documento.nome_arquivo, caminho_arquivo=documento.caminho_arquivo,
            content_type=documento.content_type, tamanho_bytes=documento.tamanho_bytes,
            enviado_por_id=documento.enviado_por_id,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def remover(self, documento_id: UUID) -> None:
        m = self.db.get(UsuarioDocumentoModel, documento_id)
        if m:
            self.db.delete(m)
            self.db.commit()
