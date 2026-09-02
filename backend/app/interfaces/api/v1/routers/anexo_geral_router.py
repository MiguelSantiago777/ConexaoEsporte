"""Rotas de Anexos Gerais — repositório livre de documentos por polo, não
ligados a um professor/beneficiário específico. Tag Swagger: 'Anexos Gerais'."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.application.anexo_geral.service import AnexoGeralService
from app.core.dependencies import DbSession, UsuarioAutenticado, assert_acesso_ao_polo, require_perfis
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.routers._arquivo_helper import resposta_download
from app.interfaces.api.v1.schemas.anexo_geral_schemas import AnexoGeralResponse, DocumentoConsolidadoResponse

router = APIRouter(prefix="/anexos-gerais", tags=["Anexos Gerais"])

MasterOuGestor = Annotated[
    UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO))
]


@router.get(
    "", response_model=list[AnexoGeralResponse],
    summary="Listar Anexos Gerais",
    description="MASTER vê os de qualquer polo (filtrando por `polo_id`). GESTOR_POLO vê apenas os do seu polo.",
)
def listar_anexos(usuario: MasterOuGestor, db: DbSession, polo_id: UUID | None = None) -> list[AnexoGeralResponse]:
    filtro_polo = usuario.polo_id if usuario.perfil == PerfilUsuario.GESTOR_POLO else polo_id
    anexos = AnexoGeralService(db).listar(polo_id=filtro_polo)
    return [AnexoGeralResponse.model_validate(a) for a in anexos]


@router.get(
    "/consolidado", response_model=list[DocumentoConsolidadoResponse],
    summary="Listar todos os documentos anexados (visão consolidada)",
    description="Reúne, numa única listagem somente leitura e ordenada do mais recente ao mais antigo: "
    "os Anexos Gerais enviados pelos polos/gestores de polo, as fotos de evidência de chamada e as "
    "observações de relatório de aula que os professores registram ao lançar a chamada. "
    "MASTER vê todos os polos (filtrando opcionalmente por `polo_id`). GESTOR_POLO vê apenas o seu.",
)
def listar_consolidado(
    usuario: MasterOuGestor, db: DbSession, polo_id: UUID | None = None
) -> list[DocumentoConsolidadoResponse]:
    filtro_polo = usuario.polo_id if usuario.perfil == PerfilUsuario.GESTOR_POLO else polo_id
    return AnexoGeralService(db).listar_consolidado(polo_id=filtro_polo)


@router.post(
    "", response_model=AnexoGeralResponse, status_code=status.HTTP_201_CREATED,
    summary="Enviar Anexo Geral",
    description="Envia um arquivo (multipart/form-data) para o repositório livre de documentos do polo. "
    "Tipos aceitos: PDF, JPG, PNG, WEBP — até 10MB.",
)
async def enviar_anexo(
    usuario: MasterOuGestor,
    db: DbSession,
    polo_id: UUID = Form(...),
    titulo: str = Form(...),
    arquivo: UploadFile = File(...),
) -> AnexoGeralResponse:
    assert_acesso_ao_polo(usuario, polo_id)
    criado = await AnexoGeralService(db).enviar(polo_id, titulo, arquivo, usuario.id)
    return AnexoGeralResponse.model_validate(criado)


@router.get(
    "/{anexo_id}/arquivo",
    summary="Baixar um Anexo Geral",
    description="Retorna o arquivo binário. Acesso restrito ao polo dono do anexo.",
)
def baixar_anexo(anexo_id: UUID, usuario: MasterOuGestor, db: DbSession) -> Response:
    service = AnexoGeralService(db)
    anexo = service.buscar(anexo_id)
    if not anexo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anexo não encontrado.")
    assert_acesso_ao_polo(usuario, anexo.polo_id)

    from app.infrastructure.storage.armazenamento_documentos import armazenamento_anexos_gerais

    with armazenamento_anexos_gerais.abrir(anexo.caminho_arquivo) as f:
        conteudo = f.read()
    return resposta_download(conteudo, anexo.content_type, anexo.nome_arquivo)


@router.delete("/{anexo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover um Anexo Geral")
def remover_anexo(anexo_id: UUID, usuario: MasterOuGestor, db: DbSession) -> None:
    service = AnexoGeralService(db)
    anexo = service.buscar(anexo_id)
    if not anexo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anexo não encontrado.")
    assert_acesso_ao_polo(usuario, anexo.polo_id)
    service.remover(anexo_id)
