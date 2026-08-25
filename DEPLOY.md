# Deploy em produção — servidor Linux próprio

Guia de instalação nativa (sem Docker): PostgreSQL, backend (FastAPI) e
frontend (React) rodando direto no servidor.

**Este servidor já tem outro app usando as portas 80, 443, 8000 e 5432, e
o domínio do Conexão Esporte ainda vai ser configurado depois.** O guia
abaixo já foi ajustado pra conviver com isso:

- **Postgres (5432):** reaproveitamos a instância que já está rodando —
  criamos só um banco e um usuário novos dentro dela. Não sobe um segundo
  Postgres.
- **Backend Uvicorn:** porta `8010` em vez de `8000` (só em `127.0.0.1`,
  nunca exposta — o número em si não importa muito, só não pode colidir).
- **Frontend/Nginx (80/443):** como ainda não tem domínio, o site sobe
  temporariamente na porta `8080` (`http://SEU_IP:8080`). Quando o domínio
  estiver pronto, você adiciona um novo `server_name` no Nginx apontando
  pra ele nas portas 80/443 normais — isso **não conflita** com o outro
  app, porque o Nginx roteia por nome de domínio (Host header), não por
  porta; múltiplos sites dividem a mesma porta 443 numa boa. O passo 5 já
  explica os dois cenários.

Comandos testados para Ubuntu/Debian (`apt`); em outra distro troque o
gerenciador de pacotes, o resto é igual.

---

## 0. Visão geral

```
Agora (sem domínio):
Internet ──8080──> Nginx ──┬─ arquivos estáticos (frontend/dist)
                            └─ /api/* ──> Uvicorn (127.0.0.1:8010) ──> PostgreSQL (127.0.0.1:5432, banco separado)

Depois (com domínio):
Internet ──443──> Nginx (server_name esporte.seudominio.com.br) ──> mesma coisa
                   (o outro app continua respondendo no server_name dele, na mesma porta 443)
```

- Postgres e o backend só escutam em `127.0.0.1` — nunca ficam expostos
  diretamente à internet, só o Nginx.
- O backend roda como serviço systemd, sem `--reload`, com um usuário
  Linux dedicado sem privilégios.

Antes de tudo, confirme o que realmente está em cada porta (só pra não
supor errado):

```bash
sudo ss -tlnp | grep -E ':80 |:443 |:8000 |:5432 '
```

Se **5432** não aparecer como Postgres (`postgres`/`postmaster` no
processo), ou se **8080** também já estiver ocupada, troque os números
usados neste guia por outros livres — a lógica é a mesma.

---

## 1. Preparar o servidor

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw

# Firewall: abre só o necessário. 8080 é temporário, até trocar pra 443
# com domínio (passo 5) — depois disso, pode fechar a 8080 de novo.
sudo ufw allow OpenSSH
sudo ufw allow 8080/tcp
sudo ufw status
```

> Não mexa nas regras de 80/443 aqui — elas já devem estar liberadas pelo
> outro app. Quando migrar o Conexão Esporte pra elas (passo 5), não
> precisa abrir de novo.

Crie um usuário de sistema dedicado para rodar a aplicação (não root):

```bash
sudo adduser --system --group --home /opt/conexao-esporte conexao
sudo mkdir -p /opt/conexao-esporte
sudo chown conexao:conexao /opt/conexao-esporte
```

---

## 2. PostgreSQL (reaproveitando a instância existente)

Confirme que o Postgres já instalado está rodando e escutando em
`127.0.0.1`/`localhost` (não precisa mudar nada se já for assim, é o
padrão do pacote do Ubuntu/Debian):

```bash
sudo systemctl status postgresql
sudo grep listen_addresses /etc/postgresql/*/main/postgresql.conf
```

Crie o banco e um **usuário de aplicação dedicado só do Conexão Esporte**
dentro dessa mesma instância (nunca use o superusuário `postgres`, nem o
usuário/banco do outro app, na `DATABASE_URL`). O Postgres não tem um
"gerar senha pra mim" embutido — mas o script abaixo gera uma senha
aleatória forte e já te devolve o SQL e as linhas do `.env` prontos pra
colar, sem você ter que digitar nada à mão:

```bash
bash deploy/gerar_segredos.sh
```

Ele imprime algo como:

```
Senha do usuário do banco (conexao_esporte_app): Kx8pQ2...
JWT_SECRET_KEY:                                  9f2a7c...

1) Cole isto no 'sudo -u postgres psql':
CREATE DATABASE conexao_esporte;
CREATE USER conexao_esporte_app WITH PASSWORD 'Kx8pQ2...';
...

2) Cole isto no backend/.env:
DATABASE_URL=postgresql://conexao_esporte_app:Kx8pQ2...@localhost:5432/conexao_esporte
JWT_SECRET_KEY=9f2a7c...
```

Copie o bloco 1 e cole dentro de `sudo -u postgres psql` (abra com esse
comando, cole o bloco, `Enter`, depois `\q` pra sair). Guarde o bloco 2 —
ele vai para o `.env` no passo 3, junto com a `JWT_SECRET_KEY` que o mesmo
script já gerou.

> Sem o script, o equivalente manual é `openssl rand -base64 24` (senha do
> banco) e `openssl rand -hex 32` (`JWT_SECRET_KEY`) — copie a saída de
> cada comando pros lugares certos. Se o servidor não tiver `openssl`
> instalado, `python3 -c "import secrets; print(secrets.token_urlsafe(24))"`
> funciona igual (o Python já é obrigatório pro backend).

Esse usuário só enxerga o banco `conexao_esporte`; ele não tem acesso ao
banco do outro app, e vice-versa.

Aplique o schema (rode como o novo usuário, para que ele já seja o *owner*
das tabelas):

```bash
PGPASSWORD='SUA_SENHA' psql -h localhost -U conexao_esporte_app -d conexao_esporte \
  -f database/schema.sql
```

> **Não rode `database/seed.sql` em produção.** Ele cria usuários de teste
> com a senha conhecida `senha123`. O primeiro usuário MASTER real é criado
> no passo 3 com o script `criar_usuario_master.py`.
>
> **Não rode `database/rls_policies.sql`.** Aquelas políticas dependem do
> PostgREST do Supabase (que não existe aqui) e bloqueariam o acesso do
> próprio backend. O controle de acesso por perfil/polo já é feito na API.

---

## 3. Backend (FastAPI)

Primeiro, coloque o código em `/opt/conexao-esporte` (a pasta já criada e
com dono `conexao` no passo 1). Duas formas — use a que preferir:

**Via `git clone`** (se o repositório estiver num Git remoto):

```bash
sudo apt install -y python3.12-venv build-essential libpq-dev git
sudo -u conexao git clone <URL_DO_SEU_REPOSITORIO_GIT> /opt/conexao-esporte-src
sudo rsync -a --delete /opt/conexao-esporte-src/ /opt/conexao-esporte/
```

**Via WinSCP + PuTTY (zip, sem Git)** — ver seção **3.1** logo abaixo para o
passo a passo completo, incluindo como gerar o zip no Windows.

Depois de qualquer um dos dois, com o código já em `/opt/conexao-esporte`:

```bash
sudo apt install -y python3.12-venv build-essential libpq-dev
cd /opt/conexao-esporte/backend

sudo -u conexao python3 -m venv .venv
sudo -u conexao .venv/bin/pip install --upgrade pip
sudo -u conexao .venv/bin/pip install -r requirements.txt
```

### 3.1 Sem Git — subindo o código via WinSCP + PuTTY

No **Windows**, gere um zip do projeto sem o lixo que não precisa ir pro
servidor (`node_modules`, `.venv`, `__pycache__`, etc. — tudo isso é
reinstalado/gerado no servidor, e binários compilados no Windows não
funcionam no Linux mesmo). No PowerShell, na pasta onde fica o projeto:

```powershell
$src = "C:\ConexaoEsporte\conexao-esporte"
$tmp = "$env:TEMP\conexao-esporte-deploy"
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
robocopy $src $tmp /E /XD node_modules .venv venv __pycache__ dist .vite uploads .git .pytest_cache /XF .env
Compress-Archive -Path "$tmp\*" -DestinationPath "$env:USERPROFILE\Desktop\conexao-esporte.zip" -Force
```

(O robocopy imprime uma tabela-resumo e pode "parecer" ter dado erro — isso
é normal, ele só reporta quantos arquivos copiou. O que importa é o
`.zip` ter sido criado na Área de Trabalho no final.)

No **WinSCP**: conecte com seu usuário SSH normal (o mesmo do PuTTY) e
arraste o `conexao-esporte.zip` para a **home dele no servidor**
(`/home/seu_usuario/`) — nunca direto pra `/opt/...`, porque seu usuário
SSH não tem permissão de escrita lá (só `sudo` tem).

No **PuTTY** (SSH), extraia e mova pro lugar certo com `sudo`:

```bash
sudo apt install -y unzip
sudo mkdir -p /opt/conexao-esporte
sudo unzip -q ~/conexao-esporte.zip -d /opt/conexao-esporte
sudo chown -R conexao:conexao /opt/conexao-esporte
rm ~/conexao-esporte.zip
```

Confira que ficou com a cara certa antes de seguir para o resto do passo 3:

```bash
ls /opt/conexao-esporte
# deve mostrar: backend  frontend  database  deploy  DEPLOY.md  README.md ...
```

Crie o `.env` de produção a partir do exemplo:

```bash
sudo -u conexao cp .env.example .env
sudo -u conexao nano .env
```

Preencha `DATABASE_URL` e `JWT_SECRET_KEY` com o bloco 2 que o
`gerar_segredos.sh` do passo 2 já te deu, e complete o resto:

```dotenv
DATABASE_URL=postgresql://conexao_esporte_app:SUA_SENHA_GERADA@localhost:5432/conexao_esporte
JWT_SECRET_KEY=sua_jwt_secret_gerada
ENVIRONMENT=production
# Enquanto não tem domínio, libere a porta temporária; troque para
# https://esporte.seudominio.com.br assim que o domínio estiver pronto.
CORS_ORIGINS=http://SEU_IP:8080
UPLOAD_DIR=/opt/conexao-esporte/backend/uploads/documentos
```

`ENVIRONMENT=production` faz duas coisas automaticamente: a aplicação se
recusa a subir se `JWT_SECRET_KEY` ainda for o valor padrão de
desenvolvimento, e o Swagger/ReDoc (`/docs`, `/redoc`, `/openapi.json`)
ficam desligados.

Crie o primeiro usuário MASTER:

```bash
cd /opt/conexao-esporte/backend
sudo -u conexao .venv/bin/python scripts/criar_usuario_master.py
```

Teste manualmente antes de criar o serviço (porta `8010`, para não colidir
com o `8000` do outro app). Em produção quem sobe a aplicação é o
**Gunicorn**, usando o Uvicorn só como "worker class" (Gunicorn gerencia os
processos — reinicia worker que travar, faz reload gradual sem derrubar
conexão — e o Uvicorn é quem entende async/FastAPI de fato):

```bash
sudo -u conexao .venv/bin/gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker --workers 2 --bind 127.0.0.1:8010
# noutro terminal:
curl http://127.0.0.1:8010/
# Ctrl+C para parar depois de confirmar que respondeu {"status":"ok",...}
```

> Mesmo já tendo Gunicorn instalado no servidor, ele entra como dependência
> do `requirements.txt` (dentro do venv deste projeto) — assim a versão
> fica isolada e não depende do que outro app já tem instalado
> globalmente, evitando que uma atualização de um quebre o outro.

Instale como serviço systemd (o arquivo em `deploy/` já usa Gunicorn +
Uvicorn workers na porta `8010`):

```bash
sudo cp deploy/conexao-esporte-api.service /etc/systemd/system/
# Só precisa editar se você colocou o código em outro caminho que não /opt/conexao-esporte
sudo nano /etc/systemd/system/conexao-esporte-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now conexao-esporte-api
sudo systemctl status conexao-esporte-api
```

Logs em tempo real:

```bash
sudo journalctl -u conexao-esporte-api -f
```

---

## 4. Frontend (React/Vite)

Build local (na sua máquina ou direto no servidor — precisa de Node 20+):

```bash
cd frontend
npm install
npm run build   # gera frontend/dist
```

Como o Nginx serve o frontend e a API na **mesma origem** (via proxy em
`/api/`), não é preciso configurar `VITE_API_URL` — o `api.ts` já usa o
caminho relativo `/api/v1` por padrão. Isso continua valendo tanto na
porta temporária `8080` quanto depois no domínio final.

Copie o resultado para onde o Nginx vai servir:

```bash
sudo mkdir -p /opt/conexao-esporte/frontend
sudo cp -r dist/* /opt/conexao-esporte/frontend/dist/
```

---

## 5. Nginx

### 5.1 Agora — sem domínio, porta 8080

```bash
# Se o outro app já usa Nginx, ótimo, é o mesmo pacote — só adiciona um
# novo arquivo de site. Se o outro app usa outra coisa (Apache etc.), o
# apt install abaixo instala o Nginx do zero, sem mexer no que já existe.
sudo apt install -y nginx

sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/conexao-esporte
sudo ln -s /etc/nginx/sites-available/conexao-esporte /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Não mexa em `sites-enabled/default` nem nos arquivos do outro app — o
bloco novo escuta só na `8080`, então não briga com o que já existe.

Acesse `http://SEU_IP:8080` e faça login com o usuário MASTER criado no
passo 3.

### 5.2 Depois — quando o domínio estiver pronto

Aponte o DNS (registro `A`) do domínio/subdomínio escolhido
(ex.: `esporte.seudominio.com.br`) para o IP deste servidor. Depois:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo nano /etc/nginx/sites-available/conexao-esporte
```

Troque `listen 8080;` / `listen [::]:8080;` por `listen 80;` /
`listen [::]:80;`, e `server_name _;` pelo domínio real
(`server_name esporte.seudominio.com.br;`). Depois:

```bash
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d esporte.seudominio.com.br
```

O certbot edita o server block automaticamente para servir em 443 com
HTTPS e redirecionar HTTP→HTTPS; a renovação automática já vem
configurada (`systemctl status certbot.timer`). Isso convive numa boa com
o outro app já rodando em 80/443 — cada um responde pelo seu próprio
`server_name`.

Depois disso, atualize também:

```bash
# backend/.env
CORS_ORIGINS=https://esporte.seudominio.com.br
```

e reinicie o serviço (`sudo systemctl restart conexao-esporte-api`). Pode
fechar a porta 8080 no firewall (`sudo ufw delete allow 8080/tcp`).

---

## 6. Checklist de segurança

- [x] Senhas com hash bcrypt (custo 12) — já implementado no backend.
- [x] Senha mínima de 8 caracteres na criação/troca de senha (`usuario_schemas.py`, `auth_schemas.py`).
- [x] `JWT_SECRET_KEY` forte e exclusivo de produção (`openssl rand -hex 32`); a app recusa subir com o valor padrão quando `ENVIRONMENT=production`.
- [x] Autenticação via Bearer JWT puro (`HTTPBearer`) em todas as rotas protegidas.
- [x] Rate limiting em `/auth/login` e `PATCH /auth/senha` (10 tentativas/minuto por IP) — ver `app/core/rate_limit.py`.
- [x] Security headers em toda resposta (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Strict-Transport-Security` quando HTTPS) — ver middleware em `app/main.py`.
- [x] `client_max_body_size` no Nginx, alinhado ao limite de upload do backend (`deploy/nginx.conf.example`).
- [x] Validação de que `professor_id` vinculado a uma turma é de fato um PROFESSOR do mesmo polo (evita vazamento de acesso entre polos).
- [x] Nome de arquivo de documentos sanitizado antes de entrar no header `Content-Disposition` no download.
- [x] Postgres e backend acessíveis só via `127.0.0.1` — nunca exponha as portas 5432/8010 no firewall.
- [x] Usuário de banco dedicado (`conexao_esporte_app`), sem privilégio de superusuário, isolado do banco/usuário do outro app.
- [x] `CORS_ORIGINS` restrito à origem real do frontend (porta temporária agora, domínio HTTPS depois).
- [x] Swagger/ReDoc desligados em produção (`ENVIRONMENT=production`).
- [x] Backend rodando como usuário Linux sem privilégios (`conexao`), nunca root.
- [x] Aba "Alterar senha" disponível para todo usuário logado trocar a própria senha.
- [ ] Migrar para HTTPS assim que o domínio estiver pronto (passo 5.2) — não deixe rodando só em HTTP por muito tempo, principalmente com dados de menores de idade envolvidos.
- [ ] Configure backups periódicos do banco (passo 7).
- [ ] Troque a senha do usuário MASTER se em algum momento você rodou `seed.sql` para testar.
- [ ] (Melhoria futura, não bloqueante) Refresh tokens não são revogados/rotacionados no logout ou troca de senha — um refresh token válido continua ativo até sua expiração natural (7 dias) mesmo depois de trocar a senha. Para revogação imediata, precisaria de uma tabela de tokens emitidos/revogados no banco.

---

## 7. Backup do banco

Cron diário simples com `pg_dump` (funciona igual reaproveitando a
instância existente — só faz backup do banco `conexao_esporte`, não mexe
no banco do outro app):

```bash
sudo -u postgres mkdir -p /var/backups/conexao_esporte
sudo crontab -u postgres -e
```

Adicione:

```
0 3 * * * pg_dump -Fc conexao_esporte > /var/backups/conexao_esporte/$(date +\%F).dump
0 4 * * * find /var/backups/conexao_esporte -mtime +14 -delete
```

Restaurar, se precisar:

```bash
pg_restore -d conexao_esporte --clean --if-exists /var/backups/conexao_esporte/2026-08-25.dump
```

Copie os backups para fora do servidor periodicamente (outro host, storage
externo) — backup que mora só na mesma máquina não protege contra falha de
disco.

---

## 8. Atualizando depois do primeiro deploy

Primeiro, atualize o código em `/opt/conexao-esporte`:

**Via Git:**

```bash
cd /opt/conexao-esporte
sudo -u conexao git pull
```

**Via WinSCP + PuTTY (zip)** — gere um novo zip como na seção 3.1, suba
pra sua home no servidor via WinSCP e, no PuTTY:

```bash
sudo unzip -oq ~/conexao-esporte.zip -d /opt/conexao-esporte   # -o sobrescreve sem perguntar
sudo chown -R conexao:conexao /opt/conexao-esporte
rm ~/conexao-esporte.zip
```

> O `unzip -o` sobrescreve os arquivos do projeto, mas não apaga o `.env`
> nem a pasta `uploads/` se eles não estiverem dentro do zip (e não estão,
> já excluímos os dois na hora de gerar o zip) — então sua configuração e
> os documentos já enviados continuam intactos.

Depois, com o código atualizado (por qualquer um dos dois caminhos):

```bash
cd /opt/conexao-esporte

# Backend: reaplica o schema (é idempotente — só cria/altera o que mudou)
sudo -u conexao PGPASSWORD='SUA_SENHA' psql -h localhost -U conexao_esporte_app \
  -d conexao_esporte -f database/schema.sql
cd backend
sudo -u conexao .venv/bin/pip install -r requirements.txt
sudo systemctl restart conexao-esporte-api
# Alternativa sem downtime (não use se as dependências do requirements.txt
# mudaram — aí precisa do restart completo acima, que já carrega o venv novo):
#   sudo systemctl reload conexao-esporte-api

# Frontend (build local no Windows e sobe via WinSCP, ou direto no servidor
# se ele tiver Node instalado — os dois funcionam, escolha o mais simples)
cd ../frontend
npm install && npm run build
sudo cp -r dist/* /opt/conexao-esporte/frontend/dist/
```
