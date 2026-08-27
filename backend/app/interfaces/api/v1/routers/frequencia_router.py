"""Rotas de Frequência/Chamada. Tag Swagger: 'Frequência'. Foco no perfil PROFESSOR."""
from datetime import date
from typing import Annotated
from uuid import UUID
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.application.frequencia.evidencia_service import ChamadaEvidenciaService
from app.application.frequencia.service import FrequenciaService
from app.core.dependencies import (
    CurrentUser,
    DbSession,
    UsuarioAutenticado,
    assert_acesso_a_turma,
    require_perfis,
)
from app.domain.enums import PerfilUsuario
from app.infrastructure.storage.armazenamento_documentos import armazenamento_evidencias
from app.interfaces.api.v1.schemas.frequencia_schemas import (
    ChamadaCreateRequest,
    ChamadaEvidenciaResponse,
    FrequenciaResponse,
)

router = APIRouter(prefix="/frequencias", tags=["Frequência"])

# Chamada é feita pelo PROFESSOR; MASTER/GESTOR podem consultar/lançar em suporte.
QualquerPerfil = Annotated[
    UsuarioAutenticado,
    Depends(require_perfis(PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO, PerfilUsuario.PROFESSOR)),
]


@router.post(
    "/chamada",
    response_model=list[FrequenciaResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Lançar chamada diária (frequência dos beneficiários)",
    description="Registra a presença/ausência dos beneficiários de uma turma numa data. "
    "PROFESSOR só pode lançar chamada nas suas próprias turmas. Reenviar a mesma data "
    "atualiza os registros (idempotente por turma+beneficiário+data).",
)
def lancar_chamada(body: ChamadaCreateRequest, usuario: QualquerPerfil, db: DbSession) -> list[FrequenciaResponse]:
    assert_acesso_a_turma(usuario, db, body.turma_id)
    service = FrequenciaService(db)
    registros = service.registrar_chamada(
        turma_id=body.turma_id, data_ref=body.data,
        presencas=[(p.beneficiario_id, p.presente) for p in body.presencas],
        registrado_por_id=usuario.id,
    )
    return [FrequenciaResponse.model_validate(r) for r in registros]


@router.get(
    "/turma/{turma_id}",
    response_model=list[FrequenciaResponse],
    summary="Consultar chamada de uma turma por data",
)
def consultar_chamada(
    turma_id: UUID, data: date, usuario: QualquerPerfil, db: DbSession
) -> list[FrequenciaResponse]:
    assert_acesso_a_turma(usuario, db, turma_id)
    service = FrequenciaService(db)
    return [FrequenciaResponse.model_validate(r) for r in service.listar_chamada(turma_id, data)]


@router.post(
    "/evidencias",
    response_model=list[ChamadaEvidenciaResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Anexar fotos de evidência a uma chamada",
    description="Envia uma ou mais fotos (multipart/form-data) comprovando que a aula da turma, "
    "na data informada, realmente aconteceu. Tipos aceitos: JPG, PNG, WEBP, HEIC — até 10MB cada.",
)
async def enviar_evidencias(
    usuario: QualquerPerfil,
    db: DbSession,
    turma_id: Annotated[UUID, Form()],
    data: Annotated[date, Form()],
    arquivos: Annotated[list[UploadFile], File()],
) -> list[ChamadaEvidenciaResponse]:
    assert_acesso_a_turma(usuario, db, turma_id)
    if not arquivos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhuma foto enviada.")

    service = ChamadaEvidenciaService(db)
    criadas = [await service.enviar(turma_id, data, arquivo, usuario.id) for arquivo in arquivos]
    return [ChamadaEvidenciaResponse.model_validate(e) for e in criadas]


@router.get(
    "/evidencias",
    response_model=list[ChamadaEvidenciaResponse],
    summary="Listar fotos de evidência de uma chamada",
)
def listar_evidencias(
    turma_id: UUID, data: date, usuario: QualquerPerfil, db: DbSession
) -> list[ChamadaEvidenciaResponse]:
    assert_acesso_a_turma(usuario, db, turma_id)
    service = ChamadaEvidenciaService(db)
    return [ChamadaEvidenciaResponse.model_validate(e) for e in service.listar(turma_id, data)]


@router.get(
    "/evidencias/{evidencia_id}/arquivo",
    summary="Baixar/visualizar uma foto de evidência",
)
def baixar_evidencia(evidencia_id: UUID, usuario: QualquerPerfil, db: DbSession) -> Response:
    service = ChamadaEvidenciaService(db)
    evidencia = service.buscar(evidencia_id)
    if not evidencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto não encontrada.")
    assert_acesso_a_turma(usuario, db, evidencia.turma_id)

    with armazenamento_evidencias.abrir(evidencia.caminho_arquivo) as f:
        conteudo = f.read()

    nome_ascii = evidencia.nome_arquivo.encode("ascii", errors="replace").decode("ascii")
    content_disposition = f'inline; filename="{nome_ascii}"; filename*=UTF-8\'\'{quote(evidencia.nome_arquivo)}'
    return Response(
        content=conteudo,
        media_type=evidencia.content_type or "application/octet-stream",
        headers={"Content-Disposition": content_disposition},
    )
