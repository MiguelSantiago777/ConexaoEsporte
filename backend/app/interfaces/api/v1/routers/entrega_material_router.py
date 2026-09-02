"""Rotas de Entrega de Materiais (Termo de Entrega de Materiais).
Tag Swagger: 'Entregas de Materiais'. MASTER e GESTOR_POLO do próprio polo."""
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.application.entrega_material.service import EntregaMaterialService
from app.application.relatorios.service import RelatorioService
from app.core.dependencies import DbSession, UsuarioAutenticado, assert_acesso_ao_polo, require_perfis
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.routers._arquivo_helper import resposta_relatorio
from app.interfaces.api.v1.schemas.entrega_material_schemas import (
    EntregaMaterialCreateRequest,
    EntregaMaterialResponse,
    EntregaMaterialUpdateRequest,
)
from app.interfaces.api.v1.schemas.paginacao_schemas import PaginaResponse

router = APIRouter(prefix="/entregas-materiais", tags=["Entregas de Materiais"])

MasterOuGestor = Annotated[
    UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO))
]


@router.get(
    "", response_model=list[EntregaMaterialResponse] | PaginaResponse[EntregaMaterialResponse],
    summary="Listar Entregas de Materiais",
    description="MASTER vê todas. GESTOR_POLO vê apenas as do seu polo. Informe `pagina` pra paginar "
    "— sem isso, devolve a lista inteira.",
)
def listar_entregas(
    usuario: MasterOuGestor, db: DbSession, polo_id: UUID | None = None,
    pagina: Annotated[int | None, Query(ge=1)] = None,
    tamanho_pagina: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[EntregaMaterialResponse] | PaginaResponse[EntregaMaterialResponse]:
    filtro_polo = usuario.polo_id if usuario.perfil == PerfilUsuario.GESTOR_POLO else polo_id
    service = EntregaMaterialService(db)

    if pagina is None:
        entregas = service.listar(polo_id=filtro_polo)
        return [EntregaMaterialResponse.model_validate(e) for e in entregas]

    entregas, total = service.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, polo_id=filtro_polo)
    return PaginaResponse(
        itens=[EntregaMaterialResponse.model_validate(e) for e in entregas],
        total=total, pagina=pagina, tamanho_pagina=tamanho_pagina,
    )


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
def exportar_entrega(
    entrega_id: UUID, usuario: MasterOuGestor, db: DbSession, formato: Literal["docx", "pdf"] = "docx"
) -> Response:
    entrega = EntregaMaterialService(db).buscar(entrega_id)
    if not entrega:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrega de materiais não encontrada.")
    assert_acesso_ao_polo(usuario, entrega.polo_id)

    buffer = RelatorioService(db).gerar_termo_entrega(entrega_id)
    return resposta_relatorio(buffer, "Termo de Entrega de Materiais", "docx", formato)
