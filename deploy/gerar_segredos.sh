#!/usr/bin/env bash
# Gera a senha do usuário do banco e a JWT_SECRET_KEY, e já mostra prontos
# o comando SQL e as linhas do .env pra copiar/colar — ver DEPLOY.md.
#
# Uso (no servidor, dentro da pasta do repositório):
#   bash deploy/gerar_segredos.sh
set -euo pipefail

DB_PASSWORD=$(openssl rand -hex 24)
JWT_SECRET=$(openssl rand -hex 32)

echo "===================================================================="
echo " Guarde estes dois valores — eles não ficam salvos em lugar nenhum,"
echo " só aparecem aqui uma vez."
echo "===================================================================="
echo
echo "Senha do usuário do banco (conexao_esporte_app): $DB_PASSWORD"
echo "JWT_SECRET_KEY:                                  $JWT_SECRET"
echo
echo "--------------------------------------------------------------------"
echo "1) Cole isto no 'sudo -u postgres psql' (passo 2 do DEPLOY.md):"
echo "--------------------------------------------------------------------"
cat <<SQL
CREATE DATABASE conexao_esporte;
CREATE USER conexao_esporte_app WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE conexao_esporte TO conexao_esporte_app;
\c conexao_esporte
GRANT ALL ON SCHEMA public TO conexao_esporte_app;
SQL
echo
echo "--------------------------------------------------------------------"
echo "2) Cole isto no backend/.env (passo 3 do DEPLOY.md):"
echo "--------------------------------------------------------------------"
cat <<ENV
DATABASE_URL=postgresql://conexao_esporte_app:$DB_PASSWORD@localhost:5432/conexao_esporte
JWT_SECRET_KEY=$JWT_SECRET
ENV
echo
echo "===================================================================="
