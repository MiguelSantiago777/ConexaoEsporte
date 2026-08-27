# Conexão Esporte

Plataforma de gestão de projetos esportivos — cadastro e acompanhamento de **polos**, **modalidades**, **turmas** e **beneficiários**.

> **Regra de Ouro (nomenclatura):** a pessoa atendida pelo sistema é sempre **Beneficiário** — nunca "aluno". Isso vale para banco, DTOs, variáveis, endpoints, Swagger, telas e docs.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python + FastAPI (DDD + SOLID), SQLAlchemy 2 |
| Docs de API | Swagger UI / OpenAPI automático |
| Frontend | React (Vite + TypeScript) + TailwindCSS |
| Banco | PostgreSQL — servidor próprio, sem dependência de terceiros |
| Autenticação | JWT (Access + Refresh Token), esquema Bearer puro |
| Produção | Instalação nativa (systemd + Gunicorn/Uvicorn + Nginx) — ver [`DEPLOY.md`](./DEPLOY.md) |

## Perfis de acesso (RBAC)

- **MASTER** — acesso total: polos, modalidades, turmas, beneficiários e usuários; cadastra os gestores de cada polo.
- **GESTOR_POLO** — editor restrito **exclusivamente** ao seu polo; gerencia modalidades, turmas e beneficiários daquele polo; cadastra e vincula professores às turmas (aba "Professores").
- **PROFESSOR** — restrito às suas turmas: chamada de frequência diária e emissão de relatórios de aula.

Qualquer usuário autenticado pode trocar a própria senha na aba **"Alterar senha"**.

---

## Estrutura de pastas

```
conexao-esporte/
├── backend/                    # API FastAPI (DDD)
│   ├── app/
│   │   ├── core/               # config, security (JWT/bcrypt), rate_limit, database, dependencies (RBAC)
│   │   ├── domain/              # entidades puras + enums + regras de negócio
│   │   ├── application/         # casos de uso (services), 1 por contexto
│   │   ├── infrastructure/      # modelos ORM + repositórios + storage de documentos
│   │   └── interfaces/api/v1/   # routers (endpoints) + schemas (DTOs Pydantic)
│   ├── scripts/                 # criar_usuario_master.py — bootstrap do 1º MASTER em produção
│   ├── tests/                   # pytest: auth, RBAC, documentos, rate limiting, security headers
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── database/
│   ├── schema.sql               # tabelas, enums, FKs, índices (idempotente)
│   ├── rls_policies.sql         # NÃO USAR fora do Supabase — ver aviso no topo do arquivo
│   └── seed.sql                 # dados de teste (NÃO usar em produção)
├── deploy/                      # assets de produção: systemd, Nginx, gerador de segredos
├── DEPLOY.md                    # passo a passo completo de deploy num servidor Linux próprio
├── docker-compose.yml           # ambiente de desenvolvimento local (Postgres + API)
└── frontend/                    # React + Vite + TS + Tailwind
    └── src/
        ├── features/             # auth, polos, modalidades, turmas, beneficiarios, professores, frequencia, relatorios
        ├── components/           # ui/ (Button, Input, Select, Modal, Card...) + layout/
        ├── lib/                  # cliente axios (interceptors + refresh token)
        ├── routes/               # roteamento protegido por perfil
        └── types/                # interfaces TypeScript do domínio
```

---

## 1. Banco de dados (PostgreSQL)

Desenvolvimento local rápido via Docker (sobe só o Postgres com o schema já aplicado):

```bash
docker compose up -d db
```

Ou num Postgres já instalado localmente, aplique nesta ordem:

```bash
psql -h localhost -U postgres -d conexao_esporte -f database/schema.sql
psql -h localhost -U postgres -d conexao_esporte -f database/seed.sql   # só em dev
```

> **Não rode `database/rls_policies.sql`** fora de um projeto Supabase — ele depende do PostgREST para funcionar e, num Postgres comum, bloquearia o acesso do próprio backend. Leia o aviso no topo do arquivo.

### Usuários de teste do `seed.sql` (senha: `senha123`)

| Perfil | Email |
|--------|-------|
| MASTER | `master@conexaoesporte.org` |
| GESTOR_POLO | `gestor.zn@conexaoesporte.org` |
| PROFESSOR | `prof.joao@conexaoesporte.org` |

Em produção, não use o `seed.sql` — crie o primeiro MASTER com
`backend/scripts/criar_usuario_master.py` (ver [`DEPLOY.md`](./DEPLOY.md)).

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

(Em produção, com `ENVIRONMENT=production`, essas três rotas ficam desligadas — ver `DEPLOY.md`.)

**Como testar rotas protegidas no Swagger:**
1. Rode `POST /api/v1/auth/login` (campo `username` = email, `password` = senha).
2. Copie o `access_token` da resposta.
3. Clique em **Authorize** (cadeado no topo) e cole o token — o esquema é **Bearer puro** (`HTTPBearer`), só o token, sem client_id/client_secret.
4. As rotas protegidas passam a enviar o header `Authorization: Bearer <token>` automaticamente.

### Rodar os testes

```bash
cd backend
pytest -v
```

Cobre login JWT, isolamento entre polos (RBAC), regras de negócio dos
beneficiários, upload/download de documentos (incluindo sanitização de
nome de arquivo), troca de senha, cadastro de professor pelo gestor do
polo, validação de vínculo professor↔turma, rate limiting do login e
security headers.

### Via Docker (backend + banco, ambiente de dev)

```bash
docker compose up -d
```

Sobe Postgres + API já conectados. Para produção num servidor Linux
próprio (instalação nativa, sem Docker), siga o [`DEPLOY.md`](./DEPLOY.md).

---

## 3. Frontend (React + Vite)

```bash
cd frontend
npm install
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
| POST | `/api/v1/auth/login` | público (10 tentativas/min por IP) |
| POST | `/api/v1/auth/refresh` | público |
| GET | `/api/v1/auth/me` | autenticado |
| PATCH | `/api/v1/auth/senha` | autenticado (troca a própria senha) |
| GET/POST/PATCH | `/api/v1/polos` | MASTER — cada polo é sua própria entidade parceira (Termo de Fomento, CNPJ, representante legal ficam no cadastro do polo) |
| GET/POST | `/api/v1/modalidades` | MASTER, GESTOR_POLO |
| GET/POST/PATCH | `/api/v1/turmas` | MASTER, GESTOR_POLO |
| GET/POST/PATCH | `/api/v1/beneficiarios` | MASTER, GESTOR_POLO |
| POST/GET | `/api/v1/beneficiarios/{id}/matriculas` | MASTER, GESTOR_POLO — vínculo N:N com turmas; um beneficiário pode estar em várias modalidades ao mesmo tempo |
| PATCH | `/api/v1/beneficiarios/{id}/matriculas/{matricula_id}` | MASTER, GESTOR_POLO — encerra uma matrícula |
| POST/GET | `/api/v1/beneficiarios/{id}/documentos` | MASTER, GESTOR_POLO |
| GET | `/api/v1/beneficiarios/documentos/{id}/arquivo` | MASTER, GESTOR_POLO |
| POST | `/api/v1/frequencias/chamada` | PROFESSOR (+ MASTER/GESTOR) |
| POST | `/api/v1/relatorios-aula` | PROFESSOR |
| GET/POST/PATCH | `/api/v1/usuarios` | MASTER, GESTOR_POLO — cadastro de gestores/professores (aba "Professores" do front usa este endpoint filtrando por PROFESSOR); PATCH edita nome/telefone/carga horária (GESTOR_POLO só o próprio professor) |
| GET/POST/PATCH | `/api/v1/fichas-execucao` | MASTER — Ficha Técnica de Execução da Entidade (Portaria nº 102/2024), uma por polo e por período |
| GET | `/api/v1/fichas-execucao/{id}/exportar` | MASTER — exporta a ficha em `.xlsx`, no layout oficial do modelo |
| GET | `/api/v1/turmas/{id}/lista-presenca/exportar` | MASTER, GESTOR_POLO — exporta a Lista de Presença mensal da turma em `.xlsx` a partir da frequência já lançada |
| GET | `/api/v1/polos/{id}/grade-horaria/exportar` | MASTER, GESTOR_POLO — exporta a Grade Horária semanal do polo em `.docx` a partir das turmas já cadastradas |
| GET | `/api/v1/polos/{id}/planilha-nucleos/exportar` | MASTER, GESTOR_POLO — exporta a Planilha de Núcleos (RH e Beneficiário) do polo em `.xlsx` |
| GET/POST/PATCH | `/api/v1/entregas-materiais` | MASTER, GESTOR_POLO — registro de entregas de materiais/uniformes por polo |
| GET | `/api/v1/entregas-materiais/{id}/exportar` | MASTER, GESTOR_POLO — exporta o Termo de Entrega de Materiais em `.docx` |
| GET | `/api/v1/polos/{id}/termo-responsabilidade/exportar` | MASTER, GESTOR_POLO — exporta o Termo de Responsabilidade em `.docx` a partir dos dados do representante legal cadastrados no polo |

Todos os detalhes (DTOs, exemplos, códigos de resposta) estão no Swagger.

### Relatórios oficiais (exportação `.xlsx`/`.docx`)

O sistema gera os 6 documentos de prestação de contas exigidos pela
Portaria nº 102/2024, preenchidos automaticamente a partir dos dados já
cadastrados, no layout dos modelos oficiais:

- **Ficha Técnica de Execução da Entidade** — cadastre primeiro os dados da
  parceria (Termo de Fomento, CNPJ, representante legal) editando o **Polo**
  em **Polos** (cada polo é sua própria entidade parceira), depois crie uma
  Ficha por período em **Fichas de Execução** e use "Exportar .xlsx".
- **Lista de Presença** — na aba **Turmas**, seção "Exportar Lista de
  Presença": escolha a turma e o mês/ano; o arquivo sai preenchido com a
  grade de presença (P/A) a partir da frequência já lançada pelo professor.
- **Grade Horária** — na aba **Polos**, ícone de calendário na linha do
  polo: informe as horas de planejamento semanal e o arquivo sai
  preenchido com a carga horária (Segunda/Quarta/Sexta) de cada turma do
  polo, já somando o total semanal + planejamento.
- **Planilha de Núcleos — RH e Beneficiário** — na aba **Polos**, ícone de
  prancheta na linha do polo: o arquivo sai preenchido com a equipe (RH —
  gestor/professores do polo, com telefone e carga horária cadastrados em
  **Professores**) e os beneficiários ativos do polo (nome, idade,
  modalidade).
- **Termo de Entrega de Materiais** — aba **Entregas de Materiais**:
  registre a entrega (polo, data, itens) e use "Exportar .docx"; o
  coordenador do termo é copiado do responsável cadastrado no polo.
- **Termo de Responsabilidade** — na aba **Polos**, ícone de documento na
  linha do polo: gera o termo com os dados pessoais do representante legal
  (nome, RG, CPF, endereço) cadastrados na edição do polo.

Os arquivos-modelo ficam em `backend/app/infrastructure/templates/` — os
`.xlsx` são carregados com `openpyxl` e o `.docx` com `python-docx` (ambos
preservam 100% do layout/estilo originais).

---

## Arquitetura & decisões

- **DDD em camadas:** `domain` (entidades e regras puras, sem framework) → `application` (casos de uso) → `infrastructure` (ORM/repos) → `interfaces` (HTTP). As dependências apontam sempre para dentro.
- **RBAC no backend:** todas as regras de acesso por perfil/polo/turma são impostas em `app/core/dependencies.py` e nos services — a API nunca depende de RLS de banco para segurança (o arquivo `rls_policies.sql` é só um resquício de uma versão anterior pensada para Supabase, e não deve ser executado neste setup).
- **Nomenclatura "beneficiário"** aplicada de ponta a ponta e verificada por teste automatizado.
- **JWT self-managed:** access token curto + refresh token; o front renova automaticamente via interceptor do axios. Autenticação via **Bearer puro** (`HTTPBearer`), não OAuth2 completo.
- **Segurança:** senhas com bcrypt (custo 12, mínimo 8 caracteres), rate limiting em login/troca de senha, security headers em toda resposta, Swagger desligado em produção, usuário de banco dedicado sem privilégio de superusuário. Checklist completo em `DEPLOY.md`.
