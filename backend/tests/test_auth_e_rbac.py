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
    polo_a_id = str(seed_basico["polo_a"].id)

    # menor de idade SEM responsável legal -> deve falhar
    resp = client.post(
        "/api/v1/beneficiarios",
        json={
            "nome_completo": "Criança Teste", "data_nascimento": "2015-01-01",
            "documento": "111.222.333-44", "polo_id": polo_a_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "responsável legal" in resp.json()["detail"].lower()


def test_resposta_inclui_security_headers(client):
    resp = client.get("/")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["referrer-policy"] == "strict-origin-when-cross-origin"


def test_endpoint_usa_nomenclatura_beneficiario(client):
    """A rota oficial é /beneficiarios — nunca /alunos."""
    schema = client.app.openapi()
    paths = schema["paths"]
    assert any("/beneficiarios" in p for p in paths)
    assert not any("aluno" in p.lower() for p in paths)


def test_login_e_bloqueado_apos_muitas_tentativas(client, seed_basico):
    """Proteção contra força bruta: 10 tentativas/minuto por IP em /auth/login."""
    for _ in range(10):
        resp = client.post(
            "/api/v1/auth/login", data={"username": "master@test.com", "password": "errada"}
        )
        assert resp.status_code == 401

    bloqueado = client.post(
        "/api/v1/auth/login", data={"username": "master@test.com", "password": "errada"}
    )
    assert bloqueado.status_code == 429


def test_alterar_senha_sucesso_e_login_com_nova_senha(client, seed_basico):
    token = login(client, "master@test.com")
    resp = client.patch(
        "/api/v1/auth/senha",
        json={"senha_atual": "senha123", "nova_senha": "senha-nova-456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204, resp.text

    # a senha antiga não funciona mais, a nova sim
    assert client.post(
        "/api/v1/auth/login", data={"username": "master@test.com", "password": "senha123"}
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login", data={"username": "master@test.com", "password": "senha-nova-456"}
    ).status_code == 200


def test_alterar_senha_com_senha_atual_incorreta_falha(client, seed_basico):
    token = login(client, "master@test.com")
    resp = client.patch(
        "/api/v1/auth/senha",
        json={"senha_atual": "errada123", "nova_senha": "senha-nova-456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401


def test_gestor_cria_professor_forcando_proprio_polo(client, seed_basico):
    """GESTOR_POLO só pode cadastrar PROFESSOR, sempre vinculado ao seu próprio polo
    — mesmo que tente informar o polo_id de outro polo no corpo da requisição."""
    token = login(client, "gestor.a@test.com")
    polo_b_id = str(seed_basico["polo_b"].id)
    resp = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Professor Teste", "email": "prof.teste@test.com", "senha": "senha123",
            "perfil": "PROFESSOR", "polo_id": polo_b_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["polo_id"] == str(seed_basico["polo_a"].id)


def test_gestor_nao_cria_outro_gestor(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    resp = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Outro Gestor", "email": "outro.gestor@test.com", "senha": "senha123",
            "perfil": "GESTOR_POLO",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_criar_turma_com_professor_de_outro_polo_falha(client, seed_basico):
    """Um professor só pode ser vinculado a turmas do próprio polo — impede que
    um GESTOR_POLO dê acesso de leitura da turma a um professor de fora."""
    token_a = login(client, "gestor.a@test.com")
    token_b = login(client, "gestor.b@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    polo_b_id = str(seed_basico["polo_b"].id)
    modalidade_id = str(seed_basico["modalidade"].id)

    professor_b = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Professor B", "email": "prof.b@test.com", "senha": "senha123",
            "perfil": "PROFESSOR", "polo_id": polo_b_id,
        },
        headers={"Authorization": f"Bearer {token_b}"},
    ).json()

    resp = client.post(
        "/api/v1/turmas",
        json={
            "polo_id": polo_a_id, "modalidade_id": modalidade_id, "professor_id": professor_b["id"],
            "horario_inicio": "08:00", "horario_fim": "09:00",
            "dias_semana": ["SEG"], "limite_vagas": 10,
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 400


def test_criar_turma_com_professor_id_de_usuario_nao_professor_falha(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    resp = client.post(
        "/api/v1/turmas",
        json={
            # gestor_a não é PROFESSOR
            "polo_id": polo_a_id, "modalidade_id": modalidade_id,
            "professor_id": str(seed_basico["gestor_a"].id),
            "horario_inicio": "08:00", "horario_fim": "09:00",
            "dias_semana": ["SEG"], "limite_vagas": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_polo_horario_funcionamento_cadastro_e_edicao(client, seed_basico):
    token = login(client, "master@test.com")
    criado = client.post(
        "/api/v1/polos",
        json={"nome": "Polo com Horário", "horario_funcionamento": "Seg a Sex, 08h às 18h"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert criado.status_code == 201, criado.text
    assert criado.json()["horario_funcionamento"] == "Seg a Sex, 08h às 18h"

    editado = client.patch(
        f"/api/v1/polos/{criado.json()['id']}",
        json={"horario_funcionamento": "Seg a Sáb, 07h às 20h"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert editado.status_code == 200, editado.text
    assert editado.json()["horario_funcionamento"] == "Seg a Sáb, 07h às 20h"
