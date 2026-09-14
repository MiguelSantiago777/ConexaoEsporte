"""Use case de Autenticação: login com email/senha, emissão de JWT e o fluxo
de 'esqueci minha senha' (token de uso único enviado por email)."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.email.service import EmailService
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain.enums import PerfilUsuario
from app.domain.shared.exceptions import AcessoNegado, RegraDeNegocioViolada
from app.infrastructure.repositories.papel_repository import PapelRepository
from app.infrastructure.repositories.redefinicao_senha_repository import RedefinicaoSenhaRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository

_HORAS_VALIDADE_TOKEN_REDEFINICAO_SENHA = 1


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _como_utc(momento: datetime) -> datetime:
    """SQLite (usado nos testes) não preserva o tzinfo de colunas
    DateTime(timezone=True) na volta do banco — o valor lido vem naive,
    mas sempre foi gravado em UTC. No Postgres de produção o driver já
    devolve aware. Normaliza os dois casos antes de comparar."""
    return momento if momento.tzinfo else momento.replace(tzinfo=timezone.utc)


class AuthService:
    def __init__(self, db: Session):
        self.repo = UsuarioRepository(db)
        self.papel_repo = PapelRepository(db)
        self.redefinicao_repo = RedefinicaoSenhaRepository(db)
        self.email_service = EmailService()

    def _modulos_do_usuario(self, usuario) -> list[str]:
        """Só resolvido pra quem é PERSONALIZADO — os outros perfis têm
        regras fixas de acesso e não usam módulo nenhum."""
        if usuario.perfil != PerfilUsuario.PERSONALIZADO or not usuario.papel_id:
            return []
        papel = self.papel_repo.buscar_por_id(usuario.papel_id)
        return papel.modulos if papel and papel.ativo else []

    def autenticar(self, email: str, senha: str) -> dict:
        usuario = self.repo.buscar_por_email(email)
        if not usuario or not usuario.ativo or not verify_password(senha, usuario.senha_hash):
            raise AcessoNegado("Email ou senha inválidos.")

        access = create_access_token(
            usuario_id=str(usuario.id), perfil=usuario.perfil.value,
            polo_id=str(usuario.polo_id) if usuario.polo_id else None,
            almoxarifado_id=str(usuario.almoxarifado_id) if usuario.almoxarifado_id else None,
            modulos=self._modulos_do_usuario(usuario),
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
            almoxarifado_id=str(usuario.almoxarifado_id) if usuario.almoxarifado_id else None,
            modulos=self._modulos_do_usuario(usuario),
        )
        return {"access_token": access, "refresh_token": refresh_token, "token_type": "bearer"}

    def alterar_senha(self, usuario_id: UUID, senha_atual: str, nova_senha: str) -> None:
        usuario = self.repo.buscar_por_id(usuario_id)
        if not usuario or not verify_password(senha_atual, usuario.senha_hash):
            raise AcessoNegado("Senha atual incorreta.")
        if verify_password(nova_senha, usuario.senha_hash):
            raise RegraDeNegocioViolada("A nova senha deve ser diferente da senha atual.")
        self.repo.atualizar_senha(usuario_id, hash_password(nova_senha))

    def solicitar_redefinicao_senha(self, email: str) -> None:
        """Sempre retorna silenciosamente, exista ou não o email — a resposta
        do endpoint não pode revelar se um email está cadastrado no sistema."""
        usuario = self.repo.buscar_por_email(email)
        if not usuario or not usuario.ativo:
            return

        self.redefinicao_repo.invalidar_pendentes_do_usuario(usuario.id)

        token = secrets.token_urlsafe(32)
        expira_em = datetime.now(timezone.utc) + timedelta(hours=_HORAS_VALIDADE_TOKEN_REDEFINICAO_SENHA)
        self.redefinicao_repo.criar(usuario.id, token_hash=_hash_token(token), expira_em=expira_em)

        link = f"{settings.FRONTEND_URL.rstrip('/')}/redefinir-senha?token={token}"
        self.email_service.enviar_redefinicao_senha(
            destinatario=usuario.email, nome=usuario.nome, link=link,
            horas_validade=_HORAS_VALIDADE_TOKEN_REDEFINICAO_SENHA,
        )

    def redefinir_senha(self, token: str, nova_senha: str) -> None:
        registro = self.redefinicao_repo.buscar_por_token_hash(_hash_token(token))
        agora = datetime.now(timezone.utc)
        if not registro or registro.usado_em or _como_utc(registro.expira_em) < agora:
            raise RegraDeNegocioViolada("Token de redefinição inválido ou expirado.")

        self.redefinicao_repo.marcar_usado(registro.id)
        self.repo.atualizar_senha(registro.usuario_id, hash_password(nova_senha))
