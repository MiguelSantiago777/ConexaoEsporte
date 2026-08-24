"""Rotas de Autenticação (JWT: access + refresh). Tag Swagger: 'Autenticação'."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.application.auth.service import AuthService
from app.core.dependencies import CurrentUser, DbSession
from app.domain.shared.exceptions import AcessoNegado
from app.interfaces.api.v1.schemas.auth_schemas import (
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
    "**Authorize** do Swagger para testar as rotas protegidas.",
)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> TokenResponse:
    service = AuthService(db)
    try:
        tokens = service.autenticar(email=form.username, senha=form.password)
    except AcessoNegado as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return TokenResponse(**tokens)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar access token",
    description="Recebe um refresh token válido e devolve um novo access token.",
)
def refresh(body: RefreshTokenRequest, db: DbSession) -> TokenResponse:
    service = AuthService(db)
    try:
        tokens = service.renovar_access_token(body.refresh_token)
    except AcessoNegado as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return TokenResponse(**tokens)


@router.get(
    "/me",
    response_model=UsuarioLogadoResponse,
    summary="Dados do usuário autenticado",
    description="Retorna o perfil e o polo vinculado do usuário do token atual.",
)
def me(usuario: CurrentUser, db: DbSession) -> UsuarioLogadoResponse:
    from app.infrastructure.repositories.usuario_repository import UsuarioRepository

    u = UsuarioRepository(db).buscar_por_id(usuario.id)
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return UsuarioLogadoResponse(
        id=u.id, nome=u.nome, email=u.email, perfil=u.perfil.value, polo_id=u.polo_id
    )
