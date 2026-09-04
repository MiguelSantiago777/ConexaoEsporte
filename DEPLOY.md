# Deploy em produção — servidor Linux próprio

Guia de instalação nativa (sem Docker): PostgreSQL, backend (FastAPI) e
frontend (React) rodando direto no servidor.

**Este servidor já tem outro app usando as portas 80, 443 e 8000 (Apache
na 80/443, com domínio próprio — `galeria.institutonata.org.br` — e um
Gunicorn dele na 8000) — mas não tem Postgres instalado. O domínio do
Conexão Esporte ainda vai ser configurado depois.** O guia abaixo já foi
ajustado pra conviver com isso:

- **Postgres (5432):** este servidor não tinha Postgres instalado
  (confirmado via `systemctl`, `ss`, `dpkg` e `docker ps` — nada achado),
  então instalamos do zero, só pra esta aplicação. Diferente de um cenário
  onde já existisse uma instância a reaproveitar, aqui não tem outro banco
  pra isolar — mas o usuário de aplicação dedicado (nunca o superusuário
  `postgres`) continua sendo boa prática de qualquer forma.
- **Backend Uvicorn:** porta `8010` em vez de `8000` (só em `127.0.0.1`,
  nunca exposta — o número em si não importa muito, só não pode colidir
  com o Gunicorn do outro app, que já ocupa a `8000`).
- **Frontend/Apache (80/443):** o outro app já roda em **Apache**, então
  o Conexão Esporte usa o mesmo Apache em vez de instalar Nginx — evita
  ter dois servidores web concorrendo pela mesma porta. Como ainda não tem
  domínio, o site do Conexão Esporte sobe temporariamente num
  `VirtualHost` numa porta alternativa (`8080`, `http://SEU_IP:8080`), sem
  conflito nenhum com o VirtualHost do outro app. **Quando o domínio
  estiver pronto (passo 5.2):** como o outro app já usa `ServerName`
  explícito (`galeria.institutonata.org.br`, não é um "catch-all"), basta
  o Conexão Esporte virar mais um `VirtualHost` na porta 80/443 com o
  próprio `ServerName` — o Apache roteia nativamente pelo header `Host`,
  sem precisar mover nada do outro app nem colocar um proxy reverso na
  frente dos dois.

Comandos testados para Ubuntu/Debian (`apt`); em outra distro troque o
gerenciador de pacotes, o resto é igual.

---

## 0. Visão geral

```
Agora (sem domínio):
Internet ──8080──> Apache (VirtualHost novo) ──┬─ arquivos estáticos (frontend/dist)
                                                 └─ /api/* ──> Uvicorn (127.0.0.1:8010) ──> PostgreSQL (127.0.0.1:5432, instalado só pra este app)
Internet ──80/443──> Apache (VirtualHost do outro app, sem mexer)

Depois (com domínio) — mesmo Apache, dois VirtualHosts dividindo a porta pelo ServerName:
Internet ──443──> Apache (ServerName conexaoesporte.institutonata.org.br) ──> mesma coisa
Internet ──443──> Apache (ServerName galeria.institutonata.org.br) ──> outro app, sem mexer
```

- Postgres e o backend só escutam em `127.0.0.1` — nunca ficam expostos
  diretamente à internet, só o Apache.
- O backend roda como serviço systemd, sem `--reload`, sob um **usuário
  Linux dedicado** (`conexao_esporte`) — separado do `servidor`, que é
  quem roda o outro app neste servidor — sem privilégio de root. Isso
  importa porque os dois apps compartilham o mesmo servidor/SO: se
  rodassem como o mesmo usuário, uma falha que desse execução de código
  no outro app já teria acesso de leitura ao `.env` e aos uploads deste
  (permissão de dono sempre vale pro próprio dono, mesmo com `chmod 600`).
  Com usuários separados, isso não acontece. O *sandboxing* do systemd
  (`ProtectSystem=strict`, `ProtectHome=read-only` e `ReadWritePaths`
  liberando escrita só na pasta `uploads/`) continua valendo por cima
  disso, contendo o próprio processo do Conexão Esporte.

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

Crie o usuário Linux dedicado que vai rodar (e ser dono d)o Conexão
Esporte — sem senha e sem shell de login, já que ele só existe pra ser
dono de arquivos e do processo do backend, nunca pra logar de verdade:

```bash
sudo useradd --system --create-home --home-dir /home/conexao_esporte --shell /usr/sbin/nologin conexao_esporte
sudo chmod 711 /home/conexao_esporte
```

`711`: o dono (`conexao_esporte`) tem acesso total; qualquer outro
usuário do sistema consegue *atravessar* o diretório (necessário porque
o Apache, rodando como `www-data`, precisa alcançar `frontend/dist`),
mas não *listar* o conteúdo. O código do backend, o `.venv` e o `.env`
continuam sem nenhum acesso para "outros" — só `frontend/dist` (arquivos
estáticos já públicos de qualquer forma) fica de fato legível por fora,
no passo 4.

Você continua logado via SSH como `servidor` normalmente. Todo comando
daqui pra frente que grava algo dentro da pasta do projeto (clone, `pip
install`, `npm install`, criar o `.env` etc.) roda como o usuário novo
via `sudo -u conexao_esporte` — é só um prefixo a mais em cada comando,
sem precisar abrir outra sessão SSH nem trocar de usuário de verdade.

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

> Sem o script, o equivalente manual é `openssl rand -hex 24` (senha do
> banco — hexadecimal, sem caracteres como `/` que quebram a `DATABASE_URL`)
> e `openssl rand -hex 32` (`JWT_SECRET_KEY`) — copie a saída de
> cada comando pros lugares certos. Se o servidor não tiver `openssl`
> instalado, `python3 -c "import secrets; print(secrets.token_urlsafe(24))"`
> funciona igual (o Python já é obrigatório pro backend).

Esse usuário só enxerga o banco `conexao_esporte` — não tem privilégio de
superusuário nem acesso a outros bancos que venham a existir nesta mesma
instância no futuro.

O schema usa a extensão `pgcrypto` (pra gerar UUID) — criá-la exige
superusuário, então rode isso uma vez como `postgres` antes do schema (o
próprio `schema.sql` também tenta criar, mas o usuário de aplicação não
tem permissão; sem isso, toda tabela falha em cascata porque nenhuma
consegue resolver `gen_random_uuid()`):

```bash
sudo -u postgres psql -d conexao_esporte -c 'CREATE EXTENSION IF NOT EXISTS "pgcrypto";'
```

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

Primeiro, coloque o código em `/home/conexao_esporte/conexao-esporte` (a
home criada no passo 1 pro usuário dedicado). Duas formas de trazer o
código — use a que preferir:

**Via `git clone`** (repositório é público no GitHub):

```bash
sudo apt install -y python3.12-venv build-essential libpq-dev git
sudo -u conexao_esporte git clone https://github.com/MiguelSantiago777/ConexaoEsporte.git /home/conexao_esporte/conexao-esporte
```

**Via WinSCP + PuTTY (zip, sem Git)** — ver seção **3.1** logo abaixo para o
passo a passo completo, incluindo como gerar o zip no Windows.

O projeto usa sintaxe `X | None` de tipos direto (sem
`from __future__ import annotations`), então **exige Python 3.10+ de
verdade rodando** — não é só uma questão de compatibilidade de sintaxe,
o processo nem sobe em Python mais antigo. Confirme antes:

```bash
python3 --version
```

**Se já for 3.10+**, pode usar `python3` mesmo daqui pra baixo. **Se for
mais antigo** (ex.: Ubuntu 20.04 vem com Python 3.8), tente primeiro o
repositório `deadsnakes` — mas ele só builda pra distros ainda dentro do
suporte padrão, então em algo tão antigo quanto o 20.04 (fora de suporte
desde abril/2025) é bem provável que não tenha nada publicado pra ela:

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
apt-cache madison python3.12   # se não aparecer nada, o deadsnakes não serve — pule pro método abaixo
```

**Se o deadsnakes não tiver a versão pra sua distro** (foi o caso real no
primeiro deploy deste guia, em Ubuntu 20.04 — o `apt update` "achava" o
repositório mas nenhum pacote dele aparecia, porque o índice de pacotes
retornava 404 direto na fonte), compile o Python do código-fonte oficial.
Mais lento (uns 5-15 min de `make`), mas não depende de nenhum repositório
terceiro manter suporte à sua distro:

```bash
sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
  libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget \
  libbz2-dev liblzma-dev libpq-dev

cd /tmp
wget https://www.python.org/ftp/python/3.12.7/Python-3.12.7.tgz
tar -xf Python-3.12.7.tgz
cd Python-3.12.7
./configure --enable-optimizations
make -j"$(nproc)"
sudo make altinstall
python3.12 --version
```

`make altinstall` (não `make install`) é o que garante que isso não
sobrescreve nem interfere no `python3`/`python3.8` que o resto do sistema
(outros apps incluídos) já usa — instala só como `/usr/local/bin/python3.12`,
um binário adicional, sem tocar em nada existente.

Depois de qualquer um dos caminhos acima (o `deadsnakes`, se sua distro
tiver suporte, já deixa `python3.12-venv` pronto; a compilação do
código-fonte já inclui o módulo `venv` embutido, sem pacote extra), com o
código já em `/home/conexao_esporte/conexao-esporte`:

```bash
cd /home/conexao_esporte/conexao-esporte/backend

sudo -u conexao_esporte python3.12 -m venv .venv
sudo -u conexao_esporte .venv/bin/pip install --upgrade pip
sudo -u conexao_esporte .venv/bin/pip install -r requirements.txt
```

Agora que o código já está todo no lugar, feche o acesso de "outros" ao
que é sensível e deixe só travessia (sem listagem) no resto — o `backend/`
(código, `.venv`, e o `.env` que você ainda vai criar) fica completamente
inacessível a qualquer usuário que não seja `conexao_esporte`; só
`frontend/dist`, depois de buildado no passo 4, vai ganhar leitura:

```bash
sudo chmod 711 /home/conexao_esporte/conexao-esporte
sudo chmod 700 /home/conexao_esporte/conexao-esporte/backend
sudo chmod 711 /home/conexao_esporte/conexao-esporte/frontend
```

> Se o seu Ubuntu já tinha Python 3.10+ nativo (não precisou do
> deadsnakes), troque `python3.12` por `python3` nesses dois últimos
> comandos.

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
(`/home/servidor/`) — é só um ponto de trânsito, o zip é apagado depois
de extraído no lugar certo.

No **PuTTY** (SSH), extraia direto no lugar certo, já como o usuário
dedicado (pra sair com o dono certo sem precisar de `chown` depois):

```bash
sudo apt install -y unzip
sudo -u conexao_esporte unzip -q ~/conexao-esporte.zip -d /home/conexao_esporte/conexao-esporte
rm ~/conexao-esporte.zip
```

Confira que ficou com a cara certa antes de seguir para o resto do passo 3:

```bash
ls /home/conexao_esporte/conexao-esporte
# deve mostrar: backend  frontend  database  deploy  DEPLOY.md  README.md ...
```

Crie o `.env` de produção a partir do exemplo, restringindo a leitura só
ao dono (agora o usuário dedicado `conexao_esporte` — nem o `servidor`
consegue ler):

```bash
sudo -u conexao_esporte cp .env.example .env
sudo -u conexao_esporte chmod 600 .env
sudo -u conexao_esporte nano .env
```

Preencha `DATABASE_URL` e `JWT_SECRET_KEY` com o bloco 2 que o
`gerar_segredos.sh` do passo 2 já te deu, e complete o resto:

```dotenv
DATABASE_URL=postgresql://conexao_esporte_app:SUA_SENHA_GERADA@localhost:5432/conexao_esporte
JWT_SECRET_KEY=sua_jwt_secret_gerada
ENVIRONMENT=production
# Enquanto não tem domínio, libere a porta temporária; troque para
# https://conexaoesporte.institutonata.org.br assim que o domínio estiver pronto.
CORS_ORIGINS=http://SEU_IP:8080
UPLOAD_DIR=/home/conexao_esporte/conexao-esporte/backend/uploads/documentos
```

`ENVIRONMENT=production` faz duas coisas automaticamente: a aplicação se
recusa a subir se `JWT_SECRET_KEY` ainda for o valor padrão de
desenvolvimento, e o Swagger/ReDoc (`/docs`, `/redoc`, `/openapi.json`)
ficam desligados.

Crie o primeiro usuário MASTER:

```bash
cd /home/conexao_esporte/conexao-esporte/backend
sudo -u conexao_esporte .venv/bin/python scripts/criar_usuario_master.py
```

Teste manualmente antes de criar o serviço (porta `8010`, para não colidir
com o `8000` do outro app). Em produção quem sobe a aplicação é o
**Gunicorn**, usando o Uvicorn só como "worker class" (Gunicorn gerencia os
processos — reinicia worker que travar, faz reload gradual sem derrubar
conexão — e o Uvicorn é quem entende async/FastAPI de fato):

```bash
sudo -u conexao_esporte .venv/bin/gunicorn app.main:app \
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
Uvicorn workers na porta `8010`, `User=conexao_esporte`/`Group=conexao_esporte`
e o caminho `/home/conexao_esporte/conexao-esporte`, então não precisa
editar nada se você seguiu os caminhos deste guia:

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
cd /home/conexao_esporte/conexao-esporte/frontend
sudo -u conexao_esporte npm install
sudo -u conexao_esporte npm run build   # gera frontend/dist
```

Como o Apache serve o frontend e a API na **mesma origem** (via proxy em
`/api/`), não é preciso configurar `VITE_API_URL` — o `api.ts` já usa o
caminho relativo `/api/v1` por padrão. Isso continua valendo tanto na
porta temporária `8080` quanto depois no domínio final.

O Apache aponta direto pra `frontend/dist` — não precisa copiar pra lugar
nenhum. Isso funciona graças ao esquema de permissões do passo 3 (`backend/`
travado, resto só com bit de travessia): falta só liberar leitura no
conteúdo do `dist/` recém-gerado, que é estático e já público de qualquer
forma:

```bash
sudo -u conexao_esporte chmod -R o+rX /home/conexao_esporte/conexao-esporte/frontend/dist
```

---

## 5. Apache

O outro app já roda em Apache — em vez de instalar Nginx e ter dois
servidores web na máquina, o Conexão Esporte entra como mais um
`VirtualHost` no mesmo Apache. O arquivo do outro app (o que serve
`galeria.institutonata.org.br`) não é tocado em nenhum passo abaixo.

### 5.1 Agora — sem domínio, porta 8080

```bash
# Módulos necessários (proxy reverso pro backend, reescrita de URL pro
# SPA e o header de cache dos assets). Habilitar módulo não afeta o outro
# app, só amplia o que o Apache sabe fazer; o reload é gracioso.
sudo a2enmod proxy proxy_http rewrite headers

sudo cp deploy/apache.conf.example /etc/apache2/sites-available/conexao-esporte.conf
sudo a2ensite conexao-esporte
sudo apachectl configtest
sudo systemctl reload apache2
```

Não mexa no site do outro app (`sites-enabled/`, procure pelo arquivo com
`ServerName galeria.institutonata.org.br`) — o VirtualHost novo escuta só
na `8080`, então não briga com o que já existe.

Acesse `http://SEU_IP:8080` e faça login com o usuário MASTER criado no
passo 3.

### 5.2 Depois — quando o domínio estiver pronto

Como o outro app já usa `ServerName` explícito (não é um "catch-all"
pegando qualquer requisição sem domínio reconhecido), não tem a
complicação de dois processos disputando a mesma porta — os dois
VirtualHosts simplesmente dividem a 80/443, cada um roteado pelo Apache
via header `Host`. Antes de mexer em DNS/certbot, confirme isso:

```bash
sudo apachectl -S
```

Confirme que o VirtualHost do outro app aparece com
`ServerName galeria.institutonata.org.br` (não como `_default_` ou sem
`ServerName`) — se ele for o "default" da porta 80/443, é ele quem
responde a qualquer requisição sem domínio reconhecido (acesso direto por
IP, por exemplo), então o ideal é que o Conexão Esporte não vire esse
default sem querer.

Aponte o DNS (registro `A`) do domínio/subdomínio escolhido
(ex.: `conexaoesporte.institutonata.org.br`) para o IP deste servidor. Depois:

```bash
sudo apt install -y certbot python3-certbot-apache
sudo nano /etc/apache2/sites-available/conexao-esporte.conf
```

Troque `Listen 8080` / `<VirtualHost *:8080>` por `<VirtualHost *:80>`, e
`ServerName _default_` pelo domínio real
(`ServerName conexaoesporte.institutonata.org.br`). Depois:

```bash
sudo apachectl configtest
sudo systemctl reload apache2
sudo certbot --apache -d conexaoesporte.institutonata.org.br
```

O certbot edita o VirtualHost automaticamente para servir em 443 com
HTTPS e redirecionar HTTP→HTTPS — o mesmo certbot já usado para
`galeria.institutonata.org.br`, então a renovação automática (
`systemctl status certbot.timer`) já cobre os dois domínios sem
configuração extra. Os dois apps continuam respondendo, cada um pelo seu
`ServerName`, sem que um interfira no outro.

Depois disso, atualize também:

```bash
# backend/.env
CORS_ORIGINS=https://conexaoesporte.institutonata.org.br
```

e reinicie o serviço (`sudo systemctl restart conexao-esporte-api`). Pode
fechar a porta 8080 no firewall (`sudo ufw delete allow 8080/tcp`).

---

## 6. Checklist de segurança

- [x] Senhas com hash bcrypt (custo 12) — já implementado no backend.
- [x] Senha mínima de 8 caracteres na criação/troca de senha (`usuario_schemas.py`, `auth_schemas.py`).
- [x] `JWT_SECRET_KEY` forte e exclusivo de produção (`openssl rand -hex 32`); a app recusa subir com o valor padrão quando `ENVIRONMENT=production`.
- [x] `DATABASE_URL` com usuário/senha dedicados (nunca `postgres`/`postgres`); a app recusa subir com essa credencial padrão quando `ENVIRONMENT=production` (mesma trava do JWT, ver `app/core/config.py`).
- [x] `backend/.env` com permissão `600` (leitura restrita ao dono do arquivo, `conexao_esporte` — nem o usuário do outro app consegue ler).
- [x] Autenticação via Bearer JWT puro (`HTTPBearer`) em todas as rotas protegidas.
- [x] Rate limiting em `/auth/login` e `PATCH /auth/senha` (10 tentativas/minuto por IP) — ver `app/core/rate_limit.py`.
- [x] Security headers em toda resposta (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Strict-Transport-Security` quando HTTPS) — ver middleware em `app/main.py`.
- [x] `LimitRequestBody` no Apache, alinhado ao limite de upload do backend (`deploy/apache.conf.example`).
- [x] Validação de que `professor_id` vinculado a uma turma é de fato um PROFESSOR do mesmo polo (evita vazamento de acesso entre polos).
- [x] Nome de arquivo de documentos sanitizado antes de entrar no header `Content-Disposition` no download.
- [x] Postgres e backend acessíveis só via `127.0.0.1` — nunca exponha as portas 5432/8010 no firewall.
- [x] Usuário de banco dedicado (`conexao_esporte_app`), sem privilégio de superusuário.
- [x] `CORS_ORIGINS` restrito à origem real do frontend (porta temporária agora, domínio HTTPS depois).
- [x] Swagger/ReDoc desligados em produção (`ENVIRONMENT=production`).
- [x] Backend rodando sob usuário Linux dedicado (`conexao_esporte`, nunca root nem o `servidor` que roda o outro app), isolado do resto do sistema via *sandboxing* do systemd (`ProtectSystem=strict`, `ProtectHome=read-only`, `ReadWritePaths` só em `uploads/`) e via permissões de arquivo (`backend/` em `700`, ilegível por qualquer outro usuário, incluindo o do outro app).
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

Primeiro, atualize o código em `/home/conexao_esporte/conexao-esporte`.
Como esses arquivos são donos do usuário dedicado, os comandos que gravam
ali continuam levando `sudo -u conexao_esporte` (só o restart do serviço
precisa de `sudo` puro):

**Via Git:**

```bash
cd /home/conexao_esporte/conexao-esporte
sudo -u conexao_esporte git pull
```

**Via WinSCP + PuTTY (zip)** — gere um novo zip como na seção 3.1, suba
pra sua home no servidor via WinSCP e, no PuTTY:

```bash
sudo -u conexao_esporte unzip -oq ~/conexao-esporte.zip -d /home/conexao_esporte/conexao-esporte   # -o sobrescreve sem perguntar
rm ~/conexao-esporte.zip
```

> O `unzip -o` sobrescreve os arquivos do projeto, mas não apaga o `.env`
> nem a pasta `uploads/` se eles não estiverem dentro do zip (e não estão,
> já excluímos os dois na hora de gerar o zip) — então sua configuração e
> os documentos já enviados continuam intactos.

Depois, com o código atualizado (por qualquer um dos dois caminhos):

```bash
cd /home/conexao_esporte/conexao-esporte

# Backend: reaplica o schema (é idempotente — só cria/altera o que mudou)
PGPASSWORD='SUA_SENHA' psql -h localhost -U conexao_esporte_app \
  -d conexao_esporte -f database/schema.sql
cd backend
sudo -u conexao_esporte .venv/bin/pip install -r requirements.txt
sudo systemctl restart conexao-esporte-api
# Alternativa sem downtime (não use se as dependências do requirements.txt
# mudaram — aí precisa do restart completo acima, que já carrega o venv novo):
#   sudo systemctl reload conexao-esporte-api

# Frontend (build local no Windows e sobe via WinSCP, ou direto no servidor
# se ele tiver Node instalado — os dois funcionam, escolha o mais simples)
cd ../frontend
sudo -u conexao_esporte npm install && sudo -u conexao_esporte npm run build
sudo -u conexao_esporte chmod -R o+rX dist
# Nada pra copiar — o Apache já lê direto de frontend/dist.
```
