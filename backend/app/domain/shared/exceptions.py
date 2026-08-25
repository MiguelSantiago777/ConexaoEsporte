"""
Exceções de domínio — independentes de HTTP/FastAPI.

O mapeamento para status HTTP fica centralizado em app/main.py (handlers
globais), nunca espalhado em cada router — assim nenhum endpoint escapa
sem o código de resposta correto por esquecimento de um try/except.
"""


class DomainError(Exception):
    """Erro base de regra de negócio."""


class RecursoNaoEncontrado(DomainError):
    """Mapeada para 404 Not Found."""


class RecursoJaExiste(DomainError):
    """Conflito com um recurso/campo único já existente. Mapeada para 409 Conflict."""


class RegraDeNegocioViolada(DomainError):
    """Mapeada para 400 Bad Request."""


class ArquivoMuitoGrande(RegraDeNegocioViolada):
    """Upload maior que o limite permitido. Mapeada para 413 Payload Too Large."""


class TipoArquivoNaoSuportado(RegraDeNegocioViolada):
    """Content-Type de upload fora da lista permitida. Mapeada para 415 Unsupported Media Type."""


class AcessoNegado(DomainError):
    """Credenciais inválidas/ausentes. Mapeada para 401 Unauthorized."""
