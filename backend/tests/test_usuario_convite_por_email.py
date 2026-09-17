"""Testes do cadastro de usuário sem senha: omitir `senha` em POST /usuarios
dispara o mesmo fluxo de 'esqueci minha senha' (token de uso único por
email) em vez de o usuário nascer com uma senha escolhida por quem
cadastrou. O envio real de email é substituído por um dublê (ver
conftest.py, `_sem_envio_real_de_email`)."""
from tests.conftest import login


def test_criar_usuario_sem_senha_envia_email_de_definicao_de_senha(client, seed_basico, _sem_envio_real_de_email):
    token_master = login(client, "master@test.com")
    resp = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Gestor Convidado", "email": "gestor.convidado@test.com",
            "perfil": "GESTOR_POLO", "polo_id": str(seed_basico["polo_a"].id),
        },
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    assert len(_sem_envio_real_de_email) == 1
    assert _sem_envio_real_de_email[0]["destinatario"] == "gestor.convidado@test.com"


def test_criar_usuario_com_senha_nao_envia_email(client, seed_basico, _sem_envio_real_de_email):
    token_master = login(client, "master@test.com")
    resp = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Gestor Com Senha", "email": "gestor.comsenha@test.com", "senha": "senha123",
            "perfil": "GESTOR_POLO", "polo_id": str(seed_basico["polo_a"].id),
        },
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    assert len(_sem_envio_real_de_email) == 0

    # A senha informada funciona normalmente pra login.
    resp_login = client.post(
        "/api/v1/auth/login", data={"username": "gestor.comsenha@test.com", "password": "senha123"}
    )
    assert resp_login.status_code == 200


def test_criar_usuario_com_telefone_e_cpf(client, seed_basico):
    token_master = login(client, "master@test.com")
    resp = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Gestor Completo", "email": "gestor.completo@test.com", "senha": "senha123",
            "perfil": "GESTOR_POLO", "polo_id": str(seed_basico["polo_a"].id),
            "telefone": "(11) 98765-4321", "cpf": "123.456.789-01",
        },
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["telefone"] == "(11) 98765-4321"
    assert resp.json()["cpf"] == "123.456.789-01"


def test_usuario_convidado_sem_senha_nao_consegue_logar_ate_definir_uma(client, seed_basico):
    token_master = login(client, "master@test.com")
    client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Gestor Convidado", "email": "gestor.convidado2@test.com",
            "perfil": "GESTOR_POLO", "polo_id": str(seed_basico["polo_a"].id),
        },
        headers={"Authorization": f"Bearer {token_master}"},
    )
    # Sem conhecer a senha aleatória gerada internamente, nenhuma tentativa de
    # login funciona — só o link de definição de senha recebido por email.
    resp_login = client.post(
        "/api/v1/auth/login", data={"username": "gestor.convidado2@test.com", "password": "qualquer-coisa"}
    )
    assert resp_login.status_code == 401
