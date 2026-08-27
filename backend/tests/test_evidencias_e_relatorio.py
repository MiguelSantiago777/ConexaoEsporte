"""
Testes das fotos de evidência de aula (anexadas à chamada) e dos relatórios
gerenciais agregados (KPIs e séries para gráficos) de Polo e Geral.
"""
import shutil
from datetime import date
from pathlib import Path

import pytest

from tests.conftest import login


@pytest.fixture(autouse=True)
def _limpar_uploads_teste():
    yield
    shutil.rmtree(Path("uploads/evidencias"), ignore_errors=True)


def _criar_turma(client, token, polo_id, modalidade_id, professor_id=None):
    turma = client.post(
        "/api/v1/turmas",
        json={
            "polo_id": polo_id, "modalidade_id": modalidade_id,
            "horario_inicio": "08:00", "horario_fim": "09:00",
            "dias_semana": ["SEG"], "limite_vagas": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    if professor_id:
        client.patch(
            f"/api/v1/turmas/{turma['id']}", json={"professor_id": professor_id},
            headers={"Authorization": f"Bearer {token}"},
        )
    return turma


def _criar_beneficiario(client, token, polo_id, documento="000.111.222-33"):
    return client.post(
        "/api/v1/beneficiarios",
        json={
            "nome_completo": "Beneficiário Teste", "data_nascimento": "2000-01-01",
            "documento": documento, "polo_id": polo_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()


def _criar_professor(client, token_gestor, polo_id, email="prof.evid@test.com"):
    resp = client.post(
        "/api/v1/usuarios",
        json={"nome": "Professor Teste", "email": email, "senha": "senha123", "perfil": "PROFESSOR", "polo_id": polo_id},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _montar_cenario(client, seed_basico):
    """Polo A com 1 turma, 1 professor vinculado, 1 beneficiário matriculado
    e chamada lançada como presente na data de hoje."""
    token_gestor = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)

    professor = _criar_professor(client, token_gestor, polo_a_id)
    turma = _criar_turma(client, token_gestor, polo_a_id, modalidade_id, professor_id=professor["id"])
    beneficiario = _criar_beneficiario(client, token_gestor, polo_a_id)
    client.post(
        f"/api/v1/beneficiarios/{beneficiario['id']}/matriculas",
        json={"turma_id": turma["id"]},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )

    hoje = date.today().isoformat()
    token_prof = login(client, professor["email"])
    client.post(
        "/api/v1/frequencias/chamada",
        json={"turma_id": turma["id"], "data": hoje, "presencas": [{"beneficiario_id": beneficiario["id"], "presente": True}]},
        headers={"Authorization": f"Bearer {token_prof}"},
    )
    return {
        "polo_a_id": polo_a_id, "turma": turma, "professor": professor,
        "beneficiario": beneficiario, "hoje": hoje,
        "token_gestor": token_gestor, "token_prof": token_prof,
    }


def test_professor_anexa_e_lista_fotos_de_evidencia(client, seed_basico):
    cenario = _montar_cenario(client, seed_basico)

    resp = client.post(
        "/api/v1/frequencias/evidencias",
        data={"turma_id": cenario["turma"]["id"], "data": cenario["hoje"]},
        files=[
            ("arquivos", ("aula1.jpg", b"foto-fake-1", "image/jpeg")),
            ("arquivos", ("aula2.jpg", b"foto-fake-2", "image/jpeg")),
        ],
        headers={"Authorization": f"Bearer {cenario['token_prof']}"},
    )
    assert resp.status_code == 201, resp.text
    fotos = resp.json()
    assert len(fotos) == 2
    assert {f["nome_arquivo"] for f in fotos} == {"aula1.jpg", "aula2.jpg"}

    resp_lista = client.get(
        "/api/v1/frequencias/evidencias",
        params={"turma_id": cenario["turma"]["id"], "data": cenario["hoje"]},
        headers={"Authorization": f"Bearer {cenario['token_prof']}"},
    )
    assert resp_lista.status_code == 200
    assert len(resp_lista.json()) == 2

    resp_arquivo = client.get(
        f"/api/v1/frequencias/evidencias/{fotos[0]['id']}/arquivo",
        headers={"Authorization": f"Bearer {cenario['token_prof']}"},
    )
    assert resp_arquivo.status_code == 200
    assert resp_arquivo.content == b"foto-fake-1"
    assert resp_arquivo.headers["content-type"] == "image/jpeg"


def test_tipo_de_arquivo_nao_permitido_e_rejeitado(client, seed_basico):
    cenario = _montar_cenario(client, seed_basico)

    resp = client.post(
        "/api/v1/frequencias/evidencias",
        data={"turma_id": cenario["turma"]["id"], "data": cenario["hoje"]},
        files=[("arquivos", ("relatorio.pdf", b"conteudo", "application/pdf"))],
        headers={"Authorization": f"Bearer {cenario['token_prof']}"},
    )
    assert resp.status_code == 415


def test_professor_nao_vinculado_nao_anexa_evidencia_em_turma_alheia(client, seed_basico):
    cenario = _montar_cenario(client, seed_basico)
    outro_professor = _criar_professor(client, cenario["token_gestor"], cenario["polo_a_id"], email="outro.prof@test.com")
    token_outro = login(client, outro_professor["email"])

    resp = client.post(
        "/api/v1/frequencias/evidencias",
        data={"turma_id": cenario["turma"]["id"], "data": cenario["hoje"]},
        files=[("arquivos", ("aula1.jpg", b"foto-fake", "image/jpeg"))],
        headers={"Authorization": f"Bearer {token_outro}"},
    )
    assert resp.status_code == 403


def test_relatorio_polo_reflete_frequencia_e_beneficiarios_ativos(client, seed_basico):
    cenario = _montar_cenario(client, seed_basico)
    hoje = cenario["hoje"]

    resp = client.get(
        f"/api/v1/relatorios/polo/{cenario['polo_a_id']}",
        params={"data_inicio": hoje, "data_fim": hoje},
        headers={"Authorization": f"Bearer {cenario['token_gestor']}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["kpis"]["beneficiarios_ativos"] == 1
    assert body["kpis"]["turmas_ativas"] == 1
    assert body["kpis"]["frequencia_media_pct"] == 100.0
    assert body["kpis"]["aulas_registradas"] == 1
    assert len(body["beneficiarios_por_modalidade"]) == 1
    assert body["beneficiarios_por_modalidade"][0]["valor"] == 1


def test_gestor_de_outro_polo_nao_acessa_relatorio(client, seed_basico):
    cenario = _montar_cenario(client, seed_basico)
    token_b = login(client, "gestor.b@test.com")

    resp = client.get(
        f"/api/v1/relatorios/polo/{cenario['polo_a_id']}",
        params={"data_inicio": cenario["hoje"], "data_fim": cenario["hoje"]},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403


def test_professor_nao_acessa_relatorio_gerencial(client, seed_basico):
    cenario = _montar_cenario(client, seed_basico)

    resp = client.get(
        f"/api/v1/relatorios/polo/{cenario['polo_a_id']}",
        params={"data_inicio": cenario["hoje"], "data_fim": cenario["hoje"]},
        headers={"Authorization": f"Bearer {cenario['token_prof']}"},
    )
    assert resp.status_code == 403


def test_relatorio_geral_e_exclusivo_do_master(client, seed_basico):
    cenario = _montar_cenario(client, seed_basico)
    token_master = login(client, "master@test.com")

    resp = client.get(
        "/api/v1/relatorios/geral",
        params={"data_inicio": cenario["hoje"], "data_fim": cenario["hoje"]},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["kpis"]["total_polos"] == 2
    assert body["kpis"]["total_beneficiarios_ativos"] == 1
    assert len(body["ranking_polos"]) == 2

    resp_gestor = client.get(
        "/api/v1/relatorios/geral",
        params={"data_inicio": cenario["hoje"], "data_fim": cenario["hoje"]},
        headers={"Authorization": f"Bearer {cenario['token_gestor']}"},
    )
    assert resp_gestor.status_code == 403
