# Deploy em produção — servidor Linux próprio

Guia de instalação nativa (sem Docker): PostgreSQL, backend (FastAPI) e
frontend (React) rodando direto no servidor.

**Este servidor já tem outro app usando as portas 80, 443 e 8000 (Apache
na 80/443, um Gunicorn dele na 8000) — mas não tem Postgres instalado. O
domínio do Conexão Esporte ainda vai ser configurado depois.** O guia
abaixo já foi ajustado pra conviver com isso:

- **Postgres (5432):** este servidor não tinha Postgres instalado
  (confirmado via `systemctl`, `ss`, `dpkg` e `docker ps` — nada achado),
  então instalamos do zero, só pra esta aplicação. Diferente de um cenário
  onde já existisse uma instância a reaproveitar, aqui não tem outro banco
  pra isolar — mas o usuário de aplicação dedicado (nunca o superusuário
  `postgres`) continua sendo boa prática de qualquer forma.
- **Backend Uvicorn:** porta `8010` em vez de `8000` (só em `127.0.0.1`,
  nunca exposta — o número em si não importa muito, só não pode colidir
  com o Gunicorn do outro app, que já ocupa a `8000`).
- **Frontend/Nginx (80/443):** o outro app usa **Apache** nessas portas,
  não Nginx — então `apt install nginx` não mexe em nada dele. Como ainda
  não tem domínio, o site do Conexão Esporte sobe temporariamente na porta
  `8080` (`http://SEU_IP:8080`), sem conflito nenhum com o Apache. **Ponto
  de atenção pra quando o domínio estiver pronto (passo 5.2):** Nginx e
  Apache não escutam a mesma porta 80/443 ao mesmo tempo do jeito simples
  — como o Apache já é dono dessas portas, nessa hora vai ser preciso
  decidir entre (a) colocar o Nginx na frente roteando por domínio e mover
  o Apache pra escutar só internamente (ex.: `127.0.0.1:8081`, com o
  próprio Nginx fazendo proxy pro site dele também), ou (b) publicar o
  Conexão Esporte como mais um `VirtualHost`/proxy dentro do próprio
  Apache em vez de instalar Nginx pra valer. Não é bloqueio agora — só não
  é tão simples quanto "múltiplos `server_name` dividem a mesma porta",
  como seria se o outro app já usasse Nginx.

Comandos testados para Ubuntu/Debian (`apt`); em outra distro troque o
gerenciador de pacotes, o resto é igual.

---

## 0. Visão geral

```
Agora (sem domínio):
Internet ──8080──> Nginx ──┬─ arquivos estáticos (frontend/dist)
                            └─ /api/* ──> Uvicorn (127.0.0.1:8010) ──> PostgreSQL (127.0.0.1:5432, instalado só pra este app)
Internet ──80/443──> Apache (outro app, sem mexer)

Depois (com domínio) — ver ressalva do passo 5.2 sobre dividir a 80/443 com o Apache:
Internet ──443──> Nginx (server_name esporte.seudominio.com.br) ──> mesma coisa
```

- Postgres e o backend só escutam em `127.0.0.1` — nunca ficam expostos
  diretamente à internet, só o Nginx.
- O backend roda como serviço systemd, sem `--reload`, com o mesmo usuário
  Linux `servidor` que já roda o outro app neste servidor — sem privilégio
  de root. O isolamento entre os dois apps vem de *sandboxing* do próprio
  systemd (`ProtectSystem=strict`, `ProtectHome=read-only` e
  `ReadWritePaths` liberando escrita só na pasta `uploads/`), em vez de um
  usuário Linux dedicado — o processo não consegue escrever em nada fora
  dali, nem nos próprios arquivos do projeto, nem nos do outro app.

Antes de tudo, confirme o que realmente está em cada porta (só pra não
supor errado):

```bash
sudo ss -tlnp | grep -E ':80 |:443 |:8000 |:5432 '
```

Se **5432** não aparecer em nada (nem `ss`, nem `ps aux | grep postgres`,
nem `dpkg -l | grep postgres`, nem `docker ps`), é porque não tem Postgres
instalado ainda — normal, o passo 2 instala do zero e ele nasce escutando
nessa porta por padrão, sem precisar trocar nada. Só troque os números
deste guia se a porta já estiver ocupada por **outra coisa** que não seja
Postgres (mesma lógica valeria pra **8080**, se ela também já estivesse em
uso).

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

> **Firewall (`ufw`) inativo neste servidor:** o `ufw status` mostrou
> `inactive` — ele nunca foi ativado aqui (o outro app roda exposto sem
> regra nenhuma; Postgres e o backend deste app continuam protegidos de
> qualquer forma, por escutarem só em `127.0.0.1`). Os comandos acima só
> deixam as regras *prontas*, sem ativar o firewall (`sudo ufw enable`) —
> ativar remotamente tem risco de travar o próprio acesso SSH se algo na
> regra do OpenSSH não pegar. Só ative se tiver um plano B de acesso ao
> servidor (console da hospedagem, etc.) e depois de confirmar que a regra
> `OpenSSH` está mesmo lá (`sudo ufw status`).

Este app roda com o mesmo usuário Linux que já é dono do resto do
servidor (`servidor`, o mesmo da galerianata) — sem criar usuário
dedicado novo. O isolamento entre os dois apps fica por conta do
*sandboxing* do systemd no passo 3 (`ProtectSystem=strict` etc.), não de
UIDs separados. A pasta do projeto fica ao lado da galerianata, dentro da
home de `servidor`:

```bash
mkdir -p /home/servidor/conexao-esporte
```

(sem `sudo` — como você já está logado como `servidor`, é sua própria
home, não precisa de privilégio extra.)

---

## 2. PostgreSQL (instalação nova, só pra este app)

Este servidor não tinha Postgres — instale o pacote padrão do
Ubuntu/Debian, que já sobe como serviço e escuta em `127.0.0.1`/`localhost`
por padrão (não precisa mudar nada nisso):

```bash
sudo apt install -y postgresql
sudo systemctl status postgresql --no-pager
sudo grep listen_addresses /etc/postgresql/*/main/postgresql.conf
```

Confirme que criou um usuário Linux `postgres` (padrão do pacote) e que o
serviço está `active (running)`.

Crie o banco e um **usuário de aplicação dedicado só do Conexão Esporte**
(nunca use o superusuário `postgres` na `DATABASE_URL`, mesmo sendo a
única aplicação usando esta instância — evita que um bug na app tenha
privilégio de superusuário no banco). O Postgres não tem um "gerar senha
pra mim" embutido — mas o script abaixo gera uma senha aleatória forte e
já te devolve o SQL e as linhas do `.env` prontos pra colar, sem você ter
que digitar nada à mão:

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

Esse usuário só enxerga o banco `conexao_esporte` — não tem privilégio de
superusuário nem acesso a outros bancos que venham a existir nesta mesma
instância no futuro.

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
---

## 3. Backend (FastAPI)

Primeiro, coloque o código em `/home/servidor/conexao-esporte` (a pasta
criada no passo 1, ao lado da galerianata). Como está tudo dentro da sua
própria home, nenhum comando daqui pra baixo precisa de `sudo` — só os que
mexem em pacotes do sistema ou no systemd/Nginx. Duas formas de trazer o
código — use a que preferir:

**Via `git clone`** (repositório é público no GitHub):

```bash
sudo apt install -y python3.12-venv build-essential libpq-dev git
git clone https://github.com/MiguelSantiago777/ConexaoEsporte.git /home/servidor/conexao-esporte
```

**Via WinSCP + PuTTY (zip, sem Git)** — ver seção **3.1** logo abaixo para o
passo a passo completo, incluindo como gerar o zip no Windows.

Depois de qualquer um dos dois, com o código já em `/home/servidor/conexao-esporte`:

```bash
sudo apt install -y python3.12-venv build-essential libpq-dev
cd /home/servidor/conexao-esporte/backend

python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

> **Exportação de relatórios em PDF:** além das dependências acima, a
> exportação em PDF (`?formato=pdf` nas rotas de relatórios) chama o
> LibreOffice headless (`soffice`) por trás dos panos para converter o
> `.xlsx`/`.docx` gerado — sem ele, só os formatos originais funcionam.
> Instale a versão "sem interface" (bem mais leve que o pacote completo):
> ```bash
> sudo apt install -y libreoffice-calc libreoffice-writer
> ```

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
arraste o `conexao-esporte.zip` para a **sua home no servidor**
(`/home/servidor/`).

No **PuTTY** (SSH), extraia direto no lugar certo (sem precisar de `sudo`,
é a sua própria home):

```bash
sudo apt install -y unzip
unzip -q ~/conexao-esporte.zip -d /home/servidor/conexao-esporte
rm ~/conexao-esporte.zip
```

Confira que ficou com a cara certa antes de seguir para o resto do passo 3:

```bash
ls /home/servidor/conexao-esporte
# deve mostrar: backend  frontend  database  deploy  DEPLOY.md  README.md ...
```

Crie o `.env` de produção a partir do exemplo, restringindo a leitura só
ao dono (o servidor tem outro app rodando, então outras contas locais
podem existir):

```bash
cp .env.example .env
chmod 600 .env
nano .env
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
UPLOAD_DIR=/home/servidor/conexao-esporte/backend/uploads/documentos
```

`ENVIRONMENT=production` faz duas coisas automaticamente: a aplicação se
recusa a subir se `JWT_SECRET_KEY` ainda for o valor padrão de
desenvolvimento, e o Swagger/ReDoc (`/docs`, `/redoc`, `/openapi.json`)
ficam desligados.

Crie o primeiro usuário MASTER:

```bash
cd /home/servidor/conexao-esporte/backend
.venv/bin/python scripts/criar_usuario_master.py
```

Teste manualmente antes de criar o serviço (porta `8010`, para não colidir
com o `8000` do outro app). Em produção quem sobe a aplicação é o
**Gunicorn**, usando o Uvicorn só como "worker class" (Gunicorn gerencia os
processos — reinicia worker que travar, faz reload gradual sem derrubar
conexão — e o Uvicorn é quem entende async/FastAPI de fato):

```bash
.venv/bin/gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker --workers 2 --bind 127.0.0.1:8010
# noutro terminal:
curl http://127.0.0.1:8010/
# Ctrl+C para parar depois de confirmar que respondeu {"status":"ok",...}
```

> Mesmo já tendo Gunicorn instalado no servidor, ele entra como dependência
> do `requirements.txt` (dentro do venv deste projeto) — assim a versão
> fica isolada e não depende do que outro app já tem instalado
> globalmente, evitando que uma atualização de um quebre o outro.

Instale como serviço systemd — o arquivo em `deploy/` já usa Gunicorn +
Uvicorn workers na porta `8010`, `User=servidor`/`Group=servidor` e o
caminho `/home/servidor/conexao-esporte`, então não precisa editar nada se
você seguiu os caminhos deste guia:

```bash
sudo cp deploy/conexao-esporte-api.service /etc/systemd/system/
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
cd /home/servidor/conexao-esporte/frontend
npm install
npm run build   # gera frontend/dist
```

Como o Nginx serve o frontend e a API na **mesma origem** (via proxy em
`/api/`), não é preciso configurar `VITE_API_URL` — o `api.ts` já usa o
caminho relativo `/api/v1` por padrão. Isso continua valendo tanto na
porta temporária `8080` quanto depois no domínio final.

Como tudo já está dentro da home de `servidor`, o Nginx aponta direto pra
`frontend/dist` — não precisa copiar pra lugar nenhum (isso só seria
necessário se o build ficasse fora do alcance de leitura do Nginx, o que
não é o caso aqui: `/home/servidor` é `755`, então o worker do Nginx
consegue ler os arquivos normalmente).

---

## 5. Nginx

### 5.1 Agora — sem domínio, porta 8080

```bash
# O outro app usa Apache (80/443) — apt install nginx instala do zero,
# sem mexer nele. Nginx só vai escutar na 8080 por enquanto.
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

**Ressalva importante (já avisada na Visão geral):** como o outro app usa
**Apache** nas portas 80/443 — não Nginx —, não dá pra simplesmente trocar
`listen 8080;` por `listen 80;` no Nginx: as duas portas já têm dono
(Apache) e dois processos não escutam a mesma porta ao mesmo tempo. Antes
de mexer em DNS/certbot, decida um dos dois caminhos:

- **(a) Nginx assume a porta 80/443, Apache passa a escutar só
  internamente.** Reconfigura o Apache pra ouvir em algo tipo
  `127.0.0.1:8081` (editar `Listen` e o `VirtualHost` do Apache) e o Nginx
  ganha um segundo `server_name` fazendo proxy pra lá, além do
  `server_name` do Conexão Esporte. Deixa os dois apps atrás do mesmo
  Nginx, cada um por `server_name`/domínio.
- **(b) Publica o Conexão Esporte dentro do próprio Apache**, com um novo
  `VirtualHost`/`ServerName` pro domínio dele e `mod_proxy`/`mod_proxy_http`
  encaminhando `/api/` pro backend (`127.0.0.1:8010`) e servindo
  `frontend/dist` como arquivos estáticos — sem nunca colocar o Nginx pra
  valer em produção (ele fica só como preview temporário na 8080, e dá pra
  desinstalar depois).

Este guia documenta o caminho com Nginx (opção a) por ser o mais comum,
mas os comandos abaixo assumem que a porta 80/443 **já está livre pro
Nginx** — ou seja, o Apache já foi movido pra outra porta antes de rodar
isso. Se preferir a opção (b), a configuração de `VirtualHost`+proxy do
Apache não está coberta aqui.

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
configurada (`systemctl status certbot.timer`). Com a opção (a) já feita
(Apache movido pra outra porta e reconfigurado como segundo `server_name`
no Nginx), os dois apps continuam respondendo, cada um pelo seu domínio.

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
- [x] `DATABASE_URL` com usuário/senha dedicados (nunca `postgres`/`postgres`); a app recusa subir com essa credencial padrão quando `ENVIRONMENT=production` (mesma trava do JWT, ver `app/core/config.py`).
- [x] `backend/.env` com permissão `600` (leitura restrita ao dono do arquivo, `servidor`).
- [x] Autenticação via Bearer JWT puro (`HTTPBearer`) em todas as rotas protegidas.
- [x] Rate limiting em `/auth/login` e `PATCH /auth/senha` (10 tentativas/minuto por IP) — ver `app/core/rate_limit.py`.
- [x] Security headers em toda resposta (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Strict-Transport-Security` quando HTTPS) — ver middleware em `app/main.py`.
- [x] `client_max_body_size` no Nginx, alinhado ao limite de upload do backend (`deploy/nginx.conf.example`).
- [x] Validação de que `professor_id` vinculado a uma turma é de fato um PROFESSOR do mesmo polo (evita vazamento de acesso entre polos).
- [x] Nome de arquivo de documentos sanitizado antes de entrar no header `Content-Disposition` no download.
- [x] Postgres e backend acessíveis só via `127.0.0.1` — nunca exponha as portas 5432/8010 no firewall.
- [x] Usuário de banco dedicado (`conexao_esporte_app`), sem privilégio de superusuário.
- [x] `CORS_ORIGINS` restrito à origem real do frontend (porta temporária agora, domínio HTTPS depois).
- [x] Swagger/ReDoc desligados em produção (`ENVIRONMENT=production`).
- [x] Backend rodando como usuário Linux sem privilégios (`servidor`, nunca root), isolado do resto do sistema via *sandboxing* do systemd (`ProtectSystem=strict`, `ProtectHome=read-only`, `ReadWritePaths` só em `uploads/`).
- [x] Aba "Alterar senha" disponível para todo usuário logado trocar a própria senha.
- [ ] Migrar para HTTPS assim que o domínio estiver pronto (passo 5.2) — não deixe rodando só em HTTP por muito tempo, principalmente com dados de menores de idade envolvidos.
- [ ] Configure backups periódicos do banco (passo 7).
- [ ] Troque a senha do usuário MASTER se em algum momento você rodou `seed.sql` para testar.
- [ ] (Melhoria futura, não bloqueante) Refresh tokens não são revogados/rotacionados no logout ou troca de senha — um refresh token válido continua ativo até sua expiração natural (7 dias) mesmo depois de trocar a senha. Para revogação imediata, precisaria de uma tabela de tokens emitidos/revogados no banco.

---

## 7. Backup do banco

Cron diário simples com `pg_dump`, fazendo backup só do banco
`conexao_esporte`:

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

Primeiro, atualize o código em `/home/servidor/conexao-esporte` (é sua
própria home, nenhum comando abaixo precisa de `sudo` além do restart do
serviço):

**Via Git:**

```bash
cd /home/servidor/conexao-esporte
git pull
```

**Via WinSCP + PuTTY (zip)** — gere um novo zip como na seção 3.1, suba
pra sua home no servidor via WinSCP e, no PuTTY:

```bash
unzip -oq ~/conexao-esporte.zip -d /home/servidor/conexao-esporte   # -o sobrescreve sem perguntar
rm ~/conexao-esporte.zip
```

> O `unzip -o` sobrescreve os arquivos do projeto, mas não apaga o `.env`
> nem a pasta `uploads/` se eles não estiverem dentro do zip (e não estão,
> já excluímos os dois na hora de gerar o zip) — então sua configuração e
> os documentos já enviados continuam intactos.

Depois, com o código atualizado (por qualquer um dos dois caminhos):

```bash
cd /home/servidor/conexao-esporte

# Backend: reaplica o schema (é idempotente — só cria/altera o que mudou)
PGPASSWORD='SUA_SENHA' psql -h localhost -U conexao_esporte_app \
  -d conexao_esporte -f database/schema.sql
cd backend
.venv/bin/pip install -r requirements.txt
sudo systemctl restart conexao-esporte-api
# Alternativa sem downtime (não use se as dependências do requirements.txt
# mudaram — aí precisa do restart completo acima, que já carrega o venv novo):
#   sudo systemctl reload conexao-esporte-api

# Frontend (build local no Windows e sobe via WinSCP, ou direto no servidor
# se ele tiver Node instalado — os dois funcionam, escolha o mais simples)
cd ../frontend
npm install && npm run build
# Nada pra copiar — o Nginx já lê direto de frontend/dist.
```
