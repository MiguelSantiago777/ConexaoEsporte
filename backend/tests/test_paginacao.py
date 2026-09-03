"""Testes da paginação server-side das listagens principais (Beneficiários,
Turmas, Professores, Polos, Entregas de Materiais, Fichas de Execução) —
sem `pagina`, cada rota continua devolvendo a lista inteira (uso por telas
que só precisam das opções, como um <select>); com `pagina`, passa a
devolver o envelope {itens, total, pagina, tamanho_pagina}, com a página
pedida calculada no banco (LIMIT/OFFSET)."""
import pytest

from tests.conftest import login


def _criar_turma(client, token, polo_id, modalidade_id):
    resp = client.post(
        "/api/v1/turmas",
        json={
            "polo_id": polo_id, "modalidade_id": modalidade_id,
            "horario_inicio": "08:00", "horario_fim": "09:00",
            "dias_semana": ["SEG"], "limite_vagas": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _criar_beneficiario(client, token, polo_id, nome, documento):
    resp = client.post(
        "/api/v1/beneficiarios",
        json={"nome_completo": nome, "data_nascimento": "2000-01-01", "documento": documento, "polo_id": polo_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _criar_professor(client, token_gestor, polo_id, email):
    resp = client.post(
        "/api/v1/usuarios",
        json={"nome": "Professor Paginacao", "email": email, "senha": "senha123", "perfil": "PROFESSOR", "polo_id": polo_id},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_beneficiarios_sem_pagina_continua_lista_completa(client, seed_basico):
    token_gestor = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    for i in range(3):
        _criar_beneficiario(client, token_gestor, polo_a_id, f"Beneficiário {i}", f"111.000.000-0{i}")

    resp = client.get("/api/v1/beneficiarios", headers={"Authorization": f"Bearer {token_gestor}"})
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json(), list)
    assert len(resp.json()) == 3


def test_beneficiarios_paginados_com_total_e_filtro_por_nome(client, seed_basico):
    token_gestor = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    nomes = ["Ana Silva", "Bruno Souza", "Carla Dias", "Ana Pereira", "Diego Lima"]
    for i, nome in enumerate(nomes):
        _criar_beneficiario(client, token_gestor, polo_a_id, nome, f"222.000.000-0{i}")

    resp_p1 = client.get(
        "/api/v1/beneficiarios", params={"pagina": 1, "tamanho_pagina": 2},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp_p1.status_code == 200, resp_p1.text
    corpo = resp_p1.json()
    assert corpo["total"] == 5
    assert corpo["pagina"] == 1
    assert corpo["tamanho_pagina"] == 2
    assert len(corpo["itens"]) == 2
    # Ordenado por nome — primeira página traz os 2 primeiros em ordem alfabética.
    assert [b["nome_completo"] for b in corpo["itens"]] == ["Ana Pereira", "Ana Silva"]

    resp_p3 = client.get(
        "/api/v1/beneficiarios", params={"pagina": 3, "tamanho_pagina": 2},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp_p3.status_code == 200
    corpo_p3 = resp_p3.json()
    assert corpo_p3["total"] == 5
    assert len(corpo_p3["itens"]) == 1

    resp_busca = client.get(
        "/api/v1/beneficiarios", params={"pagina": 1, "tamanho_pagina": 10, "nome": "ana"},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp_busca.status_code == 200
    corpo_busca = resp_busca.json()
    assert corpo_busca["total"] == 2
    assert {b["nome_completo"] for b in corpo_busca["itens"]} == {"Ana Silva", "Ana Pereira"}


def test_beneficiarios_paginados_isola_por_polo_do_gestor(client, seed_basico):
    token_gestor_a = login(client, "gestor.a@test.com")
    token_gestor_b = login(client, "gestor.b@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    polo_b_id = str(seed_basico["polo_b"].id)
    _criar_beneficiario(client, token_gestor_a, polo_a_id, "Beneficiário Polo A", "333.000.000-01")
    _criar_beneficiario(client, token_gestor_b, polo_b_id, "Beneficiário Polo B", "333.000.000-02")

    resp = client.get(
        "/api/v1/beneficiarios", params={"pagina": 1, "tamanho_pagina": 10},
        headers={"Authorization": f"Bearer {token_gestor_a}"},
    )
    corpo = resp.json()
    assert corpo["total"] == 1
    assert corpo["itens"][0]["nome_completo"] == "Beneficiário Polo A"


def test_turmas_paginadas(client, seed_basico):
    token_gestor = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    for _ in range(3):
        _criar_turma(client, token_gestor, polo_a_id, modalidade_id)

    resp_sem_pagina = client.get("/api/v1/turmas", headers={"Authorization": f"Bearer {token_gestor}"})
    assert isinstance(resp_sem_pagina.json(), list)
    assert len(resp_sem_pagina.json()) == 3

    resp_paginada = client.get(
        "/api/v1/turmas", params={"pagina": 1, "tamanho_pagina": 2},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp_paginada.status_code == 200
    corpo = resp_paginada.json()
    assert corpo["total"] == 3
    assert len(corpo["itens"]) == 2


def test_professores_paginados_filtra_por_perfil(client, seed_basico):
    token_gestor = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    _criar_professor(client, token_gestor, polo_a_id, "prof.pag1@test.com")
    _criar_professor(client, token_gestor, polo_a_id, "prof.pag2@test.com")

    resp = client.get(
        "/api/v1/usuarios", params={"perfil": "PROFESSOR", "pagina": 1, "tamanho_pagina": 10},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    # Só os 2 professores — o próprio gestor (perfil GESTOR_POLO) não entra.
    assert corpo["total"] == 2
    assert all(u["perfil"] == "PROFESSOR" for u in corpo["itens"])


def test_polos_paginados_e_busca_por_nome(client, seed_basico):
    token_master = login(client, "master@test.com")

    resp = client.get(
        "/api/v1/polos", params={"pagina": 1, "tamanho_pagina": 1},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["total"] == 2  # Polo A e Polo B do seed_basico
    assert len(corpo["itens"]) == 1

    resp_busca = client.get(
        "/api/v1/polos", params={"pagina": 1, "tamanho_pagina": 10, "nome": "Polo A"},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    corpo_busca = resp_busca.json()
    assert corpo_busca["total"] == 1
    assert corpo_busca["itens"][0]["nome"] == "Polo A"


def test_entregas_materiais_paginadas(client, seed_basico):
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    for _ in range(3):
        resp = client.post(
            "/api/v1/entregas-materiais",
            json={"polo_id": polo_a_id, "itens": [{"descricao": "Bola", "quantidade": "5"}]},
            headers={"Authorization": f"Bearer {token_master}"},
        )
        assert resp.status_code == 201, resp.text

    resp = client.get(
        "/api/v1/entregas-materiais", params={"pagina": 1, "tamanho_pagina": 2},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["total"] == 3
    assert len(corpo["itens"]) == 2


def test_fichas_execucao_paginadas(client, seed_basico):
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    for i in range(3):
        resp = client.post(
            "/api/v1/fichas-execucao",
            json={"polo_id": polo_a_id, "periodo_referencia": f"{i+1}º Trimestre 2026"},
            headers={"Authorization": f"Bearer {token_master}"},
        )
        assert resp.status_code == 201, resp.text

    resp = client.get(
        "/api/v1/fichas-execucao", params={"pagina": 1, "tamanho_pagina": 2},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["total"] == 3
    assert len(corpo["itens"]) == 2
