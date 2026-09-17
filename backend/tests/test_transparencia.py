"""Testes do Portal Transparência: resumo público (sem autenticação),
CRUD de Lançamentos Financeiros e visibilidade de Anexos Gerais (MASTER)."""
import shutil
from pathlib import Path

import pytest

from tests.conftest import login


@pytest.fixture(autouse=True)
def _limpar_uploads_teste():
    yield
    shutil.rmtree(Path("uploads/anexos_gerais"), ignore_errors=True)


def test_resumo_publico_nao_exige_autenticacao_e_agrega_execucao_fisica(client, seed_basico):
    resp = client.get("/api/v1/transparencia/publico")
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["execucao_fisica"]["total_polos"] == 2
    assert corpo["financeiro"]["total_repassado"] == 0
    assert corpo["documentos"] == []


def test_lancamentos_financeiros_somente_master_e_compoem_resumo_publico(client, seed_basico):
    token_master = login(client, "master@test.com")
    token_gestor_a = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    headers_master = {"Authorization": f"Bearer {token_master}"}

    resp_negado = client.post(
        "/api/v1/transparencia/lancamentos",
        json={"categoria": "Recursos Humanos", "tipo": "REPASSE", "valor": 1000, "data_lancamento": "2026-01-10"},
        headers={"Authorization": f"Bearer {token_gestor_a}"},
    )
    assert resp_negado.status_code == 403

    resp_repasse = client.post(
        "/api/v1/transparencia/lancamentos",
        json={
            "categoria": "Recursos Humanos", "tipo": "REPASSE", "valor": 10000.0,
            "data_lancamento": "2026-01-10", "polo_id": polo_a_id,
        },
        headers=headers_master,
    )
    assert resp_repasse.status_code == 201, resp_repasse.text

    resp_execucao = client.post(
        "/api/v1/transparencia/lancamentos",
        json={
            "categoria": "Recursos Humanos", "tipo": "EXECUCAO", "valor": 4000.0,
            "data_lancamento": "2026-02-01", "descricao": "Folha de fevereiro",
        },
        headers=headers_master,
    )
    assert resp_execucao.status_code == 201, resp_execucao.text
    lancamento_execucao_id = resp_execucao.json()["id"]

    resp_lista = client.get("/api/v1/transparencia/lancamentos", headers=headers_master)
    assert resp_lista.status_code == 200
    assert len(resp_lista.json()) == 2

    resp_publico = client.get("/api/v1/transparencia/publico")
    financeiro = resp_publico.json()["financeiro"]
    assert financeiro["total_repassado"] == 10000.0
    assert financeiro["total_executado"] == 4000.0
    assert financeiro["saldo"] == 6000.0
    assert financeiro["por_categoria"] == [
        {"categoria": "Recursos Humanos", "repassado": 10000.0, "executado": 4000.0}
    ]

    resp_valor_invalido = client.post(
        "/api/v1/transparencia/lancamentos",
        json={"categoria": "Material", "tipo": "REPASSE", "valor": -5, "data_lancamento": "2026-01-10"},
        headers=headers_master,
    )
    assert resp_valor_invalido.status_code == 422

    resp_del = client.delete(f"/api/v1/transparencia/lancamentos/{lancamento_execucao_id}", headers=headers_master)
    assert resp_del.status_code == 204

    resp_del_inexistente = client.delete(f"/api/v1/transparencia/lancamentos/{lancamento_execucao_id}", headers=headers_master)
    assert resp_del_inexistente.status_code == 404


def test_anexo_marcado_publico_aparece_no_portal_e_pode_ser_baixado_sem_login(client, seed_basico):
    token_master = login(client, "master@test.com")
    headers_master = {"Authorization": f"Bearer {token_master}"}
    polo_a_id = str(seed_basico["polo_a"].id)

    resp_anexo = client.post(
        "/api/v1/anexos-gerais",
        data={"polo_id": polo_a_id, "titulo": "Termo de Fomento"},
        files={"arquivo": ("termo.pdf", b"conteudo-termo", "application/pdf")},
        headers=headers_master,
    )
    assert resp_anexo.status_code == 201, resp_anexo.text
    anexo = resp_anexo.json()
    assert anexo["publico"] is False

    # Ainda não é público: não aparece no resumo nem é baixável sem login.
    resp_publico_antes = client.get("/api/v1/transparencia/publico")
    assert resp_publico_antes.json()["documentos"] == []
    resp_download_antes = client.get(f"/api/v1/transparencia/publico/documentos/{anexo['id']}/arquivo")
    assert resp_download_antes.status_code == 404

    resp_marcar = client.patch(
        f"/api/v1/anexos-gerais/{anexo['id']}/visibilidade", json={"publico": True}, headers=headers_master,
    )
    assert resp_marcar.status_code == 200, resp_marcar.text
    assert resp_marcar.json()["publico"] is True

    resp_publico_depois = client.get("/api/v1/transparencia/publico")
    documentos = resp_publico_depois.json()["documentos"]
    assert len(documentos) == 1
    assert documentos[0]["titulo"] == "Termo de Fomento"
    assert documentos[0]["polo_nome"] == "Polo A"

    resp_download_depois = client.get(f"/api/v1/transparencia/publico/documentos/{anexo['id']}/arquivo")
    assert resp_download_depois.status_code == 200
    assert resp_download_depois.content == b"conteudo-termo"
