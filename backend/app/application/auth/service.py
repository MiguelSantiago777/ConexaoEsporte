"""Use case de Autenticação: login com email/senha e emissão de JWT."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain.shared.exceptions import AcessoNegado, RegraDeNegocioViolada
from app.infrastructure.repositories.usuario_repository import UsuarioRepository


class AuthService:
    def __init__(self, db: Session):
        self.repo = UsuarioRepository(db)

    def autenticar(self, email: str, senha: str) -> dict:
        usuario = self.repo.buscar_por_email(email)
        if not usuario or not usuario.ativo or not verify_password(senha, usuario.senha_hash):
            raise AcessoNegado("Email ou senha inválidos.")

        access = create_access_token(
            usuario_id=str(usuario.id), perfil=usuario.perfil.value,
            polo_id=str(usuario.polo_id) if usuario.polo_id else None,
        )
        refresh = create_refresh_token(usuario_id=str(usuario.id))
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

    def renovar_access_token(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise AcessoNegado("Refresh token inválido ou expirado.")
        if payload.get("type") != "refresh":
            raise AcessoNegado("Token informado não é um refresh token.")

        usuario = self.repo.buscar_por_id(payload["sub"])
        if not usuario or not usuario.ativo:
            raise AcessoNegado("Usuário inválido.")

        access = create_access_token(
            usuario_id=str(usuario.id), perfil=usuario.perfil.value,
            polo_id=str(usuario.polo_id) if usuario.polo_id else None,
        )
        return {"access_token": access, "refresh_token": refresh_token, "token_type": "bearer"}

    def alterar_senha(self, usuario_id: UUID, senha_atual: str, nova_senha: str) -> None:
        usuario = self.repo.buscar_por_id(usuario_id)
        if not usuario or not verify_password(senha_atual, usuario.senha_hash):
            raise AcessoNegado("Senha atual incorreta.")
        if verify_password(nova_senha, usuario.senha_hash):
            raise RegraDeNegocioViolada("A nova senha deve ser diferente da senha atual.")
        self.repo.atualizar_senha(usuario_id, hash_password(nova_senha))
