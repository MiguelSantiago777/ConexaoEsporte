"""Repositório do token de 'esqueci minha senha' (redefinicoes_senha)."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import RedefinicaoSenhaModel


class RedefinicaoSenhaRepository:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, usuario_id: UUID, token_hash: str, expira_em: datetime) -> RedefinicaoSenhaModel:
        m = RedefinicaoSenhaModel(usuario_id=usuario_id, token_hash=token_hash, expira_em=expira_em)
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return m

    def buscar_por_token_hash(self, token_hash: str) -> RedefinicaoSenhaModel | None:
        return self.db.scalar(select(RedefinicaoSenhaModel).where(RedefinicaoSenhaModel.token_hash == token_hash))

    def marcar_usado(self, redefinicao_id: UUID) -> None:
        m = self.db.get(RedefinicaoSenhaModel, redefinicao_id)
        if not m:
            return
        m.usado_em = datetime.now(timezone.utc)
        self.db.commit()

    def invalidar_pendentes_do_usuario(self, usuario_id: UUID) -> None:
        """Marca como usado qualquer token anterior ainda válido do mesmo
        usuário, ao gerar um novo — evita que vários links de redefinição
        pedidos em sequência fiquem todos utilizáveis ao mesmo tempo."""
        agora = datetime.now(timezone.utc)
        stmt = select(RedefinicaoSenhaModel).where(
            RedefinicaoSenhaModel.usuario_id == usuario_id,
            RedefinicaoSenhaModel.usado_em.is_(None),
            RedefinicaoSenhaModel.expira_em > agora,
        )
        for m in self.db.scalars(stmt):
            m.usado_em = agora
        self.db.commit()
