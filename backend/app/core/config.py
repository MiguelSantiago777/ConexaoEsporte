"""
Configurações centrais da aplicação (padrão 12-factor, via variáveis de ambiente).

Banco de dados: PostgreSQL autogerenciado (não depende de Supabase — o
DATABASE_URL aponta para qualquer Postgres acessível, local ou remoto).
"""
from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_JWT_SECRET_PADRAO = "dev-secret-change-me"
_DATABASE_URL_PADRAO = "postgresql://postgres:postgres@localhost:5432/conexao_esporte"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database (PostgreSQL — próprio servidor, sem dependência de terceiros)
    DATABASE_URL: str = _DATABASE_URL_PADRAO

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

    # Fotos de evidência de aula (comprovam que a chamada de uma turma+data
    # realmente aconteceu) — mesmo esquema de armazenamento, pasta separada.
    UPLOAD_DIR_EVIDENCIAS: str = "uploads/evidencias"

    # Anexos do cadastro de professor (foto, documentos, contrato) e
    # repositório de Anexos Gerais por polo — mesmo esquema, pastas próprias.
    UPLOAD_DIR_USUARIOS: str = "uploads/usuarios"
    UPLOAD_DIR_ANEXOS_GERAIS: str = "uploads/anexos_gerais"

    # Estoque: nota fiscal/comprovante de uma Entrada, e comprovante de
    # recebimento no polo de uma Entrega de Materiais — mesmo esquema,
    # pastas próprias.
    UPLOAD_DIR_ESTOQUE: str = "uploads/estoque"
    UPLOAD_DIR_COMPROVANTES_ENTREGA: str = "uploads/comprovantes_entrega"

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
        # Mesma trava para a credencial do banco: o padrão usa o superusuário
        # `postgres` com a senha `postgres` — nunca pode subir assim em produção,
        # em nenhum host (o docker-compose.yml de desenvolvimento usa essas
        # mesmas credenciais apontando para o host "db", não "localhost" — por
        # isso a checagem é pelo usuário/senha, não pela URL inteira).
        credenciais = urlsplit(self.DATABASE_URL)
        if self.is_production and credenciais.username == "postgres" and credenciais.password == "postgres":
            raise RuntimeError(
                "DATABASE_URL não pode usar o superusuário padrão 'postgres' com a senha "
                "padrão 'postgres' quando ENVIRONMENT=production. Use um usuário de banco "
                "dedicado com senha forte (ex.: `bash deploy/gerar_segredos.sh`) e defina-o "
                "na variável de ambiente DATABASE_URL."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
