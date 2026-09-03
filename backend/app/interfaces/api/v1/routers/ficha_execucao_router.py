"""Rotas de Ficha de Execução (Ficha Técnica de Execução da Entidade).
Tag Swagger: 'Fichas de Execução'. Exclusivo do MASTER."""
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.application.ficha_execucao.service import FichaExecucaoService
from app.application.relatorios.ficha_execucao_export_service import exportar_ficha_execucao
from app.application.relatorios.cabecalho_convenio import texto_cabecalho
from app.core.dependencies import DbSession, UsuarioAutenticado, require_modulo_ou_perfis
from app.domain.enums import PerfilUsuario
from app.infrastructure.repositories.configuracao_geral_repository import ConfiguracaoGeralRepository
from app.infrastructure.repositories.polo_repository import PoloRepository
from app.interfaces.api.v1.routers._arquivo_helper import resposta_relatorio
from app.interfaces.api.v1.schemas.ficha_execucao_schemas import (
    FichaExecucaoCreateRequest,
    FichaExecucaoResponse,
    FichaExecucaoUpdateRequest,
)
from app.interfaces.api.v1.schemas.paginacao_schemas import PaginaResponse

router = APIRouter(prefix="/fichas-execucao", tags=["Fichas de Execução"])

SomenteMaster = Annotated[
    UsuarioAutenticado, Depends(require_modulo_ou_perfis("fichas_execucao", PerfilUsuario.MASTER))
]


@router.get(
    "", response_model=list[FichaExecucaoResponse] | PaginaResponse[FichaExecucaoResponse],
    summary="Listar Fichas de Execução (somente MASTER)",
    description="Informe `pagina` pra paginar — sem isso, devolve a lista inteira.",
)
def listar_fichas(
    usuario: SomenteMaster, db: DbSession, polo_id: UUID | None = None,
    pagina: Annotated[int | None, Query(ge=1)] = None,
    tamanho_pagina: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[FichaExecucaoResponse] | PaginaResponse[FichaExecucaoResponse]:
    service = FichaExecucaoService(db)
    if pagina is None:
        fichas = service.listar(polo_id=polo_id)
        return [FichaExecucaoResponse.model_validate(f) for f in fichas]

    fichas, total = service.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, polo_id=polo_id)
    return PaginaResponse(
        itens=[FichaExecucaoResponse.model_validate(f) for f in fichas],
        total=total, pagina=pagina, tamanho_pagina=tamanho_pagina,
    )


@router.post(
    "", response_model=FichaExecucaoResponse, status_code=status.HTTP_201_CREATED,
    summary="Criar Ficha de Execução (somente MASTER)",
    description="Cria a ficha do período para o polo informado, já semeada com as listas fixas "
    "do modelo (metas, checklist de documentação, comparativo de atividades) em branco — "
    "edite com PATCH para preencher.",
)
def criar_ficha(body: FichaExecucaoCreateRequest, usuario: SomenteMaster, db: DbSession) -> FichaExecucaoResponse:
    criada = FichaExecucaoService(db).criar(
        polo_id=body.polo_id, periodo_referencia=body.periodo_referencia, data_documento=body.data_documento,
        criado_por_id=usuario.id,
    )
    return FichaExecucaoResponse.model_validate(criada)


@router.get("/{ficha_id}", response_model=FichaExecucaoResponse, summary="Detalhar Ficha de Execução (somente MASTER)")
def buscar_ficha(ficha_id: UUID, usuario: SomenteMaster, db: DbSession) -> FichaExecucaoResponse:
    ficha = FichaExecucaoService(db).buscar(ficha_id)
    if not ficha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ficha de Execução não encontrada.")
    return FichaExecucaoResponse.model_validate(ficha)


@router.patch("/{ficha_id}", response_model=FichaExecucaoResponse, summary="Editar Ficha de Execução (somente MASTER)")
def atualizar_ficha(
    ficha_id: UUID, body: FichaExecucaoUpdateRequest, usuario: SomenteMaster, db: DbSession
) -> FichaExecucaoResponse:
    campos = body.model_dump(exclude_unset=True)
    atualizada = FichaExecucaoService(db).atualizar(ficha_id, **campos)
    if not atualizada:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ficha de Execução não encontrada.")
    return FichaExecucaoResponse.model_validate(atualizada)


@router.get(
    "/{ficha_id}/exportar",
    summary="Exportar Ficha de Execução em .xlsx (somente MASTER)",
    description="Gera o arquivo preenchido no layout oficial do modelo, combinando os dados "
    "da parceria cadastrados no polo com os desta ficha.",
)
def exportar_ficha(
    ficha_id: UUID, usuario: SomenteMaster, db: DbSession, formato: Literal["xlsx", "pdf"] = "xlsx"
) -> Response:
    ficha = FichaExecucaoService(db).buscar(ficha_id)
    if not ficha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ficha de Execução não encontrada.")
    polo = PoloRepository(db).buscar_por_id(ficha.polo_id)
    cabecalho = texto_cabecalho(ConfiguracaoGeralRepository(db).buscar())

    buffer = exportar_ficha_execucao(ficha, polo, cabecalho_convenio=cabecalho)
    return resposta_relatorio(buffer, f"Ficha Tecnica de Execucao - {ficha.periodo_referencia}", "xlsx", formato)
