"""Testes do cadastro de usuário sem senha: omitir `senha` em POST /usuarios
dá ao usuário a senha temporária padrão (`SENHA_TEMPORARIA_PADRAO`) e o marca
com `deve_trocar_senha=True`, forçando a troca no primeiro acesso — não
depende mais de e-mail chegar pra conseguir entrar."""
from app.application.usuario.service import SENHA_TEMPORARIA_PADRAO
from tests.conftest import login


def test_criar_usuario_sem_senha_usa_senha_temporaria_padrao(client, seed_basico):
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

    resp_login = client.post(
        "/api/v1/auth/login",
        data={"username": "gestor.convidado@test.com", "password": SENHA_TEMPORARIA_PADRAO},
    )
    assert resp_login.status_code == 200, resp_login.text


def test_criar_usuario_com_senha_nao_precisa_trocar(client, seed_basico):
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

    # A senha informada funciona normalmente pra login, sem exigir troca.
    resp_login = client.post(
        "/api/v1/auth/login", data={"username": "gestor.comsenha@test.com", "password": "senha123"}
    )
    assert resp_login.status_code == 200
    token = resp_login.json()["access_token"]
    resp_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp_me.json()["deve_trocar_senha"] is False


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


def test_usuario_com_senha_temporaria_e_forcado_a_trocar_no_primeiro_acesso(client, seed_basico):
    token_master = login(client, "master@test.com")
    client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Gestor Convidado", "email": "gestor.convidado2@test.com",
            "perfil": "GESTOR_POLO", "polo_id": str(seed_basico["polo_a"].id),
        },
        headers={"Authorization": f"Bearer {token_master}"},
    )
    resp_login = client.post(
        "/api/v1/auth/login",
        data={"username": "gestor.convidado2@test.com", "password": SENHA_TEMPORARIA_PADRAO},
    )
    token = resp_login.json()["access_token"]
    resp_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp_me.json()["deve_trocar_senha"] is True

    resp_trocar = client.patch(
        "/api/v1/auth/senha",
        json={"senha_atual": SENHA_TEMPORARIA_PADRAO, "nova_senha": "nova-senha-forte-456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_trocar.status_code == 204, resp_trocar.text

    resp_me_depois = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp_me_depois.json()["deve_trocar_senha"] is False
