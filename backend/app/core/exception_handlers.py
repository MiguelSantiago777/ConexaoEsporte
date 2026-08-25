"""
Handlers globais de exceção — mapeiam toda exceção de domínio (e falhas de
banco não previstas) para o status HTTP correto, num único lugar. Nenhum
router precisa de try/except para isso: uma exceção de domínio levantada em
qualquer service sobe até aqui e vira a resposta certa automaticamente.

Referência dos códigos usados:
    400 Bad Request            — regra de negócio violada / dado inválido
    401 Unauthorized           — credenciais inválidas ou ausentes
    404 Not Found              — recurso inexistente
    409 Conflict                — já existe um recurso com esse valor único
    413 Payload Too Large       — upload maior que o limite
    415 Unsupported Media Type  — tipo de arquivo não permitido
    429 Too Many Requests       — rate limit (ver app/core/rate_limit.py)
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError

from app.domain.shared.exceptions import (
    AcessoNegado,
    ArquivoMuitoGrande,
    RecursoJaExiste,
    RecursoNaoEncontrado,
    RegraDeNegocioViolada,
    TipoArquivoNaoSuportado,
)

# SQLSTATE (código de erro do Postgres) -> (status HTTP, mensagem genérica).
# Nunca repassamos a mensagem original do banco ao cliente — ela pode
# conter nomes de tabela/coluna internos.
_PGCODE_PARA_RESPOSTA: dict[str, tuple[int, str]] = {
    "23505": (status.HTTP_409_CONFLICT, "Já existe um registro com esses dados."),
    "23503": (status.HTTP_400_BAD_REQUEST, "Referência a um recurso que não existe."),
    "23502": (status.HTTP_400_BAD_REQUEST, "Um campo obrigatório não foi informado."),
    "23514": (status.HTTP_400_BAD_REQUEST, "Um dos valores enviados não é permitido para esse campo."),
}


def registrar_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RecursoNaoEncontrado)
    async def _recurso_nao_encontrado(request: Request, exc: RecursoNaoEncontrado) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

    @app.exception_handler(RecursoJaExiste)
    async def _recurso_ja_existe(request: Request, exc: RecursoJaExiste) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})

    @app.exception_handler(ArquivoMuitoGrande)
    async def _arquivo_muito_grande(request: Request, exc: ArquivoMuitoGrande) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, content={"detail": str(exc)})

    @app.exception_handler(TipoArquivoNaoSuportado)
    async def _tipo_arquivo_nao_suportado(request: Request, exc: TipoArquivoNaoSuportado) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, content={"detail": str(exc)})

    # Precisa vir depois dos handlers de subclasses (ArquivoMuitoGrande,
    # TipoArquivoNaoSuportado) — o Starlette despacha pelo tipo exato antes
    # de considerar a classe-mãe, então a ordem de registro aqui não afeta
    # o resultado, mas mantemos assim por clareza de leitura.
    @app.exception_handler(RegraDeNegocioViolada)
    async def _regra_de_negocio_violada(request: Request, exc: RegraDeNegocioViolada) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

    @app.exception_handler(AcessoNegado)
    async def _acesso_negado(request: Request, exc: AcessoNegado) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(ValueError)
    async def _value_error(request: Request, exc: ValueError) -> JSONResponse:
        # Entidades de domínio (dataclasses em app/domain/**/entities.py)
        # validam suas próprias invariantes levantando ValueError puro.
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

    @app.exception_handler(IntegrityError)
    async def _integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
        pgcode = getattr(getattr(exc, "orig", None), "pgcode", None)
        status_code, mensagem = _PGCODE_PARA_RESPOSTA.get(
            pgcode, (status.HTTP_400_BAD_REQUEST, "Dados inválidos ou conflitantes.")
        )
        return JSONResponse(status_code=status_code, content={"detail": mensagem})

    @app.exception_handler(DataError)
    async def _data_error(request: Request, exc: DataError) -> JSONResponse:
        # Ex.: valor fora do enum do Postgres, string maior que o limite da
        # coluna — casos que a validação do Pydantic não cobriu.
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Dados inválidos."})
