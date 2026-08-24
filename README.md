# Conexão Esporte

Plataforma de gestão de projetos esportivos — cadastro e acompanhamento de **polos**, **modalidades**, **turmas** e **beneficiários**.

> **Regra de Ouro (nomenclatura):** a pessoa atendida pelo sistema é sempre **Beneficiário** — nunca "aluno". Isso vale para banco, DTOs, variáveis, endpoints, Swagger, telas e docs.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python + FastAPI (DDD + SOLID), SQLAlchemy 2 |
| Docs de API | Swagger UI / OpenAPI automático |
| Frontend | React (Vite + TypeScript) + TailwindCSS |
| Banco & Auth | Supabase (PostgreSQL) + RLS |
| Autenticação | JWT (Access + Refresh Token) |

## Perfis de acesso (RBAC)

- **MASTER** — acesso total: polos, modalidades, turmas, beneficiários e usuários; cadastra os gestores de cada polo.
- **GESTOR_POLO** — editor restrito **exclusivamente** ao seu polo; gerencia modalidades, turmas e beneficiários daquele polo; cadastra e vincula professores às turmas.
- **PROFESSOR** — restrito às suas turmas: chamada de frequência diária e emissão de relatórios de aula.

---

## Estrutura de pastas

```
conexao-esporte/
├── backend/                    # API FastAPI (DDD)
│   ├── app/
│   │   ├── core/               # config, security (JWT/bcrypt), database, dependencies (RBAC)
│   │   ├── domain/             # entidades puras + enums + regras de negócio
│   │   ├── application/        # casos de uso (services), 1 por contexto
│   │   ├── infrastructure/     # modelos ORM + repositórios
│   │   └── interfaces/api/v1/  # routers (endpoints) + schemas (DTOs Pydantic)
│   ├── tests/                  # testes de auth + RBAC (pytest)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── database/                   # SQL do Supabase/PostgreSQL
│   ├── schema.sql              # tabelas, enums, FKs, índices
│   ├── rls_policies.sql        # Row Level Security (defesa extra)
│   └── seed.sql                # dados iniciais (usuários de teste)
└── frontend/                   # React + Vite + TS + Tailwind
    └── src/
        ├── features/           # auth, polos, modalidades, turmas, beneficiarios, frequencia, relatorios
        ├── components/         # ui/ (Button, Input, Card) + layout/
        ├── lib/                # cliente axios (interceptors + refresh token)
        ├── routes/             # roteamento protegido por perfil
        └── types/              # interfaces TypeScript do domínio
```

---

## 1. Banco de dados (Supabase / PostgreSQL)

No **SQL Editor** do Supabase (ou em um Postgres local), rode nesta ordem:

1. `database/schema.sql` — cria tabelas, enums e relacionamentos.
2. `database/rls_policies.sql` — habilita Row Level Security (opcional, mas recomendado).
3. `database/seed.sql` — insere dados de teste.

Pegue a **connection string** em *Project Settings → Database* e use no `.env` do backend.

### Usuários de teste (senha: `senha123`)

| Perfil | Email |
|--------|-------|
| MASTER | `master@conexaoesporte.org` |
| GESTOR_POLO | `gestor.zn@conexaoesporte.org` |
| PROFESSOR | `prof.joao@conexaoesporte.org` |

---

## 2. Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # ajuste DATABASE_URL e JWT_SECRET_KEY

uvicorn app.main:app --reload
```

A API sobe em **http://localhost:8000**.

### Swagger / OpenAPI

- **Swagger UI (interativo):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Schema JSON:** http://localhost:8000/openapi.json

**Como testar rotas protegidas no Swagger:**
1. Rode `POST /api/v1/auth/login` (campo `username` = email, `password` = senha).
2. Copie o `access_token` da resposta.
3. Clique em **Authorize** (cadeado no topo) e cole o token.
4. As rotas protegidas passam a enviar o header `Bearer` automaticamente.

### Rodar os testes

```bash
cd backend
pytest -v
```

Cobre login JWT, isolamento entre polos (RBAC) e regras de negócio dos beneficiários.

### Via Docker (backend)

```bash
cd backend
docker build -t conexao-esporte-api .
docker run -p 8000:8000 --env-file .env conexao-esporte-api
```

---

## 3. Frontend (React + Vite)

```bash
cd frontend
npm install
cp .env.example .env               # VITE_API_URL=/api/v1 (usa o proxy do Vite em dev)
npm run dev
```

App em **http://localhost:5173**. O Vite faz proxy de `/api` para `http://localhost:8000`, então rode o backend junto.

Build de produção:

```bash
npm run build      # gera dist/
npm run preview    # serve o build localmente
```

---

## Endpoints principais (API v1)

| Método | Rota | Perfis |
|--------|------|--------|
| POST | `/api/v1/auth/login` | público |
| POST | `/api/v1/auth/refresh` | público |
| GET | `/api/v1/auth/me` | autenticado |
| GET/POST | `/api/v1/polos` | MASTER (POST) |
| GET/POST | `/api/v1/modalidades` | MASTER, GESTOR_POLO |
| GET/POST/PATCH | `/api/v1/turmas` | MASTER, GESTOR_POLO |
| GET/POST/PATCH | `/api/v1/beneficiarios` | MASTER, GESTOR_POLO |
| POST | `/api/v1/frequencias/chamada` | PROFESSOR (+ MASTER/GESTOR) |
| POST | `/api/v1/relatorios-aula` | PROFESSOR |
| GET/POST | `/api/v1/usuarios` | MASTER, GESTOR_POLO |

Todos os detalhes (DTOs, exemplos, códigos de resposta) estão no Swagger.

---

## Arquitetura & decisões

- **DDD em camadas:** `domain` (entidades e regras puras, sem framework) → `application` (casos de uso) → `infrastructure` (ORM/repos) → `interfaces` (HTTP). As dependências apontam sempre para dentro.
- **RBAC em duas frentes:** o backend impõe as regras por polo/turma via dependências do FastAPI (`app/core/dependencies.py`); o RLS do Postgres é uma camada extra de defesa caso o front acesse o Supabase diretamente.
- **Nomenclatura "beneficiário"** aplicada de ponta a ponta e verificada por teste automatizado.
- **JWT self-managed:** access token curto + refresh token; o front renova automaticamente via interceptor do axios.
