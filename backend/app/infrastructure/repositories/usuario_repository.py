"""Repositório de Usuário — traduz entre UsuarioModel (ORM) e Usuario (domínio)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import PerfilUsuario
from app.domain.usuario.entities import Usuario
from app.infrastructure.database.models import UsuarioModel


def _to_entity(m: UsuarioModel) -> Usuario:
    return Usuario(
        id=m.id, nome=m.nome, email=m.email, senha_hash=m.senha_hash,
        perfil=PerfilUsuario(m.perfil), polo_id=m.polo_id, ativo=m.ativo,
    )


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def buscar_por_email(self, email: str) -> Usuario | None:
        m = self.db.scalar(select(UsuarioModel).where(UsuarioModel.email == email))
        return _to_entity(m) if m else None

    def buscar_por_id(self, usuario_id: UUID) -> Usuario | None:
        m = self.db.get(UsuarioModel, usuario_id)
        return _to_entity(m) if m else None

    def listar(self, polo_id: UUID | None = None) -> list[Usuario]:
        stmt = select(UsuarioModel)
        if polo_id:
            stmt = stmt.where(UsuarioModel.polo_id == polo_id)
        return [_to_entity(m) for m in self.db.scalars(stmt)]

    def criar(self, usuario: Usuario) -> Usuario:
        m = UsuarioModel(
            nome=usuario.nome, email=usuario.email, senha_hash=usuario.senha_hash,
            perfil=usuario.perfil.value, polo_id=usuario.polo_id, ativo=usuario.ativo,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def atualizar_senha(self, usuario_id: UUID, novo_senha_hash: str) -> None:
        m = self.db.get(UsuarioModel, usuario_id)
        if not m:
            return
        m.senha_hash = novo_senha_hash
        self.db.commit()
