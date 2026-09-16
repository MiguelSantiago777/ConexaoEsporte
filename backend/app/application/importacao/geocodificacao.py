"""Geocodificação de endereço via Nominatim (OpenStreetMap) — mesmo serviço
gratuito e sem chave de API usado no formulário individual de Polo (ver
`frontend/src/lib/geocoding.ts`, botão "Buscar endereço"). A importação em
massa de polos usa isso pra preencher Latitude/Longitude automaticamente a
partir do Endereço quando a planilha não traz as coordenadas prontas — sem
isso, o polo importado não apareceria no mapa do Dashboard."""
import time

import httpx

_URL = "https://nominatim.openstreetmap.org/search"
# Nominatim exige um User-Agent identificando a aplicação (uso sem isso é
# bloqueado pela política de uso justo do serviço).
_HEADERS = {"User-Agent": "ConexaoEsporte-ImportacaoEmMassa/1.0"}

_ultima_chamada = 0.0


def geocodificar(endereco: str) -> tuple[float, float] | None:
    """Devolve (latitude, longitude) ou None se o endereço não foi
    encontrado. Respeita o limite de uso justo do Nominatim (~1
    requisição/segundo) — importante numa importação em massa, que pode
    chamar isso várias vezes seguidas. Nunca levanta exceção: uma falha de
    geocodificação (endereço não encontrado, serviço fora do ar) não deve
    impedir a criação do polo, só deixa latitude/longitude em branco."""
    global _ultima_chamada
    try:
        espera = 1.0 - (time.monotonic() - _ultima_chamada)
        if espera > 0:
            time.sleep(espera)
        resp = httpx.get(
            _URL, params={"format": "json", "limit": 1, "q": endereco}, headers=_HEADERS, timeout=5.0,
        )
        _ultima_chamada = time.monotonic()
        resp.raise_for_status()
        resultados = resp.json()
        if not resultados:
            return None
        return float(resultados[0]["lat"]), float(resultados[0]["lon"])
    except Exception:
        return None
