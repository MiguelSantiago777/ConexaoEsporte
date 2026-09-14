"""
Envio de email do sistema via SMTP do Gmail autenticado por OAuth2
(XOAUTH2) — mesma arquitetura do app de referência em PHPMailer (um app
OAuth2 no Google Cloud com escopo "https://mail.google.com/", trocando um
refresh_token de longa duração por um access_token de curta duração a cada
envio), só que reimplementada em cima do smtplib da stdlib.

Para trocar de provedor (SES, SendGrid, Microsoft/Azure etc.), basta criar
outra classe com o mesmo método `enviar(destinatario, assunto, html,
texto_alternativo)` e trocar a instância `enviador_email` abaixo — igual ao
padrão já usado em app/infrastructure/storage para armazenamento.

Nunca importar `EnviadorEmailGmailOAuth2` diretamente em outra camada: toda
feature deve chamar `EmailService` (app/application/email/service.py), que
é quem sabe qual template usar para cada tipo de email do sistema.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Protocol

from app.core.config import settings
from app.infrastructure.email.oauth2_token import token_oauth2_google

logger = logging.getLogger(__name__)

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587


class EnviadorEmail(Protocol):
    def enviar(self, destinatario: str, assunto: str, html: str, texto_alternativo: str | None = None) -> None: ...


class EnviadorEmailGmailOAuth2:
    """Envia de verdade, autenticando no SMTP do Gmail via XOAUTH2."""

    def enviar(self, destinatario: str, assunto: str, html: str, texto_alternativo: str | None = None) -> None:
        mensagem = MIMEMultipart("alternative")
        mensagem["Subject"] = assunto
        mensagem["From"] = formataddr((settings.EMAIL_REMETENTE_NOME, settings.EMAIL_REMETENTE))
        mensagem["To"] = destinatario
        if texto_alternativo:
            mensagem.attach(MIMEText(texto_alternativo, "plain", "utf-8"))
        mensagem.attach(MIMEText(html, "html", "utf-8"))

        access_token = token_oauth2_google.obter_access_token()

        def _resposta_xoauth2(_desafio: bytes | None = None) -> str:
            return f"user={settings.EMAIL_REMETENTE}\x01auth=Bearer {access_token}\x01\x01"

        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.auth("XOAUTH2", _resposta_xoauth2, initial_response_ok=True)
            smtp.sendmail(settings.EMAIL_REMETENTE, [destinatario], mensagem.as_string())


class EnviadorEmailDesabilitado:
    """Usado quando as credenciais do Google OAuth2 não estão configuradas
    (dev/testes por padrão) — só registra no log em vez de tentar enviar,
    pra nunca quebrar o ambiente de quem ainda não configurou email."""

    def enviar(self, destinatario: str, assunto: str, html: str, texto_alternativo: str | None = None) -> None:
        logger.warning(
            "Email não enviado (credenciais do Google OAuth2 ausentes — ver .env.example): "
            "destinatário=%s, assunto=%r",
            destinatario, assunto,
        )


def _construir_enviador_email() -> EnviadorEmail:
    credenciais_completas = all([
        settings.GOOGLE_OAUTH_CLIENT_ID,
        settings.GOOGLE_OAUTH_CLIENT_SECRET,
        settings.GOOGLE_OAUTH_REFRESH_TOKEN,
        settings.EMAIL_REMETENTE,
    ])
    return EnviadorEmailGmailOAuth2() if credenciais_completas else EnviadorEmailDesabilitado()


enviador_email: EnviadorEmail = _construir_enviador_email()
