"""Testes da Central de Acessos: MASTER cria Papéis escolhendo módulos do
sistema, cria usuários PERSONALIZADO vinculados a eles, e esses usuários só
têm acesso de leitura/escrita nos módulos concedidos — em nenhum outro."""
import pytest

from tests.conftest import login


def _criar_papel(client, token_master, nome="Financeiro", modulos=None):
    resp = client.post(
        "/api/v1/papeis",
        json={"nome": nome, "modulos": modulos or []},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _criar_usuario_personalizado(client, token_master, papel_id, email="personalizado@test.com"):
    resp = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Usuário Personalizado", "email": email, "senha": "senha123",
            "perfil": "PERSONALIZADO", "papel_id": papel_id,
        },
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_listar_modulos_disponiveis(client, seed_basico):
    token_master = login(client, "master@test.com")
    resp = client.get("/api/v1/papeis/modulos", headers={"Authorization": f"Bearer {token_master}"})
    assert resp.status_code == 200, resp.text
    chaves = {m["chave"] for m in resp.json()}
    assert "beneficiarios" in chaves
    assert "turmas" in chaves
    assert "estoque" in chaves


def test_somente_master_acessa_central_de_acessos(client, seed_basico):
    token_gestor = login(client, "gestor.a@test.com")
    assert client.get("/api/v1/papeis", headers={"Authorization": f"Bearer {token_gestor}"}).status_code == 403
    assert client.post(
        "/api/v1/papeis", json={"nome": "X", "modulos": []}, headers={"Authorization": f"Bearer {token_gestor}"}
    ).status_code == 403


def test_criar_papel_com_modulo_invalido_e_recusado(client, seed_basico):
    token_master = login(client, "master@test.com")
    resp = client.post(
        "/api/v1/papeis", json={"nome": "Inválido", "modulos": ["modulo_que_nao_existe"]},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 422


def test_criar_usuario_personalizado_sem_papel_id_e_recusado(client, seed_basico):
    token_master = login(client, "master@test.com")
    resp = client.post(
        "/api/v1/usuarios",
        json={"nome": "Sem Papel", "email": "sempapel@test.com", "senha": "senha123", "perfil": "PERSONALIZADO"},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 400


def test_usuario_personalizado_so_acessa_o_modulo_concedido(client, seed_basico):
    token_master = login(client, "master@test.com")
    papel = _criar_papel(client, token_master, nome="Cadastro de Beneficiários", modulos=["beneficiarios"])
    _criar_usuario_personalizado(client, token_master, papel["id"])
    token_pers = login(client, "personalizado@test.com")

    polo_a_id = str(seed_basico["polo_a"].id)

    # Consegue criar e listar beneficiários de qualquer polo (módulo concedido).
    resp_criar = client.post(
        "/api/v1/beneficiarios",
        json={"nome_completo": "Fulano", "data_nascimento": "2000-01-01", "documento": "111.111.111-11", "polo_id": polo_a_id},
        headers={"Authorization": f"Bearer {token_pers}"},
    )
    assert resp_criar.status_code == 201, resp_criar.text

    resp_listar = client.get("/api/v1/beneficiarios", headers={"Authorization": f"Bearer {token_pers}"})
    assert resp_listar.status_code == 200
    assert len(resp_listar.json()) == 1

    # Não consegue acessar módulos não concedidos.
    assert client.get("/api/v1/turmas", headers={"Authorization": f"Bearer {token_pers}"}).status_code == 403
    assert client.post(
        "/api/v1/modalidades", json={"nome": "Judô"}, headers={"Authorization": f"Bearer {token_pers}"}
    ).status_code == 403
    assert client.post(
        "/api/v1/polos", json={"nome": "Polo X"}, headers={"Authorization": f"Bearer {token_pers}"}
    ).status_code == 403


def test_usuario_personalizado_com_modulo_professores_so_gerencia_professores(client, seed_basico):
    token_master = login(client, "master@test.com")
    papel = _criar_papel(client, token_master, nome="RH de Professores", modulos=["professores"])
    _criar_usuario_personalizado(client, token_master, papel["id"], email="rh@test.com")
    token_rh = login(client, "rh@test.com")

    polo_a_id = str(seed_basico["polo_a"].id)

    # Tenta criar um GESTOR_POLO — deve ser recusado (só pode PROFESSOR).
    resp_gestor = client.post(
        "/api/v1/usuarios",
        json={"nome": "Tentativa", "email": "tentativa@test.com", "senha": "senha123", "perfil": "GESTOR_POLO", "polo_id": polo_a_id},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp_gestor.status_code == 400

    # Cria um PROFESSOR normalmente, em qualquer polo (Papel não é vinculado a um polo específico).
    resp_prof = client.post(
        "/api/v1/usuarios",
        json={"nome": "Professor Novo", "email": "prof.novo@test.com", "senha": "senha123", "perfil": "PROFESSOR", "polo_id": polo_a_id},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp_prof.status_code == 201, resp_prof.text

    # Listagem só retorna professores, mesmo sem filtro explícito.
    resp_lista = client.get("/api/v1/usuarios", headers={"Authorization": f"Bearer {token_rh}"})
    assert resp_lista.status_code == 200
    perfis = {u["perfil"] for u in resp_lista.json()}
    assert perfis == {"PROFESSOR"}


def test_desativar_papel_remove_acesso_apos_relogin(client, seed_basico):
    token_master = login(client, "master@test.com")
    papel = _criar_papel(client, token_master, nome="Temporário", modulos=["modalidades"])
    _criar_usuario_personalizado(client, token_master, papel["id"], email="temp@test.com")
    token_temp = login(client, "temp@test.com")

    assert client.post(
        "/api/v1/modalidades", json={"nome": "Natação"}, headers={"Authorization": f"Bearer {token_temp}"}
    ).status_code == 201

    # MASTER desativa o Papel.
    resp_editar = client.patch(
        f"/api/v1/papeis/{papel['id']}", json={"ativo": False}, headers={"Authorization": f"Bearer {token_master}"}
    )
    assert resp_editar.status_code == 200

    # Um novo login já reflete a desativação (módulos resolvidos no momento do login).
    token_temp_novo = login(client, "temp@test.com")
    assert client.post(
        "/api/v1/modalidades", json={"nome": "Vôlei"}, headers={"Authorization": f"Bearer {token_temp_novo}"}
    ).status_code == 403


def test_remover_papel_em_uso_e_recusado_mas_sem_uso_funciona(client, seed_basico):
    token_master = login(client, "master@test.com")
    usado = _criar_papel(client, token_master, nome="Em uso", modulos=["turmas"])
    _criar_usuario_personalizado(client, token_master, usado["id"])

    resp_bloqueado = client.delete(f"/api/v1/papeis/{usado['id']}", headers={"Authorization": f"Bearer {token_master}"})
    assert resp_bloqueado.status_code == 400

    sem_uso = _criar_papel(client, token_master, nome="Livre", modulos=[])
    resp_ok = client.delete(f"/api/v1/papeis/{sem_uso['id']}", headers={"Authorization": f"Bearer {token_master}"})
    assert resp_ok.status_code == 204
