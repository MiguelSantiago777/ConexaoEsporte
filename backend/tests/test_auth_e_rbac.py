"""
Testes de integração cobrindo autenticação JWT e o RBAC por polo.
Prova as regras de ouro do sistema:
- Login emite access + refresh.
- MASTER cria polos; GESTOR_POLO não pode.
- GESTOR_POLO do Polo A NÃO acessa dados do Polo B.
- Nomenclatura "beneficiário" nos endpoints.
"""
from tests.conftest import login


def test_login_emite_access_e_refresh(client, seed_basico):
    resp = client.post(
        "/api/v1/auth/login", data={"username": "master@test.com", "password": "senha123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body and "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_senha_errada_falha(client, seed_basico):
    resp = client.post(
        "/api/v1/auth/login", data={"username": "master@test.com", "password": "errada"}
    )
    assert resp.status_code == 401


def test_master_cria_polo(client, seed_basico):
    token = login(client, "master@test.com")
    resp = client.post(
        "/api/v1/polos",
        json={"nome": "Polo Novo", "endereco": "Rua X"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["nome"] == "Polo Novo"
    assert resp.json()["status"] == "ATIVO"


def test_gestor_nao_cria_polo(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    resp = client.post(
        "/api/v1/polos",
        json={"nome": "Polo Proibido"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403  # perfil sem permissão


def test_gestor_a_nao_cria_turma_no_polo_b(client, seed_basico):
    """Regra central: isolamento entre polos."""
    token = login(client, "gestor.a@test.com")
    polo_b_id = str(seed_basico["polo_b"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    resp = client.post(
        "/api/v1/turmas",
        json={
            "polo_id": polo_b_id,  # tenta criar no polo de OUTRO gestor
            "modalidade_id": modalidade_id,
            "horario_inicio": "08:00", "horario_fim": "09:00",
            "dias_semana": ["SEG"], "limite_vagas": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403  # Gestor não tem acesso a dados de outro Polo


def test_gestor_a_cria_turma_no_proprio_polo(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    resp = client.post(
        "/api/v1/turmas",
        json={
            "polo_id": polo_a_id,
            "modalidade_id": modalidade_id,
            "horario_inicio": "08:00", "horario_fim": "09:00",
            "dias_semana": ["SEG", "QUA"], "limite_vagas": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["polo_id"] == polo_a_id
    assert resp.json()["vagas_ocupadas"] == 0


def test_cadastro_beneficiario_menor_exige_responsavel(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    # cria turma primeiro
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    turma = client.post(
        "/api/v1/turmas",
        json={"polo_id": polo_a_id, "modalidade_id": modalidade_id,
              "horario_inicio": "08:00", "horario_fim": "09:00",
              "dias_semana": ["SEG"], "limite_vagas": 10},
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    # menor de idade SEM responsável legal -> deve falhar
    resp = client.post(
        "/api/v1/beneficiarios",
        json={
            "nome_completo": "Criança Teste", "data_nascimento": "2015-01-01",
            "documento": "111.222.333-44", "turma_id": turma["id"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "responsável legal" in resp.json()["detail"].lower()


def test_endpoint_usa_nomenclatura_beneficiario(client):
    """A rota oficial é /beneficiarios — nunca /alunos."""
    schema = client.app.openapi()
    paths = schema["paths"]
    assert any("/beneficiarios" in p for p in paths)
    assert not any("aluno" in p.lower() for p in paths)
