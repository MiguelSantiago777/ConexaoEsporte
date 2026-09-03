"""Testes do perfil COORDENADOR_ALMOXARIFADO: só tem acesso ao próprio
almoxarifado (mesmo padrão de escopo já usado pro GESTOR_POLO com polo_id),
consegue registrar Entrada de estoque nele, consultar seus produtos/saldos/
movimentações/relatório, e não acessa nenhuma outra área do sistema."""
import shutil
from pathlib import Path

import pytest

from tests.conftest import login


@pytest.fixture(autouse=True)
def _limpar_uploads_teste():
    yield
    shutil.rmtree(Path("uploads/estoque"), ignore_errors=True)


def _criar_almoxarifado(client, token_master, nome="Almoxarifado Central"):
    resp = client.post("/api/v1/almoxarifados", json={"nome": nome}, headers={"Authorization": f"Bearer {token_master}"})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _criar_produto(client, token_master, nome="Bola de futebol"):
    resp = client.post(
        "/api/v1/produtos", json={"nome": nome, "unidade_medida": "unidade"},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _criar_coordenador(client, token_master, almoxarifado_id, email="coordenador@test.com"):
    resp = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Coordenador Teste", "email": email, "senha": "senha123",
            "perfil": "COORDENADOR_ALMOXARIFADO", "almoxarifado_id": almoxarifado_id,
        },
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_master_cria_coordenador_vinculado_a_um_almoxarifado(client, seed_basico):
    token_master = login(client, "master@test.com")
    almoxarifado = _criar_almoxarifado(client, token_master)
    coordenador = _criar_coordenador(client, token_master, almoxarifado["id"])
    assert coordenador["perfil"] == "COORDENADOR_ALMOXARIFADO"
    assert coordenador["almoxarifado_id"] == almoxarifado["id"]


def test_criar_coordenador_sem_almoxarifado_id_e_recusado(client, seed_basico):
    token_master = login(client, "master@test.com")
    resp = client.post(
        "/api/v1/usuarios",
        json={"nome": "Sem Almoxarifado", "email": "sem@test.com", "senha": "senha123", "perfil": "COORDENADOR_ALMOXARIFADO"},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 400


def test_coordenador_registra_entrada_so_no_proprio_almoxarifado(client, seed_basico):
    token_master = login(client, "master@test.com")
    almox_proprio = _criar_almoxarifado(client, token_master, nome="Almoxarifado do Coordenador")
    almox_outro = _criar_almoxarifado(client, token_master, nome="Outro Almoxarifado")
    produto = _criar_produto(client, token_master)
    _criar_coordenador(client, token_master, almox_proprio["id"])

    token_coord = login(client, "coordenador@test.com")

    resp_proprio = client.post(
        "/api/v1/movimentos-estoque",
        data={"produto_id": produto["id"], "almoxarifado_id": almox_proprio["id"], "quantidade": "10", "data": "2026-03-01"},
        files={"arquivo": ("nota.pdf", b"conteudo", "application/pdf")},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp_proprio.status_code == 201, resp_proprio.text

    resp_outro = client.post(
        "/api/v1/movimentos-estoque",
        data={"produto_id": produto["id"], "almoxarifado_id": almox_outro["id"], "quantidade": "10", "data": "2026-03-01"},
        files={"arquivo": ("nota.pdf", b"conteudo", "application/pdf")},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp_outro.status_code == 403


def test_coordenador_lista_movimentos_restrita_ao_proprio_almoxarifado_mesmo_sem_filtrar(client, seed_basico):
    token_master = login(client, "master@test.com")
    almox_proprio = _criar_almoxarifado(client, token_master, nome="Almoxarifado do Coordenador")
    almox_outro = _criar_almoxarifado(client, token_master, nome="Outro Almoxarifado")
    produto = _criar_produto(client, token_master)
    _criar_coordenador(client, token_master, almox_proprio["id"])

    # MASTER lança entradas nos dois almoxarifados.
    for almox in (almox_proprio, almox_outro):
        client.post(
            "/api/v1/movimentos-estoque",
            data={"produto_id": produto["id"], "almoxarifado_id": almox["id"], "quantidade": "5", "data": "2026-03-01"},
            files={"arquivo": ("nota.pdf", b"conteudo", "application/pdf")},
            headers={"Authorization": f"Bearer {token_master}"},
        )

    token_coord = login(client, "coordenador@test.com")
    # Mesmo pedindo o outro almoxarifado explicitamente, o escopo é forçado pro próprio.
    resp = client.get(
        "/api/v1/movimentos-estoque", params={"almoxarifado_id": almox_outro["id"]},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 200
    movimentos = resp.json()
    assert len(movimentos) == 1
    assert movimentos[0]["almoxarifado_id"] == almox_proprio["id"]


def test_coordenador_nao_acessa_outras_areas_do_sistema(client, seed_basico):
    token_master = login(client, "master@test.com")
    almoxarifado = _criar_almoxarifado(client, token_master)
    _criar_coordenador(client, token_master, almoxarifado["id"])
    token_coord = login(client, "coordenador@test.com")

    # Nota: GET /polos e GET /modalidades são abertos a qualquer usuário
    # autenticado (pré-existente, não é escopo deste teste) — a restrição
    # real do Coordenador é não conseguir ver/cadastrar/editar nada fora do
    # próprio almoxarifado nas áreas que de fato são restritas por perfil.
    assert client.get("/api/v1/beneficiarios", headers={"Authorization": f"Bearer {token_coord}"}).status_code == 403
    assert client.get("/api/v1/turmas", headers={"Authorization": f"Bearer {token_coord}"}).status_code == 403
    assert client.get("/api/v1/entregas-materiais", headers={"Authorization": f"Bearer {token_coord}"}).status_code == 403
    assert client.get("/api/v1/fichas-execucao", headers={"Authorization": f"Bearer {token_coord}"}).status_code == 403


def test_coordenador_nao_acessa_almoxarifado_de_outro_coordenador(client, seed_basico):
    token_master = login(client, "master@test.com")
    almox_a = _criar_almoxarifado(client, token_master, nome="Almoxarifado A")
    almox_b = _criar_almoxarifado(client, token_master, nome="Almoxarifado B")
    _criar_coordenador(client, token_master, almox_a["id"], email="coord.a@test.com")
    _criar_coordenador(client, token_master, almox_b["id"], email="coord.b@test.com")

    token_coord_a = login(client, "coord.a@test.com")
    resp = client.get(f"/api/v1/almoxarifados/{almox_b['id']}", headers={"Authorization": f"Bearer {token_coord_a}"})
    assert resp.status_code == 403

    resp_proprio = client.get(f"/api/v1/almoxarifados/{almox_a['id']}", headers={"Authorization": f"Bearer {token_coord_a}"})
    assert resp_proprio.status_code == 200


def test_me_retorna_almoxarifado_vinculado_do_coordenador(client, seed_basico):
    token_master = login(client, "master@test.com")
    almoxarifado = _criar_almoxarifado(client, token_master, nome="Almoxarifado do Coordenador")
    _criar_coordenador(client, token_master, almoxarifado["id"])
    token_coord = login(client, "coordenador@test.com")

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_coord}"})
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["perfil"] == "COORDENADOR_ALMOXARIFADO"
    assert corpo["almoxarifado_id"] == almoxarifado["id"]
    assert corpo["almoxarifado_nome"] == "Almoxarifado do Coordenador"


def test_relatorio_de_estoque_do_coordenador_e_restrito_ao_proprio_almoxarifado(client, seed_basico):
    token_master = login(client, "master@test.com")
    almox_proprio = _criar_almoxarifado(client, token_master, nome="Almoxarifado do Coordenador")
    almox_outro = _criar_almoxarifado(client, token_master, nome="Outro Almoxarifado")
    produto = _criar_produto(client, token_master, nome="Cone de treino")
    _criar_coordenador(client, token_master, almox_proprio["id"])

    for almox, quantidade in ((almox_proprio, "20"), (almox_outro, "100")):
        client.post(
            "/api/v1/movimentos-estoque",
            data={"produto_id": produto["id"], "almoxarifado_id": almox["id"], "quantidade": quantidade, "data": "2026-03-05"},
            files={"arquivo": ("nota.pdf", b"conteudo", "application/pdf")},
            headers={"Authorization": f"Bearer {token_master}"},
        )

    token_coord = login(client, "coordenador@test.com")
    resp = client.get(
        "/api/v1/movimentos-estoque/relatorio", params={"data_inicio": "2026-03-01", "data_fim": "2026-03-31"},
        headers={"Authorization": f"Bearer {token_coord}"},
    )
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["total_entradas_periodo"] == 20
    saldo_produto = next(s for s in corpo["saldos"] if s["produto_id"] == produto["id"])
    assert saldo_produto["saldo_atual"] == 20


def test_saldos_do_almoxarifado_endpoint_lista_produtos_do_coordenador(client, seed_basico):
    token_master = login(client, "master@test.com")
    almoxarifado = _criar_almoxarifado(client, token_master, nome="Almoxarifado do Coordenador")
    produto = _criar_produto(client, token_master, nome="Colete")
    _criar_coordenador(client, token_master, almoxarifado["id"])

    client.post(
        "/api/v1/movimentos-estoque",
        data={"produto_id": produto["id"], "almoxarifado_id": almoxarifado["id"], "quantidade": "15", "data": "2026-03-01"},
        files={"arquivo": ("nota.pdf", b"conteudo", "application/pdf")},
        headers={"Authorization": f"Bearer {token_master}"},
    )

    token_coord = login(client, "coordenador@test.com")
    resp = client.get(f"/api/v1/almoxarifados/{almoxarifado['id']}/saldos", headers={"Authorization": f"Bearer {token_coord}"})
    assert resp.status_code == 200, resp.text
    saldos = resp.json()
    assert len(saldos) == 1
    assert saldos[0]["produto_id"] == produto["id"]
    assert saldos[0]["saldo"] == 15
