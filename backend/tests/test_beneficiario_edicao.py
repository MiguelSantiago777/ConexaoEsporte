"""Testes da edição de beneficiário (PATCH) — data de nascimento editável."""
from tests.conftest import login
from tests.test_beneficiario_reativacao import _cadastrar, _headers


def test_editar_data_de_nascimento(client, seed_basico):
    token = login(client, "master@test.com")
    criado = _cadastrar(client, token, str(seed_basico["polo_a"].id), "66677788899").json()

    resp = client.patch(
        f"/api/v1/beneficiarios/{criado['id']}", json={"data_nascimento": "1999-03-15"}, headers=_headers(token)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data_nascimento"] == "1999-03-15"


def test_editar_data_de_nascimento_pra_menor_sem_responsavel_falha(client, seed_basico):
    token = login(client, "master@test.com")
    criado = _cadastrar(client, token, str(seed_basico["polo_a"].id), "66677788800").json()

    resp = client.patch(
        f"/api/v1/beneficiarios/{criado['id']}", json={"data_nascimento": "2015-01-01"}, headers=_headers(token)
    )
    assert resp.status_code == 400, resp.text

    resp = client.patch(
        f"/api/v1/beneficiarios/{criado['id']}",
        json={"data_nascimento": "2015-01-01", "responsavel_legal_nome": "Mãe Teste"},
        headers=_headers(token),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data_nascimento"] == "2015-01-01"
