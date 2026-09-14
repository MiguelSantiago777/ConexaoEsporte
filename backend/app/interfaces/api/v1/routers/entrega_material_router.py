"""Rotas de Entrega de Materiais (Termo de Entrega de Materiais).
Tag Swagger: 'Entregas de Materiais'. MASTER e COORDENADOR_ALMOXARIFADO.

Escopo do Coordenador de Almoxarifado (imposto neste router, nunca no
serviço): só pode despachar itens do próprio almoxarifado (mesma regra já
aplicada em /movimentos-estoque) e só enxerga/edita/exporta/confirma as
entregas que ele mesmo criou — nunca as de outro coordenador. MASTER
continua com acesso irrestrito, igual antes."""
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status

from app.application.entrega_material.service import EntregaMaterialService
from app.application.relatorios.service import RelatorioService
from app.core.dependencies import (
    DbSession,
    UsuarioAutenticado,
    assert_acesso_ao_almoxarifado,
    assert_acesso_ao_polo,
    require_modulo_ou_perfis,
)
from app.domain.entrega_material.entities import EntregaMaterial
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.routers._arquivo_helper import resposta_download, resposta_relatorio
from app.interfaces.api.v1.schemas.entrega_material_schemas import (
    EntregaMaterialCreateRequest,
    EntregaMaterialResponse,
    EntregaMaterialUpdateRequest,
)
from app.interfaces.api.v1.schemas.paginacao_schemas import PaginaResponse

router = APIRouter(prefix="/entregas-materiais", tags=["Entregas de Materiais"])

MasterOuCoordenador = Annotated[
    UsuarioAutenticado,
    Depends(require_modulo_ou_perfis("entregas_materiais", PerfilUsuario.MASTER, PerfilUsuario.COORDENADOR_ALMOXARIFADO)),
]


def _assert_acesso_a_entrega(usuario: UsuarioAutenticado, entrega: EntregaMaterial) -> None:
    """MASTER: irrestrito. COORDENADOR_ALMOXARIFADO: só a própria entrega
    (não é escopado por polo como o GESTOR_POLO — despacha pra qualquer
    polo a partir do seu almoxarifado, mas só mexe no que ele mesmo criou).
    Qualquer outro perfil (ex.: PERSONALIZADO via Central de Acessos) cai no
    escopo por polo de sempre."""
    if usuario.perfil == PerfilUsuario.COORDENADOR_ALMOXARIFADO:
        if entrega.criado_por_id != usuario.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Coordenador só tem acesso às entregas que ele mesmo registrou.",
            )
        return
    assert_acesso_ao_polo(usuario, entrega.polo_id, "entregas_materiais")


def _assert_itens_no_proprio_almoxarifado(usuario: UsuarioAutenticado, itens: list) -> None:
    """Coordenador só pode despachar produtos do próprio almoxarifado —
    mesma regra de /movimentos-estoque. Sem efeito para MASTER."""
    if usuario.perfil != PerfilUsuario.COORDENADOR_ALMOXARIFADO:
        return
    for item in itens:
        almoxarifado_id = item.almoxarifado_id if hasattr(item, "almoxarifado_id") else item.get("almoxarifado_id")
        if almoxarifado_id:
            assert_acesso_ao_almoxarifado(usuario, almoxarifado_id, "entregas_materiais")


@router.get(
    "", response_model=list[EntregaMaterialResponse] | PaginaResponse[EntregaMaterialResponse],
    summary="Listar Entregas de Materiais",
    description="Informe `polo_id` pra filtrar por polo e `pagina` pra paginar — sem isso, devolve a "
    "lista inteira.",
)
def listar_entregas(
    usuario: MasterOuCoordenador, db: DbSession, polo_id: UUID | None = None,
    pagina: Annotated[int | None, Query(ge=1)] = None,
    tamanho_pagina: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[EntregaMaterialResponse] | PaginaResponse[EntregaMaterialResponse]:
    service = EntregaMaterialService(db)
    # Coordenador só vê o que ele mesmo despachou — nunca a operação de
    # outro almoxarifado/coordenador. MASTER continua vendo tudo.
    criado_por_id = usuario.id if usuario.perfil == PerfilUsuario.COORDENADOR_ALMOXARIFADO else None

    if pagina is None:
        entregas = service.listar(polo_id=polo_id, criado_por_id=criado_por_id)
        return [EntregaMaterialResponse.model_validate(e) for e in entregas]

    entregas, total = service.listar_pagina(
        pagina=pagina, tamanho_pagina=tamanho_pagina, polo_id=polo_id, criado_por_id=criado_por_id
    )
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
def criar_entrega(body: EntregaMaterialCreateRequest, usuario: MasterOuCoordenador, db: DbSession) -> EntregaMaterialResponse:
    # Coordenador despacha pra qualquer polo (não é escopado por polo como o
    # GESTOR_POLO) — só os itens do estoque precisam vir do almoxarifado dele.
    _assert_itens_no_proprio_almoxarifado(usuario, body.itens)
    criada = EntregaMaterialService(db).criar(
        polo_id=body.polo_id, data_entrega=body.data_entrega, entregue_por=body.entregue_por,
        itens=[item.model_dump(mode="json") for item in body.itens], criado_por_id=usuario.id,
    )
    return EntregaMaterialResponse.model_validate(criada)


@router.get("/{entrega_id}", response_model=EntregaMaterialResponse, summary="Detalhar Entrega de Materiais")
def buscar_entrega(entrega_id: UUID, usuario: MasterOuCoordenador, db: DbSession) -> EntregaMaterialResponse:
    entrega = EntregaMaterialService(db).buscar(entrega_id)
    if not entrega:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrega de materiais não encontrada.")
    _assert_acesso_a_entrega(usuario, entrega)
    return EntregaMaterialResponse.model_validate(entrega)


@router.patch("/{entrega_id}", response_model=EntregaMaterialResponse, summary="Editar Entrega de Materiais")
def atualizar_entrega(
    entrega_id: UUID, body: EntregaMaterialUpdateRequest, usuario: MasterOuCoordenador, db: DbSession
) -> EntregaMaterialResponse:
    service = EntregaMaterialService(db)
    atual = service.buscar(entrega_id)
    if not atual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrega de materiais não encontrada.")
    _assert_acesso_a_entrega(usuario, atual)
    if body.itens is not None:
        _assert_itens_no_proprio_almoxarifado(usuario, body.itens)

    campos = body.model_dump(exclude_unset=True, mode="json")
    atualizada = service.atualizar(entrega_id, **campos)
    return EntregaMaterialResponse.model_validate(atualizada)


@router.get(
    "/{entrega_id}/exportar",
    summary="Exportar Termo de Entrega de Materiais em .docx",
    description="Gera o arquivo preenchido no layout oficial do modelo, pronto para assinatura.",
)
def exportar_entrega(
    entrega_id: UUID, usuario: MasterOuCoordenador, db: DbSession, formato: Literal["docx", "pdf"] = "docx"
) -> Response:
    entrega = EntregaMaterialService(db).buscar(entrega_id)
    if not entrega:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrega de materiais não encontrada.")
    _assert_acesso_a_entrega(usuario, entrega)

    buffer = RelatorioService(db).gerar_termo_entrega(entrega_id)
    return resposta_relatorio(buffer, "Termo de Entrega de Materiais", "docx", formato)


@router.post(
    "/{entrega_id}/comprovante", response_model=EntregaMaterialResponse,
    summary="Anexar comprovante de recebimento no polo",
    description="Foto ou PDF assinado comprovando que o polo recebeu os materiais — aceita PDF, JPG, "
    "PNG ou WEBP. Enviar de novo substitui o comprovante anterior.",
)
async def enviar_comprovante(
    entrega_id: UUID, usuario: MasterOuCoordenador, db: DbSession, arquivo: Annotated[UploadFile, File()],
    recebido_por: Annotated[str | None, Form()] = None,
) -> EntregaMaterialResponse:
    service = EntregaMaterialService(db)
    atual = service.buscar(entrega_id)
    if not atual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrega de materiais não encontrada.")
    _assert_acesso_a_entrega(usuario, atual)
    atualizada = await service.enviar_comprovante(entrega_id, arquivo, recebido_por=recebido_por)
    return EntregaMaterialResponse.model_validate(atualizada)


@router.get("/{entrega_id}/comprovante", summary="Baixar o comprovante de recebimento no polo")
def baixar_comprovante(entrega_id: UUID, usuario: MasterOuCoordenador, db: DbSession) -> Response:
    service = EntregaMaterialService(db)
    entrega = service.buscar(entrega_id)
    if not entrega:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrega de materiais não encontrada.")
    _assert_acesso_a_entrega(usuario, entrega)
    _, conteudo = service.abrir_comprovante(entrega_id)
    return resposta_download(conteudo, entrega.comprovante_content_type, entrega.comprovante_nome_arquivo or "comprovante")
