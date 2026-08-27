"""Rotas de Entrega de Materiais (Termo de Entrega de Materiais).
Tag Swagger: 'Entregas de Materiais'. MASTER e GESTOR_POLO do próprio polo."""
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.application.entrega_material.service import EntregaMaterialService
from app.application.relatorios.service import RelatorioService
from app.core.dependencies import DbSession, UsuarioAutenticado, assert_acesso_ao_polo, require_perfis
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.schemas.entrega_material_schemas import (
    EntregaMaterialCreateRequest,
    EntregaMaterialResponse,
    EntregaMaterialUpdateRequest,
)

router = APIRouter(prefix="/entregas-materiais", tags=["Entregas de Materiais"])

MasterOuGestor = Annotated[
    UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO))
]


@router.get(
    "", response_model=list[EntregaMaterialResponse],
    summary="Listar Entregas de Materiais",
    description="MASTER vê todas. GESTOR_POLO vê apenas as do seu polo.",
)
def listar_entregas(usuario: MasterOuGestor, db: DbSession, polo_id: UUID | None = None) -> list[EntregaMaterialResponse]:
    filtro_polo = usuario.polo_id if usuario.perfil == PerfilUsuario.GESTOR_POLO else polo_id
    entregas = EntregaMaterialService(db).listar(polo_id=filtro_polo)
    return [EntregaMaterialResponse.model_validate(e) for e in entregas]


@router.post(
    "", response_model=EntregaMaterialResponse, status_code=status.HTTP_201_CREATED,
    summary="Registrar Entrega de Materiais",
    description="O coordenador exibido no termo é copiado do responsável cadastrado no polo no "
    "momento da criação — edite pelo PATCH se precisar corrigir.",
)
def criar_entrega(body: EntregaMaterialCreateRequest, usuario: MasterOuGestor, db: DbSession) -> EntregaMaterialResponse:
    assert_acesso_ao_polo(usuario, body.polo_id)
    criada = EntregaMaterialService(db).criar(
        polo_id=body.polo_id, data_entrega=body.data_entrega, entregue_por=body.entregue_por,
        itens=[item.model_dump() for item in body.itens], criado_por_id=usuario.id,
    )
    return EntregaMaterialResponse.model_validate(criada)


@router.get("/{entrega_id}", response_model=EntregaMaterialResponse, summary="Detalhar Entrega de Materiais")
def buscar_entrega(entrega_id: UUID, usuario: MasterOuGestor, db: DbSession) -> EntregaMaterialResponse:
    entrega = EntregaMaterialService(db).buscar(entrega_id)
    if not entrega:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrega de materiais não encontrada.")
    assert_acesso_ao_polo(usuario, entrega.polo_id)
    return EntregaMaterialResponse.model_validate(entrega)


@router.patch("/{entrega_id}", response_model=EntregaMaterialResponse, summary="Editar Entrega de Materiais")
def atualizar_entrega(
    entrega_id: UUID, body: EntregaMaterialUpdateRequest, usuario: MasterOuGestor, db: DbSession
) -> EntregaMaterialResponse:
    service = EntregaMaterialService(db)
    atual = service.buscar(entrega_id)
    if not atual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrega de materiais não encontrada.")
    assert_acesso_ao_polo(usuario, atual.polo_id)

    campos = body.model_dump(exclude_unset=True)
    if campos.get("itens") is not None:
        campos["itens"] = [item for item in campos["itens"]]
    atualizada = service.atualizar(entrega_id, **campos)
    return EntregaMaterialResponse.model_validate(atualizada)


@router.get(
    "/{entrega_id}/exportar",
    summary="Exportar Termo de Entrega de Materiais em .docx",
    description="Gera o arquivo preenchido no layout oficial do modelo, pronto para assinatura.",
)
def exportar_entrega(entrega_id: UUID, usuario: MasterOuGestor, db: DbSession) -> Response:
    entrega = EntregaMaterialService(db).buscar(entrega_id)
    if not entrega:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrega de materiais não encontrada.")
    assert_acesso_ao_polo(usuario, entrega.polo_id)

    buffer = RelatorioService(db).gerar_termo_entrega(entrega_id)
    nome_arquivo = "Termo de Entrega de Materiais.docx"
    nome_ascii = nome_arquivo.encode("ascii", errors="replace").decode("ascii")
    content_disposition = f'attachment; filename="{nome_ascii}"; filename*=UTF-8\'\'{quote(nome_arquivo)}'
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": content_disposition},
    )
