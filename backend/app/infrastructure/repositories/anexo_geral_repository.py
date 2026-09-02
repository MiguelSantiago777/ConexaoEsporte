"""Repositório do repositório livre de Anexos Gerais por polo."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.anexo_geral.entities import AnexoGeral
from app.infrastructure.database.models import AnexoGeralModel


def _to_entity(m: AnexoGeralModel) -> AnexoGeral:
    return AnexoGeral(
        id=m.id, polo_id=m.polo_id, titulo=m.titulo, nome_arquivo=m.nome_arquivo,
        caminho_arquivo=m.caminho_arquivo, content_type=m.content_type, tamanho_bytes=m.tamanho_bytes,
        enviado_por_id=m.enviado_por_id, criado_em=m.criado_em,
    )


class AnexoGeralRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, polo_id: UUID | None = None) -> list[AnexoGeral]:
        stmt = select(AnexoGeralModel).order_by(AnexoGeralModel.criado_em.desc())
        if polo_id:
            stmt = stmt.where(AnexoGeralModel.polo_id == polo_id)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def buscar_por_id(self, anexo_id: UUID) -> AnexoGeral | None:
        m = self.db.get(AnexoGeralModel, anexo_id)
        return _to_entity(m) if m else None

    def criar(self, anexo: AnexoGeral) -> AnexoGeral:
        m = AnexoGeralModel(
            polo_id=anexo.polo_id, titulo=anexo.titulo,
            nome_arquivo=anexo.nome_arquivo, caminho_arquivo=anexo.caminho_arquivo,
            content_type=anexo.content_type, tamanho_bytes=anexo.tamanho_bytes,
            enviado_por_id=anexo.enviado_por_id,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def remover(self, anexo_id: UUID) -> None:
        m = self.db.get(AnexoGeralModel, anexo_id)
        if m:
            self.db.delete(m)
            self.db.commit()
