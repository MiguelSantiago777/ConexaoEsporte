"""Testes de exclusão definitiva (DELETE de verdade, não 'desativar'):
Polo e Usuário — exceto PROFESSOR, que nunca é excluído, só desativado
(`ativo=false`), pra preservar turmas/frequências já registradas."""
from tests.conftest import login


def test_master_exclui_polo_sem_vinculos(client, seed_basico):
    token_master = login(client, "master@test.com")
    headers = {"Authorization": f"Bearer {token_master}"}
    resp_criar = client.post("/api/v1/polos", json={"nome": "Polo Vazio"}, headers=headers)
    assert resp_criar.status_code == 201, resp_criar.text
    polo_id = resp_criar.json()["id"]

    resp_excluir = client.delete(f"/api/v1/polos/{polo_id}", headers=headers)
    assert resp_excluir.status_code == 204, resp_excluir.text

    resp_get = client.get("/api/v1/polos", headers=headers)
    assert polo_id not in [p["id"] for p in resp_get.json()]


def test_master_nao_exclui_polo_com_turma_vinculada(client, seed_basico):
    token_master = login(client, "master@test.com")
    headers = {"Authorization": f"Bearer {token_master}"}
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    client.post(
        "/api/v1/turmas",
        json={
            "polo_id": polo_a_id, "modalidade_id": modalidade_id,
            "horario_inicio": "08:00", "horario_fim": "09:00", "dias_semana": ["SEG"], "limite_vagas": 10,
        },
        headers=headers,
    )

    resp_excluir = client.delete(f"/api/v1/polos/{polo_a_id}", headers=headers)
    assert resp_excluir.status_code == 400
    assert "turmas" in resp_excluir.json()["detail"]

    # O polo continua existindo e utilizável — exclusão bloqueada não é a
    # mesma coisa que desativação, que continua disponível via PATCH.
    resp_get = client.get("/api/v1/polos", headers=headers)
    assert polo_a_id in [p["id"] for p in resp_get.json()]


def test_gestor_nao_exclui_polo(client, seed_basico):
    token_gestor = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    resp = client.delete(
        f"/api/v1/polos/{polo_a_id}", headers={"Authorization": f"Bearer {token_gestor}"}
    )
    assert resp.status_code == 403


def test_master_exclui_gestor_de_polo_sem_vinculos(client, seed_basico):
    token_master = login(client, "master@test.com")
    headers = {"Authorization": f"Bearer {token_master}"}
    polo_id = str(seed_basico["polo_b"].id)
    resp_criar = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Gestor Descartável", "email": "gestor.descartavel@test.com", "senha": "senha123",
            "perfil": "GESTOR_POLO", "polo_id": polo_id,
        },
        headers=headers,
    )
    assert resp_criar.status_code == 201, resp_criar.text
    usuario_id = resp_criar.json()["id"]

    resp_excluir = client.delete(f"/api/v1/usuarios/{usuario_id}", headers=headers)
    assert resp_excluir.status_code == 204, resp_excluir.text

    resp_login = client.post(
        "/api/v1/auth/login", data={"username": "gestor.descartavel@test.com", "password": "senha123"}
    )
    assert resp_login.status_code == 401


def test_professor_nunca_e_excluido_so_desativado(client, seed_basico):
    token_gestor = login(client, "gestor.a@test.com")
    headers = {"Authorization": f"Bearer {token_gestor}"}
    polo_a_id = str(seed_basico["polo_a"].id)
    resp_criar = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Professor Teste", "email": "professor.exclusao@test.com", "senha": "senha123",
            "perfil": "PROFESSOR", "polo_id": polo_a_id,
        },
        headers=headers,
    )
    assert resp_criar.status_code == 201, resp_criar.text
    professor_id = resp_criar.json()["id"]

    token_master = login(client, "master@test.com")
    resp_excluir = client.delete(
        f"/api/v1/usuarios/{professor_id}", headers={"Authorization": f"Bearer {token_master}"}
    )
    assert resp_excluir.status_code == 400
    assert "Professor" in resp_excluir.json()["detail"]

    # Continua existindo — só a desativação (ativo=false) é o caminho certo.
    resp_desativar = client.patch(
        f"/api/v1/usuarios/{professor_id}", json={"ativo": False},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp_desativar.status_code == 200
    assert resp_desativar.json()["ativo"] is False


def test_gestor_nao_exclui_usuario(client, seed_basico):
    token_gestor = login(client, "gestor.a@test.com")
    token_master = login(client, "master@test.com")
    headers_master = {"Authorization": f"Bearer {token_master}"}
    polo_a_id = str(seed_basico["polo_a"].id)
    outro_gestor = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Outro Gestor", "email": "outro.gestor@test.com", "senha": "senha123",
            "perfil": "GESTOR_POLO", "polo_id": polo_a_id,
        },
        headers=headers_master,
    ).json()

    resp = client.delete(
        f"/api/v1/usuarios/{outro_gestor['id']}", headers={"Authorization": f"Bearer {token_gestor}"}
    )
    assert resp.status_code == 403
