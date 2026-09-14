"""
Testes da Lista de Espera: inscrição pública (sem autenticação), listagem
de pendentes com RBAC por polo, e o aceite (cria/reaproveita Beneficiário +
Matrícula). O envio real de email é substituído por um dublê em todos os
testes (ver conftest.py, `_sem_envio_real_de_email`).
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


def _inscrever(client, polo_id, modalidade_id, documento="000.111.222-33", data_nascimento="2015-01-01",
                nome_responsavel="Responsável Teste", documento_responsavel="11122233344"):
    return client.post(
        "/api/v1/lista-espera",
        json={
            "nome_completo": "Beneficiário Teste", "data_nascimento": data_nascimento, "documento": documento,
            "nome_responsavel": nome_responsavel, "documento_responsavel": documento_responsavel,
            "telefone_whatsapp": "(11) 91234-5678",
            "email": "familia@test.com", "bairro": "Centro", "cidade": "São Paulo",
            "modalidade_id": modalidade_id, "polo_id": polo_id, "como_conheceu": "Instagram",
        },
    )


def test_opcoes_publicas_sem_autenticacao(client, seed_basico):
    resp = client.get("/api/v1/lista-espera/opcoes")
    assert resp.status_code == 200
    body = resp.json()
    nomes_polos = [p["nome"] for p in body["polos"]]
    assert "Polo A" in nomes_polos and "Polo B" in nomes_polos
    assert any(m["nome"] == "Judô" for m in body["modalidades"])


def test_inscrever_publico_cria_pendente_e_envia_confirmacao(client, seed_basico, _sem_envio_real_de_email):
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)

    resp = _inscrever(client, polo_a_id, modalidade_id)
    assert resp.status_code == 201, resp.text
    assert resp.json()["nome_completo"] == "Beneficiário Teste"
    assert len(_sem_envio_real_de_email) == 1
    assert _sem_envio_real_de_email[0]["destinatario"] == "familia@test.com"
    assert "Inscrição recebida" in _sem_envio_real_de_email[0]["assunto"]


def test_inscrever_menor_sem_responsavel_falha(client, seed_basico):
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)

    resp = _inscrever(
        client, polo_a_id, modalidade_id, data_nascimento="2015-01-01",
        nome_responsavel=None, documento_responsavel=None,
    )
    assert resp.status_code == 400


def test_inscrever_menor_com_nome_responsavel_mas_sem_documento_falha(client, seed_basico):
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)

    resp = _inscrever(
        client, polo_a_id, modalidade_id, data_nascimento="2015-01-01",
        nome_responsavel="Mãe Teste", documento_responsavel=None,
    )
    assert resp.status_code == 400


def test_inscrever_menor_com_responsavel_funciona(client, seed_basico, _sem_envio_real_de_email):
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)

    resp = _inscrever(
        client, polo_a_id, modalidade_id, data_nascimento="2015-01-01",
        nome_responsavel="Mãe Teste", documento_responsavel="99988877766",
    )
    assert resp.status_code == 201, resp.text


def test_inscrever_participante_mais_novo_que_a_faixa_do_projeto_falha(client, seed_basico):
    """Projeto atende de 6 a 17 anos — mais novo que isso é recusado."""
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)

    resp = _inscrever(client, polo_a_id, modalidade_id, data_nascimento="2021-01-01")
    assert resp.status_code == 400


def test_inscrever_participante_mais_velho_que_a_faixa_do_projeto_falha(client, seed_basico):
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)

    resp = _inscrever(client, polo_a_id, modalidade_id, data_nascimento="2008-01-01")
    assert resp.status_code == 400


def test_inscrever_nos_limites_da_faixa_etaria_funciona(client, seed_basico, _sem_envio_real_de_email):
    """6 e 17 anos são os limites inclusivos da faixa atendida."""
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)

    seis_anos = _inscrever(client, polo_a_id, modalidade_id, documento="66666", data_nascimento="2020-01-01")
    assert seis_anos.status_code == 201, seis_anos.text

    dezessete_anos = _inscrever(client, polo_a_id, modalidade_id, documento="17171", data_nascimento="2009-01-01")
    assert dezessete_anos.status_code == 201, dezessete_anos.text


def test_gestor_so_ve_pendentes_do_proprio_polo(client, seed_basico, _sem_envio_real_de_email):
    polo_a_id = str(seed_basico["polo_a"].id)
    polo_b_id = str(seed_basico["polo_b"].id)
    modalidade_id = str(seed_basico["modalidade"].id)

    _inscrever(client, polo_a_id, modalidade_id, documento="11111")
    _inscrever(client, polo_b_id, modalidade_id, documento="22222")

    token_a = login(client, "gestor.a@test.com")
    resp = client.get("/api/v1/lista-espera", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    documentos = [i["documento"] for i in resp.json()]
    assert documentos == ["11111"]


def test_master_ve_pendentes_de_todos_os_polos(client, seed_basico, _sem_envio_real_de_email):
    polo_a_id = str(seed_basico["polo_a"].id)
    polo_b_id = str(seed_basico["polo_b"].id)
    modalidade_id = str(seed_basico["modalidade"].id)

    _inscrever(client, polo_a_id, modalidade_id, documento="11111")
    _inscrever(client, polo_b_id, modalidade_id, documento="22222")

    token_master = login(client, "master@test.com")
    resp = client.get("/api/v1/lista-espera", headers={"Authorization": f"Bearer {token_master}"})
    assert resp.status_code == 200
    assert {i["documento"] for i in resp.json()} == {"11111", "22222"}


def test_aceitar_cria_beneficiario_e_matricula_e_envia_email(client, seed_basico, _sem_envio_real_de_email):
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    token_master = login(client, "master@test.com")

    turma = _criar_turma(client, token_master, polo_a_id, modalidade_id)
    inscricao = _inscrever(client, polo_a_id, modalidade_id, documento="33333").json()

    resp = client.post(
        f"/api/v1/lista-espera/{inscricao['id']}/aceitar",
        json={"turma_id": turma["id"]},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 204, resp.text

    beneficiarios = client.get(
        "/api/v1/beneficiarios", headers={"Authorization": f"Bearer {token_master}"}
    ).json()
    criado = next(b for b in beneficiarios if b["documento"] == "33333")

    matriculas = client.get(
        f"/api/v1/beneficiarios/{criado['id']}/matriculas", headers={"Authorization": f"Bearer {token_master}"}
    ).json()
    assert any(m["turma_id"] == turma["id"] for m in matriculas)

    # 2 emails: confirmação da inscrição + aceite.
    assert len(_sem_envio_real_de_email) == 2
    assert "Inscrição aceita" in _sem_envio_real_de_email[1]["assunto"]


def test_aceitar_com_documento_existente_reaproveita_beneficiario(client, seed_basico, _sem_envio_real_de_email):
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    token_master = login(client, "master@test.com")

    turma = _criar_turma(client, token_master, polo_a_id, modalidade_id)
    beneficiario_existente = client.post(
        "/api/v1/beneficiarios",
        json={
            "nome_completo": "Já Cadastrado", "data_nascimento": "2000-01-01",
            "documento": "44444", "polo_id": polo_a_id,
        },
        headers={"Authorization": f"Bearer {token_master}"},
    ).json()

    inscricao = _inscrever(client, polo_a_id, modalidade_id, documento="44444").json()
    resp = client.post(
        f"/api/v1/lista-espera/{inscricao['id']}/aceitar",
        json={"turma_id": turma["id"]},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 204, resp.text

    beneficiarios = client.get(
        "/api/v1/beneficiarios", headers={"Authorization": f"Bearer {token_master}"}
    ).json()
    documentos_444 = [b for b in beneficiarios if b["documento"] == "44444"]
    assert len(documentos_444) == 1
    assert documentos_444[0]["id"] == beneficiario_existente["id"]


def test_aceitar_turma_de_outro_polo_falha(client, seed_basico, _sem_envio_real_de_email):
    polo_a_id = str(seed_basico["polo_a"].id)
    polo_b_id = str(seed_basico["polo_b"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    token_master = login(client, "master@test.com")

    turma_polo_b = _criar_turma(client, token_master, polo_b_id, modalidade_id)
    inscricao = _inscrever(client, polo_a_id, modalidade_id, documento="55555").json()

    resp = client.post(
        f"/api/v1/lista-espera/{inscricao['id']}/aceitar",
        json={"turma_id": turma_polo_b["id"]},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 400


def test_aceitar_duas_vezes_falha(client, seed_basico, _sem_envio_real_de_email):
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    token_master = login(client, "master@test.com")

    turma = _criar_turma(client, token_master, polo_a_id, modalidade_id)
    inscricao = _inscrever(client, polo_a_id, modalidade_id, documento="66666").json()

    client.post(
        f"/api/v1/lista-espera/{inscricao['id']}/aceitar",
        json={"turma_id": turma["id"]},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    resp = client.post(
        f"/api/v1/lista-espera/{inscricao['id']}/aceitar",
        json={"turma_id": turma["id"]},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 400


def test_gestor_b_nao_aceita_inscricao_do_polo_a(client, seed_basico, _sem_envio_real_de_email):
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    token_master = login(client, "master@test.com")

    turma = _criar_turma(client, token_master, polo_a_id, modalidade_id)
    inscricao = _inscrever(client, polo_a_id, modalidade_id, documento="77777").json()

    token_b = login(client, "gestor.b@test.com")
    resp = client.post(
        f"/api/v1/lista-espera/{inscricao['id']}/aceitar",
        json={"turma_id": turma["id"]},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403
