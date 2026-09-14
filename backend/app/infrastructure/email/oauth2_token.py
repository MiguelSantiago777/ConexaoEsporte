"""
Obtenção de access token do Google via OAuth2 (fluxo "refresh token"), para
autenticar o envio de email por SMTP com XOAUTH2 — mesmo mecanismo usado
pelo PHPMailer com a lib league/oauth2-client (ver get_oauth_token.php),
aqui reimplementado direto contra o endpoint de token do Google (sem
dependência de uma lib de terceiros): não precisamos do fluxo de
autorização completo (isso já foi feito uma vez, manualmente, para gerar o
refresh_token), só de trocar esse refresh_token por um access_token de
curta duração a cada envio.

Cache em memória por processo: o access token dura ~1h: evita bater no
Google a cada email. Como o deploy roda múltiplos workers do Gunicorn (ver
app/core/rate_limit.py para o mesmo caveat), cada worker mantém seu próprio
cache — sem problema aqui, só significa uma renovação extra por worker.
"""
import time

import httpx

from app.core.config import settings

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_MARGEM_EXPIRACAO_SEGUNDOS = 60  # renova um pouco antes do token realmente expirar


class TokenOAuth2Google:
    def __init__(self) -> None:
        self._access_token: str | None = None
        self._expira_em: float = 0.0

    def obter_access_token(self) -> str:
        agora = time.monotonic()
        if self._access_token and agora < self._expira_em:
            return self._access_token

        resposta = httpx.post(
            _TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                "refresh_token": settings.GOOGLE_OAUTH_REFRESH_TOKEN,
                "grant_type": "refresh_token",
            },
            timeout=10.0,
        )
        resposta.raise_for_status()
        dados = resposta.json()

        self._access_token = dados["access_token"]
        self._expira_em = agora + dados.get("expires_in", 3600) - _MARGEM_EXPIRACAO_SEGUNDOS
        return self._access_token


token_oauth2_google = TokenOAuth2Google()
