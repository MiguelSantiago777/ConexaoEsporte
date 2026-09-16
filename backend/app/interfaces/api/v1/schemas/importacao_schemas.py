"""DTOs de resposta da importação em massa — comuns às 5 entidades
importáveis (beneficiário, turma, usuário, produto, polo)."""
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.application.importacao.resultado import ResultadoImportacao


class LinhaImportacaoResponse(BaseModel):
    linha: int
    status: str
    resumo: str
    erro: str | None = None


class ResultadoImportacaoResponse(BaseModel):
    confirmado: bool
    total: int
    sucesso: int
    falha: int
    linhas: list[LinhaImportacaoResponse]

    @classmethod
    def de_resultado(cls, resultado: "ResultadoImportacao") -> "ResultadoImportacaoResponse":
        return cls(
            confirmado=resultado.confirmado, total=resultado.total,
            sucesso=resultado.sucesso, falha=resultado.falha,
            linhas=[LinhaImportacaoResponse(linha=l.linha, status=l.status, resumo=l.resumo, erro=l.erro) for l in resultado.linhas],
        )
