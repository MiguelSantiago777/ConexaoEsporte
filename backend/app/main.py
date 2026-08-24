"""
Ponto de entrada da API Conexão Esporte (FastAPI).

Swagger/OpenAPI:
- Swagger UI interativo em   /docs
- ReDoc em                   /redoc
- JSON do schema OpenAPI em  /openapi.json

A autenticação Bearer JWT é reconhecida automaticamente pelo Swagger a partir
do OAuth2PasswordBearer (tokenUrl=/api/v1/auth/login). Basta clicar em
**Authorize** e colar o access token obtido no login.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.interfaces.api.v1.routers import (
    auth_router,
    beneficiario_router,
    frequencia_router,
    modalidade_router,
    polo_router,
    relatorio_aula_router,
    turma_router,
    usuario_router,
)

# Metadados das tags: aparecem organizados e descritos no topo do Swagger UI.
tags_metadata = [
    {"name": "Autenticação", "description": "Login, refresh de token e dados do usuário autenticado (JWT)."},
    {"name": "Usuários", "description": "Cadastro de funcionários: MASTER, GESTOR_POLO e PROFESSOR."},
    {"name": "Polos", "description": "Gestão de polos esportivos (exclusivo do MASTER)."},
    {"name": "Modalidades", "description": "Modalidades esportivas oferecidas (Futebol, Judô, etc.)."},
    {"name": "Turmas", "description": "Turmas por polo/modalidade e vínculo de professores."},
    {"name": "Beneficiários", "description": "Cadastro das pessoas atendidas pelo sistema (nomenclatura oficial)."},
    {"name": "Frequência", "description": "Chamada/presença diária dos beneficiários (perfil PROFESSOR)."},
    {"name": "Relatórios de Aula", "description": "Emissão e consulta de relatórios de aula (perfil PROFESSOR)."},
]

description = """
API do sistema **Conexão Esporte** — plataforma de gestão de projetos esportivos.

### Perfis de acesso (RBAC)
- **MASTER** — acesso total: polos, modalidades, turmas, beneficiários e usuários.
- **GESTOR_POLO** — editor restrito ao seu próprio polo.
- **PROFESSOR** — restrito às suas turmas: chamada de frequência e relatórios de aula.

> **Nomenclatura oficial:** a pessoa atendida é sempre **Beneficiário** — nunca "aluno".

### Como testar no Swagger
1. Faça login em `POST /api/v1/auth/login` (campo `username` = email).
2. Copie o `access_token` retornado.
3. Clique em **Authorize** (cadeado, topo direito) e cole o token.
"""

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=description,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={"name": "Equipe Conexão Esporte"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API = settings.API_V1_PREFIX
app.include_router(auth_router.router, prefix=API)
app.include_router(usuario_router.router, prefix=API)
app.include_router(polo_router.router, prefix=API)
app.include_router(modalidade_router.router, prefix=API)
app.include_router(turma_router.router, prefix=API)
app.include_router(beneficiario_router.router, prefix=API)
app.include_router(frequencia_router.router, prefix=API)
app.include_router(relatorio_aula_router.router, prefix=API)


@app.get("/", tags=["Health"], summary="Health check")
def health():
    return {"status": "ok", "servico": settings.PROJECT_NAME, "docs": "/docs"}
