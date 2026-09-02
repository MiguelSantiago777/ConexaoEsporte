"""Testes de edição e remoção de Modalidade esportiva — a remoção é
recusada quando existe alguma turma cadastrada com a modalidade, pra não
deixar a constraint de chave estrangeira do banco estourar sem uma
mensagem clara."""
import pytest

from tests.conftest import login


def test_editar_modalidade(client, seed_basico):
    token_gestor = login(client, "gestor.a@test.com")
    modalidade_id = str(seed_basico["modalidade"].id)

    resp = client.patch(
        f"/api/v1/modalidades/{modalidade_id}",
        json={"nome": "Judô Infantil", "descricao": "Turmas para crianças"},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["nome"] == "Judô Infantil"
    assert corpo["descricao"] == "Turmas para crianças"


def test_editar_modalidade_inexistente_retorna_404(client, seed_basico):
    token_gestor = login(client, "gestor.a@test.com")
    resp = client.patch(
        "/api/v1/modalidades/00000000-0000-0000-0000-000000000000",
        json={"nome": "Não existe"},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp.status_code == 404


def test_remover_modalidade_sem_turma(client, seed_basico):
    token_gestor = login(client, "gestor.a@test.com")
    resp_criar = client.post(
        "/api/v1/modalidades", json={"nome": "Xadrez"}, headers={"Authorization": f"Bearer {token_gestor}"}
    )
    assert resp_criar.status_code == 201, resp_criar.text
    modalidade_id = resp_criar.json()["id"]

    resp_remover = client.delete(
        f"/api/v1/modalidades/{modalidade_id}", headers={"Authorization": f"Bearer {token_gestor}"}
    )
    assert resp_remover.status_code == 204

    resp_lista = client.get("/api/v1/modalidades", headers={"Authorization": f"Bearer {token_gestor}"})
    assert modalidade_id not in {m["id"] for m in resp_lista.json()}


def test_remover_modalidade_em_uso_por_turma_e_recusada(client, seed_basico):
    token_gestor = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)

    resp_turma = client.post(
        "/api/v1/turmas",
        json={
            "polo_id": polo_a_id, "modalidade_id": modalidade_id,
            "horario_inicio": "08:00", "horario_fim": "09:00",
            "dias_semana": ["SEG"], "limite_vagas": 10,
        },
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp_turma.status_code == 201, resp_turma.text

    resp_remover = client.delete(
        f"/api/v1/modalidades/{modalidade_id}", headers={"Authorization": f"Bearer {token_gestor}"}
    )
    assert resp_remover.status_code == 400
    assert "turmas" in resp_remover.json()["detail"].lower()

    # A modalidade continua lá.
    resp_lista = client.get("/api/v1/modalidades", headers={"Authorization": f"Bearer {token_gestor}"})
    assert modalidade_id in {m["id"] for m in resp_lista.json()}
