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
from dataclasses import dataclass, field
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.domain.enums import PerfilUsuario

# Esquema "Bearer" puro: no Swagger, o botão Authorize pede só o token JWT
# colado (sem os campos de client_id/client_secret do fluxo OAuth2 padrão).
# O login em si continua em POST /auth/login (form email/senha), que emite
# o token a ser colado aqui.
bearer_scheme = HTTPBearer(auto_error=True, description="Cole o access_token retornado por POST /auth/login.")


@dataclass
class UsuarioAutenticado:
    id: UUID
    perfil: PerfilUsuario
    polo_id: UUID | None  # relevante para GESTOR_POLO
    almoxarifado_id: UUID | None = None  # relevante para COORDENADOR_ALMOXARIFADO
    modulos: list[str] = field(default_factory=list)  # relevante só para PERSONALIZADO (Central de Acessos)

    def tem_modulo(self, modulo: str) -> bool:
        return self.perfil == PerfilUsuario.PERSONALIZADO and modulo in self.modulos


def get_current_user(
    auth: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> UsuarioAutenticado:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(auth.credentials)
        if payload.get("type") != "access":
            raise credentials_exception
        usuario_id = payload.get("sub")
        perfil = payload.get("perfil")
        polo_id = payload.get("polo_id")
        almoxarifado_id = payload.get("almoxarifado_id")
        modulos = payload.get("modulos") or []
        if usuario_id is None or perfil is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return UsuarioAutenticado(
        id=UUID(usuario_id),
        perfil=PerfilUsuario(perfil),
        polo_id=UUID(polo_id) if polo_id else None,
        almoxarifado_id=UUID(almoxarifado_id) if almoxarifado_id else None,
        modulos=modulos,
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


def require_modulo_ou_perfis(modulo: str, *perfis_permitidos: PerfilUsuario):
    """Factory de dependência da Central de Acessos: além dos perfis fixos
    de sempre, também libera quem tem perfil PERSONALIZADO com este módulo
    no Papel vinculado — sem alterar em nada o comportamento pros perfis
    fixos (MASTER, GESTOR_POLO, PROFESSOR, COORDENADOR_ALMOXARIFADO)."""

    def _checker(
        usuario: Annotated[UsuarioAutenticado, Depends(get_current_user)]
    ) -> UsuarioAutenticado:
        if usuario.perfil in perfis_permitidos or usuario.tem_modulo(modulo):
            return usuario
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Perfil sem permissão para executar esta ação.",
        )

    return _checker


def assert_acesso_ao_polo(usuario: UsuarioAutenticado, polo_id: UUID, *modulos_extras: str) -> None:
    """
    Garante que um GESTOR_POLO só acesse o seu próprio polo.
    MASTER tem acesso irrestrito. PROFESSOR não deve chamar isso diretamente
    (use assert_acesso_a_turma). `modulos_extras` deixa cada chamador dizer
    qual módulo da Central de Acessos também libera acesso irrestrito ali
    (ex.: quem chama de dentro de Beneficiários passa "beneficiarios").
    """
    if usuario.perfil == PerfilUsuario.MASTER or any(usuario.tem_modulo(m) for m in modulos_extras):
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


def assert_acesso_ao_almoxarifado(usuario: UsuarioAutenticado, almoxarifado_id: UUID, *modulos_extras: str) -> None:
    """
    Garante que um COORDENADOR_ALMOXARIFADO só acesse o seu próprio
    almoxarifado. MASTER e GESTOR_POLO têm acesso irrestrito (o catálogo de
    Estoque já é visível a eles sem escopo por almoxarifado). `modulos_extras`
    deixa cada chamador dizer qual módulo da Central de Acessos também
    libera acesso irrestrito ali.
    """
    if usuario.perfil in (PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO):
        return
    if any(usuario.tem_modulo(m) for m in modulos_extras):
        return
    if usuario.perfil == PerfilUsuario.COORDENADOR_ALMOXARIFADO:
        if usuario.almoxarifado_id != almoxarifado_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Coordenador não tem acesso a outro almoxarifado.",
            )
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Perfil sem permissão para acessar recursos de Almoxarifado.",
    )


def assert_acesso_a_turma(usuario: UsuarioAutenticado, db: Session, turma_id: UUID, *modulos_extras: str) -> None:
    """
    Garante que um PROFESSOR só acesse turmas às quais está vinculado,
    e que um GESTOR_POLO só acesse turmas do seu próprio polo.
    `modulos_extras` deixa cada chamador dizer qual módulo da Central de
    Acessos também libera acesso irrestrito ali (normalmente "turmas").
    """
    from app.infrastructure.database.models import TurmaModel  # import local evita ciclo

    turma = db.get(TurmaModel, turma_id)
    if turma is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma não encontrada.")

    if usuario.perfil == PerfilUsuario.MASTER or any(usuario.tem_modulo(m) for m in modulos_extras):
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

    # Nega por padrão: qualquer perfil que não seja um dos três acima (ex.:
    # COORDENADOR_ALMOXARIFADO) não tem nenhum acesso a Turmas.
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil sem permissão para acessar Turmas.")


DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[UsuarioAutenticado, Depends(get_current_user)]
