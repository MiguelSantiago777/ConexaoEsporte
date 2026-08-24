"""Exceções de domínio — independentes de HTTP/FastAPI."""


class DomainError(Exception):
    """Erro base de regra de negócio."""


class RecursoNaoEncontrado(DomainError):
    pass


class RegraDeNegocioViolada(DomainError):
    pass


class AcessoNegado(DomainError):
    pass
