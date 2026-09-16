"""Helpers de parsing dos campos vindos da planilha — todo valor chega como
`str` (texto digitado), `date`/`datetime` (quando a célula é formatada como
data no Excel), `float`/`int` (célula numérica) ou `None` (célula vazia).
Reaproveitado por todos os `importacao_service.py` das 5 entidades."""
from datetime import date, datetime, time

from app.domain.shared.exceptions import RegraDeNegocioViolada


def texto(linha: dict, rotulo: str) -> str | None:
    valor = linha.get(rotulo)
    if valor is None:
        return None
    limpo = str(valor).strip()
    return limpo or None


def texto_obrigatorio(linha: dict, rotulo: str) -> str:
    valor = texto(linha, rotulo)
    if not valor:
        raise RegraDeNegocioViolada(f'Coluna "{rotulo}" é obrigatória.')
    return valor


def data(linha: dict, rotulo: str) -> date | None:
    valor = linha.get(rotulo)
    if valor is None or str(valor).strip() == "":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    bruto = str(valor).strip()
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(bruto, formato).date()
        except ValueError:
            continue
    raise RegraDeNegocioViolada(f'Coluna "{rotulo}": data inválida "{bruto}" — use o formato DD/MM/AAAA.')


def data_obrigatoria(linha: dict, rotulo: str) -> date:
    valor = data(linha, rotulo)
    if valor is None:
        raise RegraDeNegocioViolada(f'Coluna "{rotulo}" é obrigatória.')
    return valor


def hora(linha: dict, rotulo: str) -> str:
    """Devolve "HH:MM". O Excel entrega células formatadas como hora já como
    `time`/`datetime` — só texto digitado (ex.: "8:00") precisa de parsing."""
    valor = linha.get(rotulo)
    if valor is None or str(valor).strip() == "":
        raise RegraDeNegocioViolada(f'Coluna "{rotulo}" é obrigatória.')
    if isinstance(valor, datetime):
        return valor.strftime("%H:%M")
    if isinstance(valor, time):
        return valor.strftime("%H:%M")
    bruto = str(valor).strip()
    try:
        partes = bruto.split(":")
        h, m = int(partes[0]), int(partes[1])
        return f"{h:02d}:{m:02d}"
    except (ValueError, IndexError):
        raise RegraDeNegocioViolada(f'Coluna "{rotulo}": horário inválido "{bruto}" — use o formato HH:MM.')


def booleano(linha: dict, rotulo: str, padrao: bool = False) -> bool:
    valor = texto(linha, rotulo)
    if valor is None:
        return padrao
    return valor.lower() in ("sim", "s", "true", "1", "x")


def numero_inteiro(linha: dict, rotulo: str) -> int:
    valor = linha.get(rotulo)
    if valor is None or str(valor).strip() == "":
        raise RegraDeNegocioViolada(f'Coluna "{rotulo}" é obrigatória.')
    try:
        return int(float(str(valor).strip().replace(",", ".")))
    except ValueError:
        raise RegraDeNegocioViolada(f'Coluna "{rotulo}": valor numérico inválido "{valor}".')


def decimal(linha: dict, rotulo: str) -> float | None:
    valor = linha.get(rotulo)
    if valor is None or str(valor).strip() == "":
        return None
    try:
        return float(str(valor).strip().replace(",", "."))
    except ValueError:
        raise RegraDeNegocioViolada(f'Coluna "{rotulo}": valor numérico inválido "{valor}".')


def resolver_por_nome(
    rotulo: str, valor_digitado: str | None, opcoes: list[tuple], obrigatorio: bool = True
):
    """`opcoes`: lista de (id, nome_exibido) — ex.: polos, modalidades ou
    professores (por e-mail) já cadastrados. Casa por nome/e-mail ignorando
    caixa e espaços nas pontas. Levanta erro listando os valores válidos
    quando não encontra, já que ninguém digita UUID numa planilha."""
    if not valor_digitado or not valor_digitado.strip():
        if obrigatorio:
            raise RegraDeNegocioViolada(f'Coluna "{rotulo}" é obrigatória.')
        return None
    alvo = valor_digitado.strip().lower()
    for id_opcao, nome_opcao in opcoes:
        if nome_opcao.strip().lower() == alvo:
            return id_opcao
    disponiveis = ", ".join(sorted(nome for _, nome in opcoes)) or "nenhum cadastrado"
    raise RegraDeNegocioViolada(
        f'Coluna "{rotulo}": "{valor_digitado}" não encontrado. Valores disponíveis: {disponiveis}.'
    )
