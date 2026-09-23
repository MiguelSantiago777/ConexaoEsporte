"""Motor genérico de importação em massa — comum às 5 entidades importáveis.

Cada entidade fornece um `processar_linha(linha) -> str` (ou `(str, aviso)`) que resolve os
nomes/e-mails digitados na planilha pra IDs, roda a mesma validação do
cadastro individual (via `XxxService.validar`) e, se `confirmar=True`,
persiste de fato (via `XxxService.criar`) — devolvendo um resumo legível do
registro (ex.: o nome) pro relatório.

Por que não dá pra usar uma transação com savepoint por linha: todo
`XxxRepository.criar()` já chama `db.commit()` internamente (não há
autoflush na sessão — ver `app/core/database.py`), então um único
`db.commit()`/`db.rollback()` no fim do lote não é possível sem alterar 5
repositórios. Em vez disso, a prévia (`confirmar=False`) nunca chama
`criar()` — só `validar()`, que não toca o banco — e a confirmação chama
`criar()` linha a linha, cada uma commitando (ou revertendo, em erro) por
conta própria; uma linha com erro não afeta as demais.
"""
from collections.abc import Callable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.importacao.resultado import ResultadoImportacao
from app.core.exception_handlers import PGCODE_PARA_RESPOSTA
from app.domain.shared.exceptions import DomainError


def executar_importacao(
    db: Session,
    linhas: list[dict[str, str | None]],
    processar_linha: Callable[[dict[str, str | None]], str | tuple[str, str | None]],
    confirmar: bool,
) -> ResultadoImportacao:
    resultado = ResultadoImportacao(confirmado=confirmar)
    for numero, linha in enumerate(linhas, start=2):  # linha 1 é o cabeçalho
        try:
            retorno = processar_linha(linha)
            resumo, aviso = retorno if isinstance(retorno, tuple) else (retorno, None)
            resultado.adicionar_sucesso(numero, resumo, aviso)
        except (DomainError, ValueError) as e:
            db.rollback()
            resultado.adicionar_erro(numero, _resumo_bruto(linha), str(e))
        except IntegrityError as e:
            db.rollback()
            pgcode = getattr(getattr(e, "orig", None), "pgcode", None)
            _, mensagem = PGCODE_PARA_RESPOSTA.get(pgcode, (400, "Dados inválidos ou conflitantes."))
            resultado.adicionar_erro(numero, _resumo_bruto(linha), mensagem)
    return resultado


def _resumo_bruto(linha: dict[str, str | None]) -> str:
    """Fallback de identificação da linha quando ela falhou antes de
    conseguirmos montar a entidade (ex.: nome/FK não resolvido) — usa o
    primeiro valor não vazio da planilha, geralmente a coluna de nome."""
    primeiro_valor = next((str(v) for v in linha.values() if v not in (None, "")), "")
    return primeiro_valor[:80]
