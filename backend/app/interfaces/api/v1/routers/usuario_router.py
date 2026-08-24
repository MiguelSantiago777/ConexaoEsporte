"""Rotas de Usuários (funcionários). Tag Swagger: 'Usuários'."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.application.usuario.service import UsuarioService
from app.core.dependencies import DbSession, require_perfis
from app.domain.enums import PerfilUsuario
from app.domain.shared.exceptions import RegraDeNegocioViolada
from app.interfaces.api.v1.schemas.usuario_schemas import UsuarioCreateRequest, UsuarioResponse
from fastapi import Depends
from typing import Annotated
from app.core.dependencies import UsuarioAutenticado

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

# MASTER cria qualquer usuário; GESTOR_POLO só cria PROFESSOR no próprio polo.
MasterOuGestor = Annotated[
    UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO))
]


@router.post(
    "",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar usuário (funcionário)",
    description="**MASTER** pode cadastrar qualquer perfil. **GESTOR_POLO** pode "
    "cadastrar apenas **PROFESSOR**, sempre vinculado ao seu próprio polo.",
)
def criar_usuario(body: UsuarioCreateRequest, usuario: MasterOuGestor, db: DbSession) -> UsuarioResponse:
    service = UsuarioService(db)
    try:
        criado = service.criar_usuario(
            nome=body.nome, email=body.email, senha=body.senha, perfil=body.perfil,
            polo_id=body.polo_id, criado_por_perfil=usuario.perfil, criado_por_polo_id=usuario.polo_id,
        )
    except RegraDeNegocioViolada as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return UsuarioResponse.model_validate(criado)


@router.get(
    "",
    response_model=list[UsuarioResponse],
    summary="Listar usuários",
    description="MASTER lista todos. GESTOR_POLO lista apenas os do seu polo.",
)
def listar_usuarios(usuario: MasterOuGestor, db: DbSession) -> list[UsuarioResponse]:
    service = UsuarioService(db)
    filtro_polo = usuario.polo_id if usuario.perfil == PerfilUsuario.GESTOR_POLO else None
    return [UsuarioResponse.model_validate(u) for u in service.listar_usuarios(polo_id=filtro_polo)]
