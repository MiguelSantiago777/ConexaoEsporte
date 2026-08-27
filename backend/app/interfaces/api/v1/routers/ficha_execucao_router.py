"""Rotas de Ficha de Execução (Ficha Técnica de Execução da Entidade).
Tag Swagger: 'Fichas de Execução'. Exclusivo do MASTER."""
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.application.ficha_execucao.service import FichaExecucaoService
from app.application.relatorios.ficha_execucao_export_service import exportar_ficha_execucao
from app.core.dependencies import DbSession, UsuarioAutenticado, require_perfis
from app.domain.enums import PerfilUsuario
from app.infrastructure.repositories.polo_repository import PoloRepository
from app.interfaces.api.v1.schemas.ficha_execucao_schemas import (
    FichaExecucaoCreateRequest,
    FichaExecucaoResponse,
    FichaExecucaoUpdateRequest,
)

router = APIRouter(prefix="/fichas-execucao", tags=["Fichas de Execução"])

SomenteMaster = Annotated[UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.MASTER))]


@router.get("", response_model=list[FichaExecucaoResponse], summary="Listar Fichas de Execução (somente MASTER)")
def listar_fichas(usuario: SomenteMaster, db: DbSession, polo_id: UUID | None = None) -> list[FichaExecucaoResponse]:
    fichas = FichaExecucaoService(db).listar(polo_id=polo_id)
    return [FichaExecucaoResponse.model_validate(f) for f in fichas]


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
def exportar_ficha(ficha_id: UUID, usuario: SomenteMaster, db: DbSession) -> Response:
    ficha = FichaExecucaoService(db).buscar(ficha_id)
    if not ficha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ficha de Execução não encontrada.")
    polo = PoloRepository(db).buscar_por_id(ficha.polo_id)

    buffer = exportar_ficha_execucao(ficha, polo)
    nome_arquivo = f"Ficha Tecnica de Execucao - {ficha.periodo_referencia}.xlsx"
    nome_ascii = nome_arquivo.encode("ascii", errors="replace").decode("ascii")
    content_disposition = f'attachment; filename="{nome_ascii}"; filename*=UTF-8\'\'{quote(nome_arquivo)}'
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": content_disposition},
    )
