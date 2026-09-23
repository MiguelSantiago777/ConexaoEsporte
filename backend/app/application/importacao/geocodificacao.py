"""Geocodificação de endereço via Nominatim (OpenStreetMap) — mesmo serviço
gratuito e sem chave de API usado no formulário individual de Polo (ver
`frontend/src/lib/geocoding.ts`, botão "Buscar endereço"). A importação em
massa de polos usa isso pra preencher Latitude/Longitude automaticamente a
partir do Endereço quando a planilha não traz as coordenadas prontas — sem
isso, o polo importado não apareceria no mapa do Dashboard.

O Nominatim é literal: um endereço como "Rua X, 90 - Bairro: Freguesia/RJ"
ou "Rua Y - esquina com R: Z" não é encontrado. Por isso o endereço é limpo
e buscado em tentativas do mais preciso (rua + número + bairro) pro mais
genérico (só o bairro/cidade) — nesse último caso o pino fica aproximado,
e quem chama recebe `aproximado=True` pra avisar o usuário."""
import re
import time
from dataclasses import dataclass

import httpx

_URL = "https://nominatim.openstreetmap.org/search"
# Nominatim exige um User-Agent identificando a aplicação (uso sem isso é
# bloqueado pela política de uso justo do serviço).
_HEADERS = {"User-Agent": "ConexaoEsporte-ImportacaoEmMassa/1.0"}

_ultima_chamada = 0.0
# A prévia e a confirmação da importação geocodificam os mesmos endereços em
# sequência — o cache evita repetir as chamadas (e a espera de 1s cada).
_cache: dict[str, "Coordenada | None"] = {}


@dataclass(frozen=True)
class Coordenada:
    latitude: float
    longitude: float
    aproximado: bool  # True = achado só pelo bairro/cidade, não pela rua


def _consultar(consulta: str) -> tuple[float, float] | None:
    global _ultima_chamada
    espera = 1.0 - (time.monotonic() - _ultima_chamada)
    if espera > 0:
        time.sleep(espera)
    try:
        resp = httpx.get(
            _URL, params={"format": "json", "limit": 1, "countrycodes": "br", "q": consulta},
            headers=_HEADERS, timeout=10.0,
        )
        resp.raise_for_status()
        resultados = resp.json()
    finally:
        _ultima_chamada = time.monotonic()
    if not resultados:
        return None
    return float(resultados[0]["lat"]), float(resultados[0]["lon"])


def consultas_candidatas(endereco: str) -> list[tuple[str, bool]]:
    """Monta as buscas a tentar, em ordem, cada uma com a flag de
    "aproximado". Ex.: "Rua Geovani de Castro, 90 - Bairro: Freguesia/RJ" vira
    "Rua Geovani de Castro, 90, Freguesia, RJ, Brasil" → "Rua Geovani de
    Castro, Freguesia, RJ" → "Freguesia, RJ" (aproximado)."""
    s = re.sub(r"\bCEP\b\s*[:-]?\s*[\d.-]*", " - ", endereco, flags=re.I)
    s = re.sub(r"\(\s*bairro:?\s*([^)]*)\)\.?", r" - \1 - ", s, flags=re.I)
    s = re.sub(r"[,\s-]*\bbairro:?\s*", " - ", s, flags=re.I)
    # "esquina com R: Z" é referência, não parte do endereço — some até o próximo separador.
    s = re.sub(r"\s*-?\s*esquina com.*?(?=\s+-\s+|$)", "", s, flags=re.I)
    s = re.sub(r"\bs/n\b,?", "", s, flags=re.I)
    s = re.sub(r"\bR:\s*", "Rua ", s)
    s = re.sub(r"\bAv\.?:?\s+", "Avenida ", s)
    s = re.sub(r"/\s*([A-Z]{2})\b", r", \1", s)
    s = re.sub(r"\.\s+(?=[A-ZÀ-Ú]{3,})", " - ", s)  # "...). CAMPOS DOS GOYTACAZES"
    partes = [p.strip(" ,.-") for p in re.split(r"\s+-(?:\s+-)*\s+", s) if p.strip(" ,.-")]
    if not partes:
        return []

    uf_encontrada = re.search(r",\s*([A-Z]{2})$", partes[-1])
    uf = uf_encontrada.group(1) if uf_encontrada else ""
    partes[-1] = re.sub(r",\s*[A-Z]{2}$", "", partes[-1]).strip()
    partes = [p for p in partes if p]
    if not partes:
        return []

    rua = re.sub(r",\s*(cobertura|loja|sala|apto?|bloco)\b.*", "", partes[0], flags=re.I)
    locais = partes[1:]
    sufixo = [uf] if uf else []
    rua_sem_numero = re.sub(r",\s*\d+\w*$", "", rua)

    candidatas = [
        (", ".join([rua, *locais, *sufixo, "Brasil"]), False),
        (", ".join([rua, *locais[-1:], *sufixo]), False),
        (", ".join([rua_sem_numero, *locais, *sufixo]), False),
    ]
    if locais:
        candidatas.append((", ".join([*locais, *sufixo]), True))
        if len(locais) > 1:
            candidatas.append((", ".join([locais[-1], *sufixo]), True))

    unicas: list[tuple[str, bool]] = []
    for consulta, aproximado in candidatas:
        if consulta and consulta not in (c for c, _ in unicas):
            unicas.append((consulta, aproximado))
    return unicas


def geocodificar(endereco: str) -> Coordenada | None:
    """Devolve a coordenada do endereço, ou None se nada foi encontrado.
    Respeita o limite de uso justo do Nominatim (~1 requisição/segundo) —
    importante numa importação em massa, que pode chamar isso várias vezes
    seguidas. Nunca levanta exceção: uma falha de geocodificação (endereço
    não encontrado, serviço fora do ar) não deve impedir a criação do polo,
    só deixa latitude/longitude em branco."""
    chave = endereco.strip().lower()
    if chave in _cache:
        return _cache[chave]
    resultado = None
    try:
        for consulta, aproximado in consultas_candidatas(endereco):
            achado = _consultar(consulta)
            if achado:
                resultado = Coordenada(achado[0], achado[1], aproximado)
                break
    except Exception:
        return None  # serviço fora do ar: não guarda no cache, pra tentar de novo depois
    _cache[chave] = resultado
    return resultado
