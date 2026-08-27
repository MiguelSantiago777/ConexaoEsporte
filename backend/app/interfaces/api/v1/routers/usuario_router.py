"""Rotas de Usuários (funcionários). Tag Swagger: 'Usuários'."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.usuario.service import UsuarioService
from app.core.dependencies import DbSession, UsuarioAutenticado, require_perfis
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.schemas.usuario_schemas import (
    UsuarioCreateRequest,
    UsuarioResponse,
    UsuarioUpdateRequest,
)

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
    criado = service.criar_usuario(
        nome=body.nome, email=body.email, senha=body.senha, perfil=body.perfil,
        polo_id=body.polo_id, criado_por_perfil=usuario.perfil, criado_por_polo_id=usuario.polo_id,
        telefone=body.telefone, carga_horaria_semanal=body.carga_horaria_semanal,
    )
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


@router.patch(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Editar usuário (funcionário)",
    description="**MASTER** pode editar qualquer usuário. **GESTOR_POLO** só pode editar "
    "**PROFESSOR** do próprio polo (ex.: telefone e carga horária para a Planilha de Núcleos).",
)
def atualizar_usuario(
    usuario_id: UUID, body: UsuarioUpdateRequest, usuario: MasterOuGestor, db: DbSession
) -> UsuarioResponse:
    service = UsuarioService(db)
    alvo = service.buscar_usuario(usuario_id)
    if not alvo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    if usuario.perfil == PerfilUsuario.GESTOR_POLO:
        if alvo.perfil != PerfilUsuario.PROFESSOR or alvo.polo_id != usuario.polo_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Gestor só pode editar professores do próprio polo.",
            )
        if body.polo_id is not None or body.ativo is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Gestor não pode alterar polo/situação do professor.",
            )

    atualizado = service.atualizar_usuario(usuario_id, **body.model_dump(exclude_unset=True))
    return UsuarioResponse.model_validate(atualizado)
