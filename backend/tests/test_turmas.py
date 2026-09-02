"""
Testes de exclusão de turma. "Excluir" é uma desativação (ativo=false),
nunca um DELETE físico — turma_id tem ON DELETE CASCADE em frequências,
matrículas, impeditivos e evidências, então apagar de verdade destruiria
o histórico de chamada.
"""
from tests.conftest import login


def _criar_turma(client, token, polo_id, modalidade_id):
    return client.post(
        "/api/v1/turmas",
        json={
            "polo_id": polo_id, "modalidade_id": modalidade_id,
            "horario_inicio": "08:00", "horario_fim": "09:00",
            "dias_semana": ["SEG"], "limite_vagas": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()


def test_excluir_turma_e_desativacao_e_some_da_listagem(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    turma = _criar_turma(client, token, polo_a_id, modalidade_id)

    resp = client.patch(f"/api/v1/turmas/{turma['id']}", json={"ativo": False}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["ativo"] is False

    resp_lista = client.get("/api/v1/turmas", headers=headers)
    assert resp_lista.status_code == 200
    assert turma["id"] not in [t["id"] for t in resp_lista.json()]


def test_gestor_de_outro_polo_nao_exclui_turma(client, seed_basico):
    token_a = login(client, "gestor.a@test.com")
    token_b = login(client, "gestor.b@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    turma = _criar_turma(client, token_a, polo_a_id, modalidade_id)

    resp = client.patch(
        f"/api/v1/turmas/{turma['id']}", json={"ativo": False},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403
