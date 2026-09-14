"""
Testes do fluxo 'esqueci minha senha': solicitação por email (token de uso
único) e redefinição com o token recebido. O envio real de email é
substituído por um dublê em todos os testes (ver conftest.py,
`_sem_envio_real_de_email`) — aqui verificamos que o email "seria" enviado
(chamada registrada), nunca o SMTP de verdade.
"""
from app.infrastructure.repositories.redefinicao_senha_repository import RedefinicaoSenhaRepository


def _token_gerado(db_session, usuario_id) -> str:
    """Não dá pra ler o token em texto puro do banco (só o hash é salvo) —
    para os testes de redefinir-senha, gera e guarda o token do mesmo jeito
    que o service faz, direto pelo repositório."""
    import hashlib
    import secrets
    from datetime import datetime, timedelta, timezone

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    RedefinicaoSenhaRepository(db_session).criar(
        usuario_id, token_hash=token_hash, expira_em=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    return token


def test_esqueci_senha_com_email_cadastrado_envia_email(client, seed_basico, _sem_envio_real_de_email):
    resp = client.post("/api/v1/auth/esqueci-senha", json={"email": "master@test.com"})
    assert resp.status_code == 204
    assert len(_sem_envio_real_de_email) == 1
    assert _sem_envio_real_de_email[0]["destinatario"] == "master@test.com"


def test_esqueci_senha_com_email_inexistente_nao_revela_e_nao_envia(client, seed_basico, _sem_envio_real_de_email):
    """Resposta idêntica ao caso de email cadastrado (204), mas sem disparar email."""
    resp = client.post("/api/v1/auth/esqueci-senha", json={"email": "ninguem@test.com"})
    assert resp.status_code == 204
    assert len(_sem_envio_real_de_email) == 0


def test_redefinir_senha_com_token_valido_funciona_e_permite_login(client, seed_basico, db_session):
    master = seed_basico["master"]
    token = _token_gerado(db_session, master.id)

    resp = client.post(
        "/api/v1/auth/redefinir-senha", json={"token": token, "nova_senha": "senha-nova-123"}
    )
    assert resp.status_code == 204

    login_resp = client.post(
        "/api/v1/auth/login", data={"username": "master@test.com", "password": "senha-nova-123"}
    )
    assert login_resp.status_code == 200


def test_redefinir_senha_com_token_ja_usado_falha(client, seed_basico, db_session):
    master = seed_basico["master"]
    token = _token_gerado(db_session, master.id)

    primeira = client.post(
        "/api/v1/auth/redefinir-senha", json={"token": token, "nova_senha": "senha-nova-123"}
    )
    assert primeira.status_code == 204

    segunda = client.post(
        "/api/v1/auth/redefinir-senha", json={"token": token, "nova_senha": "outra-senha-456"}
    )
    assert segunda.status_code == 400


def test_redefinir_senha_com_token_invalido_falha(client, seed_basico):
    resp = client.post(
        "/api/v1/auth/redefinir-senha", json={"token": "token-que-nao-existe", "nova_senha": "senha-nova-123"}
    )
    assert resp.status_code == 400


def test_solicitar_redefinicao_invalida_token_anterior_ainda_nao_usado(client, seed_basico, _sem_envio_real_de_email):
    """Pedir uma segunda redefinição invalida a primeira — só o link mais
    recente deve funcionar."""
    client.post("/api/v1/auth/esqueci-senha", json={"email": "master@test.com"})
    client.post("/api/v1/auth/esqueci-senha", json={"email": "master@test.com"})
    assert len(_sem_envio_real_de_email) == 2

    link_primeiro_email = _sem_envio_real_de_email[0]["html"]
    token_primeiro = link_primeiro_email.split("token=")[1].split('"')[0]

    resp = client.post(
        "/api/v1/auth/redefinir-senha", json={"token": token_primeiro, "nova_senha": "senha-nova-123"}
    )
    assert resp.status_code == 400
