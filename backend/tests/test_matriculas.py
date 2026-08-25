"""
Testes de Matrícula (vínculo N:N beneficiário↔turma). Cobre a regra
central que motivou o modelo: um mesmo beneficiário pode estar matriculado
em mais de uma modalidade/turma ao mesmo tempo (ex.: judô e natação), e o
documento do RESPONSÁVEL pode se repetir entre irmãos — só o documento do
próprio beneficiário é exclusivo.
"""
from tests.conftest import login


def _criar_turma(client, token, polo_id, modalidade_id, limite_vagas=10):
    return client.post(
        "/api/v1/turmas",
        json={
            "polo_id": polo_id, "modalidade_id": modalidade_id,
            "horario_inicio": "08:00", "horario_fim": "09:00",
            "dias_semana": ["SEG"], "limite_vagas": limite_vagas,
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()


def _criar_beneficiario(client, token, polo_id, documento="000.111.222-33"):
    return client.post(
        "/api/v1/beneficiarios",
        json={
            "nome_completo": "Beneficiário Teste", "data_nascimento": "2000-01-01",
            "documento": documento, "polo_id": polo_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()


def test_beneficiario_pode_ter_matriculas_em_modalidades_diferentes(client, seed_basico):
    """Regra central: a mesma pessoa pode estar em mais de uma modalidade ao mesmo tempo."""
    token = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_judo = str(seed_basico["modalidade"].id)

    modalidade_natacao = client.post(
        "/api/v1/modalidades", json={"nome": "Natação"}, headers={"Authorization": f"Bearer {token}"}
    ).json()

    turma_judo = _criar_turma(client, token, polo_a_id, modalidade_judo)
    turma_natacao = _criar_turma(client, token, polo_a_id, modalidade_natacao["id"])
    beneficiario = _criar_beneficiario(client, token, polo_a_id)

    r1 = client.post(
        f"/api/v1/beneficiarios/{beneficiario['id']}/matriculas",
        json={"turma_id": turma_judo["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    r2 = client.post(
        f"/api/v1/beneficiarios/{beneficiario['id']}/matriculas",
        json={"turma_id": turma_natacao["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text

    matriculas = client.get(
        f"/api/v1/beneficiarios/{beneficiario['id']}/matriculas",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert {m["turma_id"] for m in matriculas} == {turma_judo["id"], turma_natacao["id"]}


def test_matricula_duplicada_na_mesma_turma_falha(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    turma = _criar_turma(client, token, polo_a_id, modalidade_id)
    beneficiario = _criar_beneficiario(client, token, polo_a_id)

    primeira = client.post(
        f"/api/v1/beneficiarios/{beneficiario['id']}/matriculas",
        json={"turma_id": turma["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    segunda = client.post(
        f"/api/v1/beneficiarios/{beneficiario['id']}/matriculas",
        json={"turma_id": turma["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert primeira.status_code == 201
    assert segunda.status_code == 409


def test_matricula_em_turma_sem_vaga_falha(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    turma = _criar_turma(client, token, polo_a_id, modalidade_id, limite_vagas=1)
    b1 = _criar_beneficiario(client, token, polo_a_id, documento="111.111.111-11")
    b2 = _criar_beneficiario(client, token, polo_a_id, documento="222.222.222-22")

    r1 = client.post(
        f"/api/v1/beneficiarios/{b1['id']}/matriculas",
        json={"turma_id": turma["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    r2 = client.post(
        f"/api/v1/beneficiarios/{b2['id']}/matriculas",
        json={"turma_id": turma["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 201
    assert r2.status_code == 400
    assert "vaga" in r2.json()["detail"].lower()


def test_desmatricular_libera_vaga_para_outro_beneficiario(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    turma = _criar_turma(client, token, polo_a_id, modalidade_id, limite_vagas=1)
    b1 = _criar_beneficiario(client, token, polo_a_id, documento="111.111.111-11")
    b2 = _criar_beneficiario(client, token, polo_a_id, documento="222.222.222-22")

    matricula_1 = client.post(
        f"/api/v1/beneficiarios/{b1['id']}/matriculas",
        json={"turma_id": turma["id"]},
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    bloqueada = client.post(
        f"/api/v1/beneficiarios/{b2['id']}/matriculas",
        json={"turma_id": turma["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert bloqueada.status_code == 400

    desmatricula = client.patch(
        f"/api/v1/beneficiarios/{b1['id']}/matriculas/{matricula_1['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert desmatricula.status_code == 200
    assert desmatricula.json()["ativo"] is False

    agora_cabe = client.post(
        f"/api/v1/beneficiarios/{b2['id']}/matriculas",
        json={"turma_id": turma["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert agora_cabe.status_code == 201


def test_matricula_em_turma_de_outro_polo_falha(client, seed_basico):
    token_a = login(client, "gestor.a@test.com")
    master_token = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    polo_b_id = str(seed_basico["polo_b"].id)
    modalidade_id = str(seed_basico["modalidade"].id)

    turma_polo_b = _criar_turma(client, master_token, polo_b_id, modalidade_id)
    beneficiario_polo_a = _criar_beneficiario(client, token_a, polo_a_id)

    resp = client.post(
        f"/api/v1/beneficiarios/{beneficiario_polo_a['id']}/matriculas",
        json={"turma_id": turma_polo_b["id"]},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    # gestor_a não tem acesso à turma de outro polo — RBAC bloqueia antes mesmo da regra de negócio
    assert resp.status_code == 403


def test_documento_do_responsavel_pode_repetir_entre_irmaos(client, seed_basico):
    """O documento é sempre exclusivo do BENEFICIÁRIO — mas nada impede dois
    beneficiários (irmãos) de compartilharem o mesmo responsável legal."""
    token = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)

    base = {
        "responsavel_legal_nome": "Ana da Silva",
        "responsavel_legal_tipo_relacao": "Mãe",
        "responsavel_legal_telefone_1": "21999990000",
        "polo_id": polo_a_id,
    }
    irmao_1 = client.post(
        "/api/v1/beneficiarios",
        json={**base, "nome_completo": "Irmão 1", "data_nascimento": "2010-01-01", "documento": "111.111.111-11"},
        headers={"Authorization": f"Bearer {token}"},
    )
    irmao_2 = client.post(
        "/api/v1/beneficiarios",
        json={**base, "nome_completo": "Irmão 2", "data_nascimento": "2012-01-01", "documento": "222.222.222-22"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert irmao_1.status_code == 201, irmao_1.text
    assert irmao_2.status_code == 201, irmao_2.text
    assert irmao_1.json()["responsavel_legal_nome"] == irmao_2.json()["responsavel_legal_nome"] == "Ana da Silva"


def test_mesmo_documento_para_dois_beneficiarios_falha(client, seed_basico):
    """O documento do BENEFICIÁRIO (diferente do responsável) continua único, sempre."""
    token = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    _criar_beneficiario(client, token, polo_a_id, documento="333.333.333-33")

    resp = client.post(
        "/api/v1/beneficiarios",
        json={
            "nome_completo": "Outra Pessoa", "data_nascimento": "2005-01-01",
            "documento": "333.333.333-33", "polo_id": polo_a_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409
