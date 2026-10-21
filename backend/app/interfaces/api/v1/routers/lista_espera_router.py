"""
Rotas da LISTA DE ESPERA. Tag Swagger: 'Lista de Espera'.

`POST /lista-espera` e `GET /lista-espera/opcoes` são **públicas** (sem
autenticação) — pensadas pra rodar embutidas via iframe numa landing page
externa ao sistema. As demais rotas (listar pendentes, aceitar, excluir) exigem
login de MASTER ou GESTOR_POLO, igual ao resto da API.
"""
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.application.lista_espera.service import ListaEsperaService
from app.core.dependencies import CurrentUser, DbSession, UsuarioAutenticado, assert_acesso_ao_polo
from app.core.rate_limit import limiter
from app.domain.enums import PerfilUsuario
from app.infrastructure.storage.armazenamento_documentos import armazenamento_documentos
from app.interfaces.api.v1.schemas.lista_espera_schemas import (
    AceitarInscricaoRequest,
    InscricaoListaEsperaCreateRequest,
    InscricaoListaEsperaResponse,
    OpcaoResponse,
    OpcoesPublicasResponse,
)

router = APIRouter(prefix="/lista-espera", tags=["Lista de Espera"])


@router.get(
    "/opcoes",
    response_model=OpcoesPublicasResponse,
    summary="[Público] Polos e modalidades para o formulário de inscrição",
    description="Sem autenticação — usado pelo formulário público embutido na landing page. Devolve só "
    "id e nome, nenhum outro dado do polo/modalidade.",
)
def opcoes_publicas(db: DbSession) -> OpcoesPublicasResponse:
    polos, modalidades = ListaEsperaService(db).opcoes_publicas()
    return OpcoesPublicasResponse(
        polos=[OpcaoResponse(id=p.id, nome=p.nome) for p in polos if p.id],
        modalidades=[OpcaoResponse(id=m.id, nome=m.nome) for m in modalidades if m.id],
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=InscricaoListaEsperaResponse,
    summary="[Público] Inscrever-se na lista de espera",
    description="Sem autenticação — formulário público embutido na landing page. multipart/form-data: "
    "`dados` = JSON com os campos da inscrição (InscricaoListaEsperaCreateRequest) e, opcional, "
    "`documento_identidade` = foto/PDF da identidade do participante (PDF, JPG, PNG, WEBP — até 10MB). "
    "Envia um email de confirmação para o email informado. Limitado a 5 tentativas por minuto por IP.",
)
@limiter.limit("5/minute")
async def inscrever(
    request: Request, db: DbSession,
    dados: str = Form(...),
    documento_identidade: UploadFile | None = File(default=None),
) -> InscricaoListaEsperaResponse:
    try:
        body = InscricaoListaEsperaCreateRequest.model_validate_json(dados)
    except ValidationError as e:
        raise RequestValidationError(e.errors()) from None

    anexo = None
    if documento_identidade is not None:
        anexo = (
            documento_identidade.filename or "documento_identidade",
            documento_identidade.content_type,
            await documento_identidade.read(),
        )

    inscricao = ListaEsperaService(db).inscrever(
        nome_completo=body.nome_completo, data_nascimento=body.data_nascimento, documento=body.documento,
        nome_responsavel=body.nome_responsavel, documento_responsavel=body.documento_responsavel,
        telefone_whatsapp=body.telefone_whatsapp, email=body.email,
        bairro=body.bairro, cidade=body.cidade, modalidade_id=body.modalidade_id, polo_id=body.polo_id,
        como_conheceu=body.como_conheceu,
        tamanho_camisa=body.tamanho_camisa, tamanho_calcado=body.tamanho_calcado, turno=body.turno,
        documento_identidade=anexo,
    )
    return InscricaoListaEsperaResponse.model_validate(inscricao)


@router.get(
    "",
    response_model=list[InscricaoListaEsperaResponse],
    summary="Listar inscrições pendentes",
    description="MASTER vê todas (filtrando opcionalmente por `polo_id`). GESTOR_POLO vê só as do "
    "próprio polo. Só lista as ainda não aceitas.",
)
def listar_pendentes(
    usuario: CurrentUser, db: DbSession, polo_id: UUID | None = None,
) -> list[InscricaoListaEsperaResponse]:
    if usuario.perfil == PerfilUsuario.MASTER:
        filtro_polo = polo_id
    elif usuario.perfil == PerfilUsuario.GESTOR_POLO:
        filtro_polo = usuario.polo_id
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil sem permissão para executar esta ação.")

    itens = ListaEsperaService(db).listar_pendentes(polo_id=filtro_polo)
    return [InscricaoListaEsperaResponse.model_validate(i) for i in itens]


@router.post(
    "/{inscricao_id}/aceitar",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Aceitar inscrição: cria/reaproveita o Beneficiário e matricula na turma escolhida",
    description="A turma informada precisa ser do mesmo polo e modalidade da inscrição. Se já existir um "
    "Beneficiário com o mesmo documento (CPF), reaproveita o cadastro em vez de duplicar. Envia um email "
    "de boas-vindas para o email da inscrição.",
)
def aceitar(
    usuario: CurrentUser, db: DbSession, inscricao_id: UUID, body: AceitarInscricaoRequest,
) -> None:
    service = ListaEsperaService(db)
    inscricao = service.repo.buscar_por_id(inscricao_id)
    if not inscricao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição não encontrada.")
    if usuario.perfil != PerfilUsuario.MASTER:
        assert_acesso_ao_polo(usuario, inscricao.polo_id)

    service.aceitar(inscricao_id, turma_id=body.turma_id, usuario_id=usuario.id)


@router.get(
    "/{inscricao_id}/documento-identidade",
    summary="Baixar o documento de identidade anexado na inscrição",
    description="Retorna o arquivo binário (PDF/imagem). MASTER de qualquer polo; GESTOR_POLO só do próprio polo.",
)
def baixar_documento_identidade(usuario: CurrentUser, db: DbSession, inscricao_id: UUID) -> Response:
    inscricao = ListaEsperaService(db).repo.buscar_por_id(inscricao_id)
    if not inscricao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição não encontrada.")
    if usuario.perfil == PerfilUsuario.GESTOR_POLO:
        assert_acesso_ao_polo(usuario, inscricao.polo_id)
    elif usuario.perfil != PerfilUsuario.MASTER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil sem permissão para executar esta ação.")
    if not inscricao.documento_identidade_caminho:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição sem documento anexado.")

    with armazenamento_documentos.abrir(inscricao.documento_identidade_caminho) as f:
        conteudo = f.read()

    # Mesmo cuidado do download de documentos do beneficiário: o nome veio do
    # upload público, nunca interpolar bruto no header.
    nome_seguro = (inscricao.documento_identidade_nome_arquivo or "documento").replace("\\", "_").replace('"', "_")
    nome_ascii = nome_seguro.encode("ascii", errors="replace").decode("ascii")
    content_disposition = f'attachment; filename="{nome_ascii}"; filename*=UTF-8\'\'{quote(nome_seguro)}'
    return Response(
        content=conteudo,
        media_type=inscricao.documento_identidade_content_type or "application/octet-stream",
        headers={"Content-Disposition": content_disposition},
    )


@router.delete(
    "/{inscricao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir inscrição pendente",
    description="Remove definitivamente uma inscrição ainda não aceita (ex.: duplicada, desistência). "
    "MASTER exclui de qualquer polo; GESTOR_POLO só do próprio polo. Inscrições já aceitas não podem "
    "ser excluídas.",
)
def excluir(usuario: CurrentUser, db: DbSession, inscricao_id: UUID) -> None:
    service = ListaEsperaService(db)
    inscricao = service.repo.buscar_por_id(inscricao_id)
    if not inscricao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscrição não encontrada.")
    if usuario.perfil != PerfilUsuario.MASTER:
        assert_acesso_ao_polo(usuario, inscricao.polo_id)

    service.remover(inscricao_id)
