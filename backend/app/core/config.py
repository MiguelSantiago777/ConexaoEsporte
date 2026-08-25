"""
Configurações centrais da aplicação (padrão 12-factor, via variáveis de ambiente).

Banco de dados: PostgreSQL autogerenciado (não depende de Supabase — o
DATABASE_URL aponta para qualquer Postgres acessível, local ou remoto).
"""
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_JWT_SECRET_PADRAO = "dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database (PostgreSQL — próprio servidor, sem dependência de terceiros)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/conexao_esporte"

    # JWT
    JWT_SECRET_KEY: str = _JWT_SECRET_PADRAO
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173"

    PROJECT_NAME: str = "Conexão Esporte API"
    API_V1_PREFIX: str = "/api/v1"

    # Upload de documentos de beneficiários — armazenamento em disco local do
    # servidor (ver app/infrastructure/storage). Os arquivos nunca são servidos
    # por rota estática pública; o download passa sempre pela API autenticada.
    UPLOAD_DIR: str = "uploads/documentos"
    UPLOAD_MAX_SIZE_MB: int = 10

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @model_validator(mode="after")
    def _valida_segredo_em_producao(self) -> "Settings":
        # Trava de segurança: nunca deixar subir em produção com o segredo JWT
        # de desenvolvimento — todo token emitido seria forjável.
        if self.is_production and self.JWT_SECRET_KEY == _JWT_SECRET_PADRAO:
            raise RuntimeError(
                "JWT_SECRET_KEY não pode ser o valor padrão de desenvolvimento quando "
                "ENVIRONMENT=production. Gere um segredo forte (ex.: `openssl rand -hex 32`) "
                "e defina-o na variável de ambiente JWT_SECRET_KEY."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
