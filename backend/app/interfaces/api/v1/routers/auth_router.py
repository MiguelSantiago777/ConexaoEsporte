"""Rotas de Autenticação (JWT: access + refresh). Tag Swagger: 'Autenticação'."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.application.auth.service import AuthService
from app.core.dependencies import CurrentUser, DbSession
from app.core.rate_limit import limiter
from app.interfaces.api.v1.schemas.auth_schemas import (
    AlterarSenhaRequest,
    RefreshTokenRequest,
    TokenResponse,
    UsuarioLogadoResponse,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login e emissão de tokens JWT",
    description="Autentica um usuário (MASTER, GESTOR_POLO ou PROFESSOR) e retorna "
    "um **access token** (curta duração) e um **refresh token** (longa duração). "
    "O campo `username` corresponde ao **email**. Use o access token no botão "
    "**Authorize** do Swagger para testar as rotas protegidas.\n\n"
    "Limitado a 10 tentativas por minuto por IP (proteção contra força bruta).",
)
@limiter.limit("10/minute")
def login(
    request: Request,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> TokenResponse:
    service = AuthService(db)
    tokens = service.autenticar(email=form.username, senha=form.password)
    return TokenResponse(**tokens)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar access token",
    description="Recebe um refresh token válido e devolve um novo access token.",
)
def refresh(body: RefreshTokenRequest, db: DbSession) -> TokenResponse:
    service = AuthService(db)
    tokens = service.renovar_access_token(body.refresh_token)
    return TokenResponse(**tokens)


@router.get(
    "/me",
    response_model=UsuarioLogadoResponse,
    summary="Dados do usuário autenticado",
    description="Retorna o perfil e o polo vinculado do usuário do token atual.",
)
def me(usuario: CurrentUser, db: DbSession) -> UsuarioLogadoResponse:
    from app.infrastructure.repositories.almoxarifado_repository import AlmoxarifadoRepository
    from app.infrastructure.repositories.polo_repository import PoloRepository
    from app.infrastructure.repositories.usuario_repository import UsuarioRepository

    u = UsuarioRepository(db).buscar_por_id(usuario.id)
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    polo = PoloRepository(db).buscar_por_id(u.polo_id) if u.polo_id else None
    almoxarifado = AlmoxarifadoRepository(db).buscar_por_id(u.almoxarifado_id) if u.almoxarifado_id else None
    return UsuarioLogadoResponse(
        id=u.id, nome=u.nome, email=u.email, perfil=u.perfil.value, polo_id=u.polo_id,
        polo_nome=polo.nome if polo else None, polo_codigo=polo.codigo if polo else None,
        almoxarifado_id=u.almoxarifado_id, almoxarifado_nome=almoxarifado.nome if almoxarifado else None,
        modulos=usuario.modulos,
    )


@router.patch(
    "/senha",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Alterar a própria senha",
    description="O usuário autenticado troca a própria senha, informando a senha atual para confirmação. "
    "Limitado a 10 tentativas por minuto por IP.",
)
@limiter.limit("10/minute")
def alterar_senha(request: Request, body: AlterarSenhaRequest, usuario: CurrentUser, db: DbSession) -> None:
    service = AuthService(db)
    service.alterar_senha(usuario.id, senha_atual=body.senha_atual, nova_senha=body.nova_senha)
