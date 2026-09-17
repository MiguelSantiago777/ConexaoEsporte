"""Rotas do Portal Transparência. Tag Swagger: 'Portal Transparência'.

`GET /transparencia/publico` e `GET /transparencia/publico/documentos/{id}/arquivo`
são **públicas** (sem autenticação) — pensadas pro órgão fiscalizador do
Termo de Fomento e qualquer visitante acessarem sem login. As demais rotas
(CRUD de Lançamentos Financeiros) são exclusivas do MASTER."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import Response

from app.application.transparencia.service import TransparenciaService
from app.core.dependencies import DbSession, UsuarioAutenticado, require_modulo_ou_perfis
from app.core.rate_limit import limiter
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.routers._arquivo_helper import resposta_download
from app.interfaces.api.v1.schemas.transparencia_schemas import (
    LancamentoFinanceiroCreateRequest,
    LancamentoFinanceiroResponse,
    PortalTransparenciaResponse,
)

router = APIRouter(prefix="/transparencia", tags=["Portal Transparência"])

SomenteMaster = Annotated[
    UsuarioAutenticado, Depends(require_modulo_ou_perfis("transparencia", PerfilUsuario.MASTER))
]


@router.get(
    "/publico", response_model=PortalTransparenciaResponse,
    summary="[Público] Resumo do Portal Transparência",
    description="Sem autenticação — execução física (polos, turmas, beneficiários atendidos, frequência), "
    "resumo financeiro (Lançamentos Financeiros do Termo de Fomento) e documentos marcados como públicos "
    "pelo MASTER. Limitado a 30 consultas por minuto por IP.",
)
@limiter.limit("30/minute")
def resumo_publico(request: Request, db: DbSession) -> PortalTransparenciaResponse:
    return TransparenciaService(db).resumo_publico()


@router.get(
    "/publico/documentos/{anexo_id}/arquivo",
    summary="[Público] Baixar um documento do Portal Transparência",
    description="Sem autenticação — só funciona para Anexos Gerais marcados como públicos pelo MASTER. "
    "Limitado a 30 downloads por minuto por IP.",
)
@limiter.limit("30/minute")
def baixar_documento_publico(request: Request, anexo_id: UUID, db: DbSession) -> Response:
    anexo = TransparenciaService(db).buscar_documento_publico(anexo_id)

    from app.infrastructure.storage.armazenamento_documentos import armazenamento_anexos_gerais

    with armazenamento_anexos_gerais.abrir(anexo.caminho_arquivo) as f:
        conteudo = f.read()
    return resposta_download(conteudo, anexo.content_type, anexo.nome_arquivo)


@router.get(
    "/lancamentos", response_model=list[LancamentoFinanceiroResponse],
    summary="Listar Lançamentos Financeiros (somente MASTER)",
    description="Informe `polo_id` pra filtrar por polo. Lançamentos sem polo são gerais do convênio.",
)
def listar_lancamentos(
    usuario: SomenteMaster, db: DbSession, polo_id: UUID | None = None
) -> list[LancamentoFinanceiroResponse]:
    lancamentos = TransparenciaService(db).listar_lancamentos(polo_id=polo_id)
    return [LancamentoFinanceiroResponse.model_validate(l) for l in lancamentos]


@router.post(
    "/lancamentos", response_model=LancamentoFinanceiroResponse, status_code=status.HTTP_201_CREATED,
    summary="Criar Lançamento Financeiro (somente MASTER)",
    description="Registra um valor repassado (REPASSE) ou executado (EXECUCAO) do Termo de Fomento, por "
    "categoria — passa a compor o resumo financeiro do Portal Transparência.",
)
def criar_lancamento(
    body: LancamentoFinanceiroCreateRequest, usuario: SomenteMaster, db: DbSession
) -> LancamentoFinanceiroResponse:
    criado = TransparenciaService(db).criar_lancamento(
        categoria=body.categoria, tipo=body.tipo, valor=body.valor, data_lancamento=body.data_lancamento,
        descricao=body.descricao, polo_id=body.polo_id, criado_por_id=usuario.id,
    )
    return LancamentoFinanceiroResponse.model_validate(criado)


@router.delete(
    "/lancamentos/{lancamento_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover Lançamento Financeiro (somente MASTER)",
)
def remover_lancamento(lancamento_id: UUID, usuario: SomenteMaster, db: DbSession) -> None:
    TransparenciaService(db).remover_lancamento(lancamento_id)
