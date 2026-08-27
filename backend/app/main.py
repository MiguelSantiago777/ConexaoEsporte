"""
Ponto de entrada da API Conexão Esporte (FastAPI).

Swagger/OpenAPI:
- Swagger UI interativo em   /docs
- ReDoc em                   /redoc
- JSON do schema OpenAPI em  /openapi.json

A autenticação usa Bearer JWT puro (esquema HTTPBearer): no Swagger, basta
clicar em **Authorize** e colar o `access_token` obtido em POST /auth/login
— sem campos de client_id/client_secret do fluxo OAuth2 completo.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.exception_handlers import registrar_exception_handlers
from app.core.rate_limit import limiter
from app.interfaces.api.v1.routers import (
    auth_router,
    beneficiario_router,
    dashboard_router,
    entrega_material_router,
    ficha_execucao_router,
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
    {
        "name": "Polos",
        "description": "Gestão de polos esportivos (exclusivo do MASTER) — cada polo é sua própria "
        "entidade parceira, com os dados do Termo de Fomento (CNPJ, representante legal etc.).",
    },
    {"name": "Modalidades", "description": "Modalidades esportivas oferecidas (Futebol, Judô, etc.)."},
    {"name": "Turmas", "description": "Turmas por polo/modalidade e vínculo de professores."},
    {"name": "Beneficiários", "description": "Cadastro das pessoas atendidas pelo sistema (nomenclatura oficial)."},
    {"name": "Frequência", "description": "Chamada/presença diária dos beneficiários (perfil PROFESSOR)."},
    {"name": "Relatórios de Aula", "description": "Emissão e consulta de relatórios de aula (perfil PROFESSOR)."},
    {
        "name": "Fichas de Execução",
        "description": "Ficha Técnica de Execução da Entidade (Portaria nº 102/2024), uma por polo e por "
        "período, e sua exportação em .xlsx — exclusivo do MASTER.",
    },
    {
        "name": "Entregas de Materiais",
        "description": "Termo de Entrega de Materiais — registro e exportação em .docx por polo.",
    },
    {
        "name": "Relatórios Gerenciais",
        "description": "KPIs e séries para gráficos (frequência, beneficiários por modalidade, ranking de "
        "polos) por período — para acompanhamento do Gestor de Polo e visão geral do MASTER.",
    },
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

# Em produção, o Swagger/ReDoc/openapi.json ficam desligados por padrão para
# reduzir a superfície exposta publicamente (a API continua funcionando
# normalmente; só a documentação interativa fica indisponível).
_docs_habilitados = not settings.is_production

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=description,
    openapi_tags=tags_metadata,
    docs_url="/docs" if _docs_habilitados else None,
    redoc_url="/redoc" if _docs_habilitados else None,
    openapi_url="/openapi.json" if _docs_habilitados else None,
    contact={"name": "Equipe Conexão Esporte"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (login e troca de senha) — ver app/core/rate_limit.py.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mapeia toda exceção de domínio para o status HTTP correto — ver
# app/core/exception_handlers.py. Nenhum router precisa de try/except
# manual para isso.
registrar_exception_handlers(app)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Cabeçalhos de segurança padrão, aplicados a toda resposta.

    HSTS só faz sentido quando a conexão já é HTTPS (o Nginx da produção
    cuida disso — ver DEPLOY.md); em HTTP puro o header é inofensivo mas
    inútil, então fica de fora até a migração para domínio+TLS.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


API = settings.API_V1_PREFIX
app.include_router(auth_router.router, prefix=API)
app.include_router(usuario_router.router, prefix=API)
app.include_router(polo_router.router, prefix=API)
app.include_router(modalidade_router.router, prefix=API)
app.include_router(turma_router.router, prefix=API)
app.include_router(beneficiario_router.router, prefix=API)
app.include_router(frequencia_router.router, prefix=API)
app.include_router(relatorio_aula_router.router, prefix=API)
app.include_router(ficha_execucao_router.router, prefix=API)
app.include_router(entrega_material_router.router, prefix=API)
app.include_router(dashboard_router.router, prefix=API)


@app.get("/", tags=["Health"], summary="Health check")
def health():
    return {"status": "ok", "servico": settings.PROJECT_NAME, "docs": "/docs" if _docs_habilitados else None}
