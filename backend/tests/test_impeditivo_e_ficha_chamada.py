"""Testes de Impeditivo de Aula, Falta Justificada e da Ficha de Chamada
mensal agregada (presença/falta/falta justificada/impeditivo/sem marcação)."""
import calendar
from datetime import date

import pytest

from tests.conftest import login


def _criar_turma(client, token, polo_id, modalidade_id, professor_id=None, dias_semana=None):
    turma = client.post(
        "/api/v1/turmas",
        json={
            "polo_id": polo_id, "modalidade_id": modalidade_id,
            "horario_inicio": "08:00", "horario_fim": "09:00",
            "dias_semana": dias_semana or ["SEG"], "limite_vagas": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    if professor_id:
        client.patch(
            f"/api/v1/turmas/{turma['id']}", json={"professor_id": professor_id},
            headers={"Authorization": f"Bearer {token}"},
        )
    return turma


def _criar_beneficiario(client, token, polo_id, documento, nascimento="2000-01-01"):
    resp = client.post(
        "/api/v1/beneficiarios",
        json={
            "nome_completo": "Beneficiário Ficha", "data_nascimento": nascimento,
            "documento": documento, "polo_id": polo_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _criar_professor(client, token_gestor, polo_id, email):
    resp = client.post(
        "/api/v1/usuarios",
        json={"nome": "Professor Ficha", "email": email, "senha": "senha123", "perfil": "PROFESSOR", "polo_id": polo_id},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _segundas_feiras(ano: int, mes: int) -> list[str]:
    _, dias_no_mes = calendar.monthrange(ano, mes)
    return [
        date(ano, mes, dia).isoformat()
        for dia in range(1, dias_no_mes + 1)
        if date(ano, mes, dia).weekday() == 0  # Monday
    ]


@pytest.fixture
def cenario(client, seed_basico):
    """Polo A, turma às segundas-feiras, 1 professor vinculado, 2
    beneficiários matriculados ativos."""
    token_gestor = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)

    professor = _criar_professor(client, token_gestor, polo_a_id, "prof.ficha@test.com")
    turma = _criar_turma(client, token_gestor, polo_a_id, modalidade_id, professor_id=professor["id"], dias_semana=["SEG"])

    b1 = _criar_beneficiario(client, token_gestor, polo_a_id, "111.222.333-44")
    b2 = _criar_beneficiario(client, token_gestor, polo_a_id, "555.666.777-88")
    for b in (b1, b2):
        client.post(
            f"/api/v1/beneficiarios/{b['id']}/matriculas",
            json={"turma_id": turma["id"]},
            headers={"Authorization": f"Bearer {token_gestor}"},
        )

    token_prof = login(client, professor["email"])
    return {
        "polo_a_id": polo_a_id, "turma": turma, "professor": professor,
        "b1": b1, "b2": b2, "token_gestor": token_gestor, "token_prof": token_prof,
    }


def test_criar_impeditivo_marca_todos_os_beneficiarios_na_ficha(client, cenario):
    segundas = _segundas_feiras(2026, 3)  # Março/2026 tem pelo menos 4 segundas
    primeira_segunda = segundas[0]

    resp = client.post(
        "/api/v1/frequencias/impeditivos",
        json={"turma_id": cenario["turma"]["id"], "data": primeira_segunda, "justificativa": "Feriado municipal"},
        headers={"Authorization": f"Bearer {cenario['token_prof']}"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["justificativa"] == "Feriado municipal"

    ficha = client.get(
        "/api/v1/frequencias/ficha-chamada",
        params={"turma_id": cenario["turma"]["id"], "mes": 3, "ano": 2026},
        headers={"Authorization": f"Bearer {cenario['token_prof']}"},
    ).json()

    assert ficha["datas"] == segundas
    assert len(ficha["impeditivos"]) == 1
    for linha in ficha["linhas"]:
        assert linha["status_por_data"][primeira_segunda] == "IMPEDITIVO"
    # impeditivo entra na contagem do resumo uma vez por beneficiário
    assert ficha["resumo"]["impeditivo"] == len(ficha["linhas"])


def test_impeditivo_duplicado_retorna_409(client, cenario):
    dia = _segundas_feiras(2026, 3)[0]
    body = {"turma_id": cenario["turma"]["id"], "data": dia, "justificativa": "Feriado"}
    headers = {"Authorization": f"Bearer {cenario['token_prof']}"}

    assert client.post("/api/v1/frequencias/impeditivos", json=body, headers=headers).status_code == 201
    resp_dup = client.post("/api/v1/frequencias/impeditivos", json=body, headers=headers)
    assert resp_dup.status_code == 409


def test_remover_impeditivo(client, cenario):
    dia = _segundas_feiras(2026, 3)[0]
    headers = {"Authorization": f"Bearer {cenario['token_prof']}"}
    criado = client.post(
        "/api/v1/frequencias/impeditivos",
        json={"turma_id": cenario["turma"]["id"], "data": dia, "justificativa": "Feriado"},
        headers=headers,
    ).json()

    resp = client.delete(f"/api/v1/frequencias/impeditivos/{criado['id']}", headers=headers)
    assert resp.status_code == 204

    restantes = client.get(
        "/api/v1/frequencias/impeditivos",
        params={"turma_id": cenario["turma"]["id"], "mes": 3, "ano": 2026},
        headers=headers,
    ).json()
    assert restantes == []


def test_falta_justificada_aparece_na_ficha_e_conta_para_o_percentual(client, cenario):
    segundas = _segundas_feiras(2026, 3)
    dia1, dia2 = segundas[0], segundas[1]
    headers = {"Authorization": f"Bearer {cenario['token_prof']}"}

    client.post(
        "/api/v1/frequencias/chamada",
        json={
            "turma_id": cenario["turma"]["id"], "data": dia1,
            "presencas": [
                {"beneficiario_id": cenario["b1"]["id"], "presente": True},
                {"beneficiario_id": cenario["b2"]["id"], "presente": False},
            ],
        },
        headers=headers,
    )
    client.post(
        "/api/v1/frequencias/chamada",
        json={
            "turma_id": cenario["turma"]["id"], "data": dia2,
            "presencas": [
                {
                    "beneficiario_id": cenario["b2"]["id"], "presente": False,
                    "falta_justificada": True, "justificativa": "Atestado médico",
                },
            ],
        },
        headers=headers,
    )

    ficha = client.get(
        "/api/v1/frequencias/ficha-chamada",
        params={"turma_id": cenario["turma"]["id"], "mes": 3, "ano": 2026},
        headers=headers,
    ).json()

    linha_b2 = next(l for l in ficha["linhas"] if l["beneficiario_id"] == cenario["b2"]["id"])
    assert linha_b2["status_por_data"][dia1] == "FALTA"
    assert linha_b2["status_por_data"][dia2] == "FALTA_JUSTIFICADA"
    # 0 presenças em len(segundas) dias letivos (nenhum impeditivo no mês)
    assert linha_b2["frequencia_pct"] == 0.0

    linha_b1 = next(l for l in ficha["linhas"] if l["beneficiario_id"] == cenario["b1"]["id"])
    assert linha_b1["status_por_data"][dia1] == "PRESENTE"
    assert linha_b1["frequencia_pct"] == round(100 / len(segundas), 2)


def test_lancar_chamada_em_data_com_impeditivo_e_rejeitado(client, cenario):
    dia = _segundas_feiras(2026, 3)[0]
    headers = {"Authorization": f"Bearer {cenario['token_prof']}"}
    client.post(
        "/api/v1/frequencias/impeditivos",
        json={"turma_id": cenario["turma"]["id"], "data": dia, "justificativa": "Feriado"},
        headers=headers,
    )

    resp = client.post(
        "/api/v1/frequencias/chamada",
        json={
            "turma_id": cenario["turma"]["id"], "data": dia,
            "presencas": [{"beneficiario_id": cenario["b1"]["id"], "presente": True}],
        },
        headers=headers,
    )
    assert resp.status_code == 400, resp.text


def test_professor_de_outra_turma_nao_acessa_ficha_chamada(client, cenario):
    outro_professor = _criar_professor(client, cenario["token_gestor"], cenario["polo_a_id"], "outro.ficha@test.com")
    token_outro = login(client, outro_professor["email"])

    resp = client.get(
        "/api/v1/frequencias/ficha-chamada",
        params={"turma_id": cenario["turma"]["id"], "mes": 3, "ano": 2026},
        headers={"Authorization": f"Bearer {token_outro}"},
    )
    assert resp.status_code == 403
