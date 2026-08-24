"""
Dependências reutilizáveis do FastAPI para autenticação e autorização (RBAC).

Estratégia de controle de acesso por Polo:
- MASTER: enxerga tudo, sem filtro de polo_id.
- GESTOR_POLO: só pode operar dentro do seu próprio polo_id (vindo do token).
- PROFESSOR: só pode operar dentro das turmas às quais está vinculado.

As rotas usam `require_perfis(...)` para restringir por perfil, e a função
`assert_acesso_ao_polo(...)` / `assert_acesso_a_turma(...)` para impor o
escopo de dados dentro do próprio perfil (ex.: GESTOR_POLO do Polo A não
pode mexer em dados do Polo B).
"""
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.domain.enums import PerfilUsuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@dataclass
class UsuarioAutenticado:
    id: UUID
    perfil: PerfilUsuario
    polo_id: UUID | None  # relevante para GESTOR_POLO


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UsuarioAutenticado:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        usuario_id = payload.get("sub")
        perfil = payload.get("perfil")
        polo_id = payload.get("polo_id")
        if usuario_id is None or perfil is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return UsuarioAutenticado(
        id=UUID(usuario_id),
        perfil=PerfilUsuario(perfil),
        polo_id=UUID(polo_id) if polo_id else None,
    )


def require_perfis(*perfis_permitidos: PerfilUsuario):
    """Factory de dependência: restringe o endpoint a um conjunto de perfis."""

    def _checker(
        usuario: Annotated[UsuarioAutenticado, Depends(get_current_user)]
    ) -> UsuarioAutenticado:
        if usuario.perfil not in perfis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Perfil sem permissão para executar esta ação.",
            )
        return usuario

    return _checker


def assert_acesso_ao_polo(usuario: UsuarioAutenticado, polo_id: UUID) -> None:
    """
    Garante que um GESTOR_POLO só acesse o seu próprio polo.
    MASTER tem acesso irrestrito. PROFESSOR não deve chamar isso diretamente
    (use assert_acesso_a_turma).
    """
    if usuario.perfil == PerfilUsuario.MASTER:
        return
    if usuario.perfil == PerfilUsuario.GESTOR_POLO:
        if usuario.polo_id != polo_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Gestor não tem acesso a dados de outro Polo.",
            )
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Perfil sem permissão para acessar recursos de Polo.",
    )


def assert_acesso_a_turma(usuario: UsuarioAutenticado, db: Session, turma_id: UUID) -> None:
    """
    Garante que um PROFESSOR só acesse turmas às quais está vinculado,
    e que um GESTOR_POLO só acesse turmas do seu próprio polo.
    """
    from app.infrastructure.database.models import TurmaModel  # import local evita ciclo

    turma = db.get(TurmaModel, turma_id)
    if turma is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma não encontrada.")

    if usuario.perfil == PerfilUsuario.MASTER:
        return
    if usuario.perfil == PerfilUsuario.GESTOR_POLO:
        if turma.polo_id != usuario.polo_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Turma fora do seu Polo.")
        return
    if usuario.perfil == PerfilUsuario.PROFESSOR:
        if turma.professor_id != usuario.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Professor não vinculado a esta Turma.",
            )
        return


DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[UsuarioAutenticado, Depends(get_current_user)]
