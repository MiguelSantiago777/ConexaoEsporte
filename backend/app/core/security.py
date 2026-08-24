"""
Camada de segurança: hashing de senha (bcrypt) e emissão/validação de JWT
(Access Token + Refresh Token).

Usa a biblioteca `bcrypt` diretamente para evitar incompatibilidades de
versão entre passlib e bcrypt. Trunca a senha em 72 bytes (limite do bcrypt).
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import bcrypt
from jose import jwt

from app.core.config import settings

TokenType = Literal["access", "refresh"]

_BCRYPT_MAX_BYTES = 72


def _to_bytes(password: str) -> bytes:
    # bcrypt aceita no máximo 72 bytes; truncamos de forma segura.
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(_to_bytes(password), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bytes(plain_password), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_token(subject: str, extra_claims: dict[str, Any], token_type: TokenType) -> str:
    now = datetime.now(timezone.utc)
    if token_type == "access":
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": expire,
        **extra_claims,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(usuario_id: str, perfil: str, polo_id: str | None) -> str:
    return create_token(
        subject=usuario_id,
        extra_claims={"perfil": perfil, "polo_id": polo_id},
        token_type="access",
    )


def create_refresh_token(usuario_id: str) -> str:
    return create_token(subject=usuario_id, extra_claims={}, token_type="refresh")


def decode_token(token: str) -> dict[str, Any]:
    """Levanta jose.JWTError se o token for inválido/expirado."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
