"""
Testes de upload/listagem/download de documentos anexados a um BENEFICIÁRIO,
incluindo o isolamento por polo (mesma regra de RBAC do restante da API).
"""
import shutil
from pathlib import Path

import pytest

from tests.conftest import login


@pytest.fixture(autouse=True)
def _limpar_uploads_teste():
    yield
    shutil.rmtree(Path("uploads/documentos"), ignore_errors=True)


def _criar_beneficiario(client, token, polo_id, documento="000.111.222-33"):
    return client.post(
        "/api/v1/beneficiarios",
        json={
            "nome_completo": "Beneficiário Teste", "data_nascimento": "2000-01-01",
            "documento": documento, "polo_id": polo_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()


def test_envia_lista_e_baixa_documento(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    beneficiario = _criar_beneficiario(client, token, polo_a_id)

    resp = client.post(
        f"/api/v1/beneficiarios/{beneficiario['id']}/documentos",
        files={"comprovante_residencia": ("comprovante.pdf", b"conteudo-fake", "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    documentos = resp.json()
    assert len(documentos) == 1
    assert documentos[0]["tipo"] == "comprovante_residencia"
    assert documentos[0]["nome_arquivo"] == "comprovante.pdf"

    resp_lista = client.get(
        f"/api/v1/beneficiarios/{beneficiario['id']}/documentos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_lista.status_code == 200
    assert len(resp_lista.json()) == 1

    documento_id = documentos[0]["id"]
    resp_download = client.get(
        f"/api/v1/beneficiarios/documentos/{documento_id}/arquivo",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_download.status_code == 200
    assert resp_download.content == b"conteudo-fake"
    assert resp_download.headers["content-type"] == "application/pdf"


def test_tipo_de_arquivo_nao_permitido_e_rejeitado(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    beneficiario = _criar_beneficiario(client, token, polo_a_id)

    resp = client.post(
        f"/api/v1/beneficiarios/{beneficiario['id']}/documentos",
        files={"comprovante_escolar": ("virus.exe", b"conteudo", "application/x-msdownload")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 415


def test_nome_de_arquivo_com_aspas_nao_quebra_content_disposition(client, seed_basico):
    """Nome de arquivo malicioso (com aspas) não pode injetar/quebrar o header."""
    token = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    beneficiario = _criar_beneficiario(client, token, polo_a_id)

    nome_malicioso = 'inocente.pdf"; filename="evil.exe'
    upload = client.post(
        f"/api/v1/beneficiarios/{beneficiario['id']}/documentos",
        files={"comprovante_escolar": (nome_malicioso, b"conteudo", "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    resp = client.get(
        f"/api/v1/beneficiarios/documentos/{upload[0]['id']}/arquivo",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    disposition = resp.headers["content-disposition"]
    # não pode sobrar uma aspa "solta" que feche o filename= antes da hora
    assert '"; filename="evil.exe"' not in disposition
    assert disposition.count('"') == 2


def test_gestor_de_outro_polo_nao_acessa_documento(client, seed_basico):
    """Regra central: isolamento entre polos também vale para documentos."""
    token_a = login(client, "gestor.a@test.com")
    token_b = login(client, "gestor.b@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    beneficiario = _criar_beneficiario(client, token_a, polo_a_id)

    upload = client.post(
        f"/api/v1/beneficiarios/{beneficiario['id']}/documentos",
        files={"identidade_responsavel": ("rg.png", b"conteudo-imagem", "image/png")},
        headers={"Authorization": f"Bearer {token_a}"},
    ).json()

    resp = client.get(
        f"/api/v1/beneficiarios/documentos/{upload[0]['id']}/arquivo",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403
