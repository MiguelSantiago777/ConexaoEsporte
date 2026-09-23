"""
Rotas da LISTA DE ESPERA. Tag Swagger: 'Lista de Espera'.

`POST /lista-espera` e `GET /lista-espera/opcoes` são **públicas** (sem
autenticação) — pensadas pra rodar embutidas via iframe numa landing page
externa ao sistema. As demais rotas (listar pendentes, aceitar) exigem
login de MASTER ou GESTOR_POLO, igual ao resto da API.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from app.application.lista_espera.service import ListaEsperaService
from app.core.dependencies import CurrentUser, DbSession, UsuarioAutenticado, assert_acesso_ao_polo
from app.core.rate_limit import limiter
from app.domain.enums import PerfilUsuario
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
    description="Sem autenticação — formulário público embutido na landing page. Envia um email de "
    "confirmação para o email informado. Limitado a 5 tentativas por minuto por IP.",
)
@limiter.limit("5/minute")
def inscrever(
    request: Request, body: InscricaoListaEsperaCreateRequest, db: DbSession,
) -> InscricaoListaEsperaResponse:
    inscricao = ListaEsperaService(db).inscrever(
        nome_completo=body.nome_completo, data_nascimento=body.data_nascimento, documento=body.documento,
        nome_responsavel=body.nome_responsavel, documento_responsavel=body.documento_responsavel,
        telefone_whatsapp=body.telefone_whatsapp, email=body.email,
        bairro=body.bairro, cidade=body.cidade, modalidade_id=body.modalidade_id, polo_id=body.polo_id,
        como_conheceu=body.como_conheceu,
        tamanho_camisa=body.tamanho_camisa, tamanho_calcado=body.tamanho_calcado,
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
