"""Rotas de Usuários (funcionários). Tag Swagger: 'Usuários'."""
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response

from app.application.usuario.documento_service import UsuarioDocumentoService
from app.application.usuario.service import UsuarioService
from app.core.dependencies import DbSession, UsuarioAutenticado, require_perfis
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.routers._arquivo_helper import resposta_download
from app.interfaces.api.v1.schemas.paginacao_schemas import PaginaResponse
from app.interfaces.api.v1.schemas.usuario_schemas import (
    UsuarioCreateRequest,
    UsuarioDocumentoResponse,
    UsuarioResponse,
    UsuarioUpdateRequest,
)

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

# MASTER cria qualquer usuário; GESTOR_POLO só cria PROFESSOR no próprio polo.
MasterOuGestor = Annotated[
    UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO))
]


def _assert_acesso_ao_usuario_alvo(usuario: UsuarioAutenticado, db: DbSession, usuario_alvo_id: UUID):
    """GESTOR_POLO só acessa anexos de professores do seu polo. MASTER tem acesso irrestrito."""
    alvo = UsuarioService(db).buscar_usuario(usuario_alvo_id)
    if not alvo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    if usuario.perfil != PerfilUsuario.MASTER:
        if alvo.perfil != PerfilUsuario.PROFESSOR or alvo.polo_id != usuario.polo_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Gestor só pode acessar anexos de professores do próprio polo.",
            )
    return alvo


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
    response_model=list[UsuarioResponse] | PaginaResponse[UsuarioResponse],
    summary="Listar usuários",
    description="MASTER lista todos. GESTOR_POLO lista apenas os do seu polo. Filtre por `perfil` "
    "(ex.: PROFESSOR) e informe `pagina` pra paginar — sem `pagina`, devolve a lista inteira.",
)
def listar_usuarios(
    usuario: MasterOuGestor, db: DbSession,
    perfil: PerfilUsuario | None = None,
    pagina: Annotated[int | None, Query(ge=1)] = None,
    tamanho_pagina: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[UsuarioResponse] | PaginaResponse[UsuarioResponse]:
    service = UsuarioService(db)
    filtro_polo = usuario.polo_id if usuario.perfil == PerfilUsuario.GESTOR_POLO else None

    if pagina is None:
        itens = service.listar_usuarios(polo_id=filtro_polo)
        if perfil:
            itens = [u for u in itens if u.perfil == perfil]
        return [UsuarioResponse.model_validate(u) for u in itens]

    itens, total = service.listar_usuarios_pagina(
        pagina=pagina, tamanho_pagina=tamanho_pagina, polo_id=filtro_polo, perfil=perfil
    )
    return PaginaResponse(
        itens=[UsuarioResponse.model_validate(u) for u in itens], total=total, pagina=pagina, tamanho_pagina=tamanho_pagina
    )


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


@router.post(
    "/{usuario_id}/documentos",
    response_model=UsuarioDocumentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar anexo do professor (foto, documento ou contrato)",
    description="Envia um arquivo por chamada (multipart/form-data). Tipos aceitos: PDF, JPG, PNG, WEBP — "
    "até 10MB cada. Chame novamente para anexar mais de um documento do mesmo tipo.",
)
async def enviar_documento_usuario(
    usuario_id: UUID,
    usuario: MasterOuGestor,
    db: DbSession,
    tipo: Literal["FOTO", "DOCUMENTO", "CONTRATO"] = Form(...),
    arquivo: UploadFile = File(...),
) -> UsuarioDocumentoResponse:
    _assert_acesso_ao_usuario_alvo(usuario, db, usuario_id)
    criado = await UsuarioDocumentoService(db).enviar(usuario_id, tipo, arquivo, usuario.id)
    return UsuarioDocumentoResponse.model_validate(criado)


@router.get(
    "/{usuario_id}/documentos",
    response_model=list[UsuarioDocumentoResponse],
    summary="Listar anexos do professor",
)
def listar_documentos_usuario(usuario_id: UUID, usuario: MasterOuGestor, db: DbSession) -> list[UsuarioDocumentoResponse]:
    _assert_acesso_ao_usuario_alvo(usuario, db, usuario_id)
    return [UsuarioDocumentoResponse.model_validate(d) for d in UsuarioDocumentoService(db).listar(usuario_id)]


@router.get(
    "/documentos/{documento_id}/arquivo",
    summary="Baixar um anexo do professor",
    description="Retorna o arquivo binário (PDF/imagem). Acesso restrito ao polo do professor dono do anexo.",
)
def baixar_documento_usuario(documento_id: UUID, usuario: MasterOuGestor, db: DbSession) -> Response:
    service = UsuarioDocumentoService(db)
    documento = service.buscar(documento_id)
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")
    _assert_acesso_ao_usuario_alvo(usuario, db, documento.usuario_id)

    from app.infrastructure.storage.armazenamento_documentos import armazenamento_usuario_documentos

    with armazenamento_usuario_documentos.abrir(documento.caminho_arquivo) as f:
        conteudo = f.read()
    return resposta_download(conteudo, documento.content_type, documento.nome_arquivo)


@router.delete(
    "/documentos/{documento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover um anexo do professor",
)
def remover_documento_usuario(documento_id: UUID, usuario: MasterOuGestor, db: DbSession) -> None:
    service = UsuarioDocumentoService(db)
    documento = service.buscar(documento_id)
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")
    _assert_acesso_ao_usuario_alvo(usuario, db, documento.usuario_id)
    service.remover(documento_id)
