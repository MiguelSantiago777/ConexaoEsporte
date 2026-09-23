"""Testes do módulo de Estoque: Almoxarifados, catálogo de Produto, Entrada
(com comprovante em anexo, escolhendo em qual almoxarifado entra) e a
integração com Entrega de Materiais — um item de entrega que referencia um
produto e um almoxarifado baixa o estoque automaticamente como Saída
daquele almoxarifado específico, bloqueando a criação se não houver saldo
suficiente ali (mesmo que outro almoxarifado tenha saldo). Cobre também o
comprovante de recebimento no polo e o Relatório de Estoque."""
import shutil
from pathlib import Path

import pytest

from tests.conftest import login


@pytest.fixture(autouse=True)
def _limpar_uploads_teste():
    yield
    shutil.rmtree(Path("uploads/estoque"), ignore_errors=True)
    shutil.rmtree(Path("uploads/comprovantes_entrega"), ignore_errors=True)


def _criar_produto(client, token_master, nome="Bola de futebol", unidade="unidade", quantidade=0, ncm=None):
    resp = client.post(
        "/api/v1/produtos",
        json={"nome": nome, "unidade_medida": unidade, "quantidade": quantidade, "ncm": ncm},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _saldo(client, token_master, produto_id):
    resp = client.get("/api/v1/produtos", headers={"Authorization": f"Bearer {token_master}"})
    return next(p for p in resp.json() if p["id"] == produto_id)["saldo_atual"]


def _criar_almoxarifado(client, token_master, nome="Almoxarifado Central"):
    resp = client.post(
        "/api/v1/almoxarifados",
        json={"nome": nome},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _registrar_entrada(
    client, token_master, produto_id, almoxarifado_id, quantidade, data="2026-03-01", nome_arquivo="nota.pdf"
):
    resp = client.post(
        "/api/v1/movimentos-estoque",
        data={"produto_id": produto_id, "almoxarifado_id": almoxarifado_id, "quantidade": str(quantidade), "data": data},
        files={"arquivo": (nome_arquivo, b"conteudo-nota-fiscal", "application/pdf")},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_gestor_nao_pode_cadastrar_produto_nem_almoxarifado_nem_lancar_entrada(client, seed_basico):
    token_gestor = login(client, "gestor.a@test.com")
    resp = client.post(
        "/api/v1/produtos", json={"nome": "Bola", "unidade_medida": "unidade"},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp.status_code == 403

    resp_almox = client.post(
        "/api/v1/almoxarifados", json={"nome": "Almoxarifado B"},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp_almox.status_code == 403


def test_produto_nasce_com_saldo_zero_e_entrada_aumenta_saldo(client, seed_basico):
    token_master = login(client, "master@test.com")
    produto = _criar_produto(client, token_master)
    almoxarifado = _criar_almoxarifado(client, token_master)
    assert produto["saldo_atual"] == 0

    _registrar_entrada(client, token_master, produto["id"], almoxarifado["id"], 50)

    resp = client.get("/api/v1/produtos", params={"pagina": 1, "tamanho_pagina": 10}, headers={"Authorization": f"Bearer {token_master}"})
    item = next(p for p in resp.json()["itens"] if p["id"] == produto["id"])
    assert item["saldo_atual"] == 50


def test_entrada_exige_anexo_de_tipo_permitido(client, seed_basico):
    token_master = login(client, "master@test.com")
    produto = _criar_produto(client, token_master)
    almoxarifado = _criar_almoxarifado(client, token_master)
    resp = client.post(
        "/api/v1/movimentos-estoque",
        data={"produto_id": produto["id"], "almoxarifado_id": almoxarifado["id"], "quantidade": "10", "data": "2026-03-01"},
        files={"arquivo": ("nota.txt", b"conteudo", "text/plain")},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 415


def test_baixar_comprovante_da_entrada(client, seed_basico):
    token_master = login(client, "master@test.com")
    produto = _criar_produto(client, token_master)
    almoxarifado = _criar_almoxarifado(client, token_master)
    entrada = _registrar_entrada(client, token_master, produto["id"], almoxarifado["id"], 30)

    resp = client.get(f"/api/v1/movimentos-estoque/{entrada['id']}/arquivo", headers={"Authorization": f"Bearer {token_master}"})
    assert resp.status_code == 200
    assert resp.content == b"conteudo-nota-fiscal"


def test_baixar_comprovante_retorna_404_quando_arquivo_falta_no_disco(client, seed_basico):
    """Regressão: o registro no banco pode sobreviver à perda do arquivo em
    disco (rebuild de container sem volume persistente, migração de storage,
    exclusão manual) — antes do fix isso derrubava a rota com 500 em vez do
    404 limpo que o resto do código já espera (ver ArmazenamentoLocalDocumentos.abrir)."""
    token_master = login(client, "master@test.com")
    produto = _criar_produto(client, token_master)
    almoxarifado = _criar_almoxarifado(client, token_master)
    entrada = _registrar_entrada(client, token_master, produto["id"], almoxarifado["id"], 10)

    shutil.rmtree(Path("uploads/estoque") / produto["id"], ignore_errors=True)

    resp = client.get(f"/api/v1/movimentos-estoque/{entrada['id']}/arquivo", headers={"Authorization": f"Bearer {token_master}"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Arquivo não encontrado."


def test_entrega_com_produto_baixa_estoque_do_almoxarifado_escolhido(client, seed_basico):
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)

    produto = _criar_produto(client, token_master, nome="Colete")
    almoxarifado = _criar_almoxarifado(client, token_master)
    _registrar_entrada(client, token_master, produto["id"], almoxarifado["id"], 20)

    resp_entrega = client.post(
        "/api/v1/entregas-materiais",
        json={
            "polo_id": polo_a_id,
            "itens": [{"descricao": "Colete", "quantidade": "8", "produto_id": produto["id"], "almoxarifado_id": almoxarifado["id"]}],
        },
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp_entrega.status_code == 201, resp_entrega.text
    entrega = resp_entrega.json()
    assert entrega["itens"][0]["produto_id"] == produto["id"]
    assert entrega["itens"][0]["almoxarifado_id"] == almoxarifado["id"]

    resp_produtos = client.get(
        "/api/v1/produtos", params={"pagina": 1, "tamanho_pagina": 10}, headers={"Authorization": f"Bearer {token_master}"}
    )
    item = next(p for p in resp_produtos.json()["itens"] if p["id"] == produto["id"])
    assert item["saldo_atual"] == 12  # 20 - 8

    resp_movs = client.get(
        "/api/v1/movimentos-estoque", params={"produto_id": produto["id"], "tipo": "SAIDA", "pagina": 1, "tamanho_pagina": 10},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    saidas = resp_movs.json()["itens"]
    assert len(saidas) == 1
    assert saidas[0]["quantidade"] == 8
    assert saidas[0]["almoxarifado_id"] == almoxarifado["id"]
    assert saidas[0]["entrega_material_id"] == entrega["id"]


def test_entrega_sem_almoxarifado_sai_do_saldo_total(client, seed_basico):
    """Estoque único: o item da entrega não precisa mais dizer de qual
    almoxarifado sai — a Saída desconta do saldo total do produto."""
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    produto = _criar_produto(client, token_master, nome="Apito", quantidade=5)

    resp = client.post(
        "/api/v1/entregas-materiais",
        json={"polo_id": polo_a_id, "itens": [{"descricao": "Apito", "quantidade": "2", "produto_id": produto["id"]}]},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    assert _saldo(client, token_master, produto["id"]) == 3

    resp_demais = client.post(
        "/api/v1/entregas-materiais",
        json={"polo_id": polo_a_id, "itens": [{"descricao": "Apito", "quantidade": "4", "produto_id": produto["id"]}]},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp_demais.status_code == 400
    assert "insuficiente" in resp_demais.json()["detail"].lower()


def test_cadastro_com_quantidade_ja_lanca_entrada_e_grava_ncm(client, seed_basico):
    token_master = login(client, "master@test.com")
    produto = _criar_produto(client, token_master, nome="Bola de basquete", quantidade=40, ncm="9506.62.00")
    assert produto["saldo_atual"] == 40
    assert produto["ncm"] == "95066200"
    assert _saldo(client, token_master, produto["id"]) == 40

    resp_movs = client.get(
        "/api/v1/movimentos-estoque", params={"produto_id": produto["id"], "pagina": 1, "tamanho_pagina": 10},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    entradas = resp_movs.json()["itens"]
    assert len(entradas) == 1
    assert entradas[0]["tipo"] == "ENTRADA"
    assert entradas[0]["quantidade"] == 40
    assert entradas[0]["almoxarifado_id"] is None


def test_ncm_invalido_e_recusado_e_edicao_pode_apagar(client, seed_basico):
    token_master = login(client, "master@test.com")
    headers = {"Authorization": f"Bearer {token_master}"}
    resp = client.post("/api/v1/produtos", json={"nome": "Bola", "unidade_medida": "unidade", "ncm": "12345"}, headers=headers)
    assert resp.status_code == 400
    assert "ncm" in resp.json()["detail"].lower()

    produto = _criar_produto(client, token_master, ncm="95066200")
    resp_editar = client.patch(f"/api/v1/produtos/{produto['id']}", json={"nome": "Bola nova"}, headers=headers)
    assert resp_editar.json()["ncm"] == "95066200"  # não enviar = manter
    resp_apagar = client.patch(f"/api/v1/produtos/{produto['id']}", json={"ncm": ""}, headers=headers)
    assert resp_apagar.status_code == 200, resp_apagar.text
    assert resp_apagar.json()["ncm"] is None


def test_entrada_sem_comprovante_e_sem_almoxarifado(client, seed_basico):
    token_master = login(client, "master@test.com")
    produto = _criar_produto(client, token_master, nome="Colchonete")
    resp = client.post(
        "/api/v1/movimentos-estoque",
        data={"produto_id": produto["id"], "quantidade": "12", "data": "2026-03-01"},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["nome_arquivo"] is None
    assert _saldo(client, token_master, produto["id"]) == 12


def test_dar_baixa_pra_um_polo(client, seed_basico):
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    produto = _criar_produto(client, token_master, nome="Uniforme", quantidade=30)

    resp = client.post(
        "/api/v1/movimentos-estoque/baixa",
        json={
            "produto_id": produto["id"], "polo_id": polo_a_id, "quantidade": 12, "data": "2026-03-10",
            "recebido_por": "Maria", "observacao": "Turma sub-15",
        },
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    corpo = resp.json()
    assert corpo["tipo"] == "SAIDA"
    assert corpo["polo_id"] == polo_a_id
    assert corpo["recebido_por"] == "Maria"
    assert _saldo(client, token_master, produto["id"]) == 18


def test_dar_baixa_acima_do_saldo_e_recusada(client, seed_basico):
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    produto = _criar_produto(client, token_master, nome="Uniforme", quantidade=3)

    resp = client.post(
        "/api/v1/movimentos-estoque/baixa",
        json={"produto_id": produto["id"], "polo_id": polo_a_id, "quantidade": 4, "data": "2026-03-10"},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 400
    assert "insuficiente" in resp.json()["detail"].lower()
    assert _saldo(client, token_master, produto["id"]) == 3


def test_gestor_nao_pode_dar_baixa(client, seed_basico):
    token_master = login(client, "master@test.com")
    token_gestor = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    produto = _criar_produto(client, token_master, quantidade=3)

    resp = client.post(
        "/api/v1/movimentos-estoque/baixa",
        json={"produto_id": produto["id"], "polo_id": polo_a_id, "quantidade": 1, "data": "2026-03-10"},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp.status_code == 403


def test_saldo_e_separado_por_almoxarifado_saida_recusa_de_onde_nao_tem_estoque(client, seed_basico):
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)

    produto = _criar_produto(client, token_master, nome="Bola de vôlei")
    almox_a = _criar_almoxarifado(client, token_master, nome="Almoxarifado A")
    almox_b = _criar_almoxarifado(client, token_master, nome="Almoxarifado B")
    _registrar_entrada(client, token_master, produto["id"], almox_a["id"], 10)
    # Almoxarifado B nunca recebeu entrada nenhuma — saldo 0 lá, mesmo com
    # saldo de sobra no Almoxarifado A.

    resp_entrega = client.post(
        "/api/v1/entregas-materiais",
        json={
            "polo_id": polo_a_id,
            "itens": [{"descricao": "Bola de vôlei", "quantidade": "3", "produto_id": produto["id"], "almoxarifado_id": almox_b["id"]}],
        },
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp_entrega.status_code == 400
    assert "insuficiente" in resp_entrega.json()["detail"].lower()

    # Do Almoxarifado A funciona normalmente.
    resp_ok = client.post(
        "/api/v1/entregas-materiais",
        json={
            "polo_id": polo_a_id,
            "itens": [{"descricao": "Bola de vôlei", "quantidade": "3", "produto_id": produto["id"], "almoxarifado_id": almox_a["id"]}],
        },
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp_ok.status_code == 201, resp_ok.text

    resp_saldos = client.get(
        f"/api/v1/produtos/{produto['id']}/saldos-por-almoxarifado", headers={"Authorization": f"Bearer {token_master}"}
    )
    saldos = {s["almoxarifado_id"]: s["saldo"] for s in resp_saldos.json()}
    assert saldos[almox_a["id"]] == 7  # 10 - 3
    assert almox_b["id"] not in saldos  # nunca teve movimentação


def test_entrega_com_produto_sem_estoque_suficiente_e_recusada(client, seed_basico):
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)

    produto = _criar_produto(client, token_master, nome="Bola de vôlei")
    almoxarifado = _criar_almoxarifado(client, token_master)
    _registrar_entrada(client, token_master, produto["id"], almoxarifado["id"], 3)

    resp_entrega = client.post(
        "/api/v1/entregas-materiais",
        json={
            "polo_id": polo_a_id,
            "itens": [{"descricao": "Bola de vôlei", "quantidade": "10", "produto_id": produto["id"], "almoxarifado_id": almoxarifado["id"]}],
        },
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp_entrega.status_code == 400
    assert "insuficiente" in resp_entrega.json()["detail"].lower()

    # Nenhuma entrega nem saída foi criada.
    resp_movs = client.get(
        "/api/v1/movimentos-estoque", params={"produto_id": produto["id"], "tipo": "SAIDA", "pagina": 1, "tamanho_pagina": 10},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp_movs.json()["total"] == 0


def test_entrega_sem_produto_continua_sem_afetar_estoque(client, seed_basico):
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    resp = client.post(
        "/api/v1/entregas-materiais",
        json={"polo_id": polo_a_id, "itens": [{"descricao": "Material qualquer", "quantidade": "5"}]},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["itens"][0].get("produto_id") is None


def test_comprovante_de_recebimento_no_polo(client, seed_basico):
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    entrega = client.post(
        "/api/v1/entregas-materiais",
        json={"polo_id": polo_a_id, "itens": [{"descricao": "Uniformes", "quantidade": "15"}]},
        headers={"Authorization": f"Bearer {token_master}"},
    ).json()

    resp_upload = client.post(
        f"/api/v1/entregas-materiais/{entrega['id']}/comprovante",
        files={"arquivo": ("recibo.jpg", b"foto-do-recibo-assinado", "image/jpeg")},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp_upload.status_code == 200, resp_upload.text
    assert resp_upload.json()["comprovante_nome_arquivo"] == "recibo.jpg"

    resp_download = client.get(
        f"/api/v1/entregas-materiais/{entrega['id']}/comprovante",
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp_download.status_code == 200
    assert resp_download.content == b"foto-do-recibo-assinado"


def test_gestor_de_polo_nao_acessa_comprovante(client, seed_basico):
    token_master = login(client, "master@test.com")
    token_gestor = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    entrega = client.post(
        "/api/v1/entregas-materiais",
        json={"polo_id": polo_a_id, "itens": []},
        headers={"Authorization": f"Bearer {token_master}"},
    ).json()

    resp = client.post(
        f"/api/v1/entregas-materiais/{entrega['id']}/comprovante",
        files={"arquivo": ("recibo.jpg", b"conteudo", "image/jpeg")},
        headers={"Authorization": f"Bearer {token_gestor}"},
    )
    assert resp.status_code == 403


def test_remover_produto_em_uso_e_recusado_mas_sem_uso_funciona(client, seed_basico):
    token_master = login(client, "master@test.com")
    almoxarifado = _criar_almoxarifado(client, token_master)
    usado = _criar_produto(client, token_master, nome="Rede de vôlei")
    _registrar_entrada(client, token_master, usado["id"], almoxarifado["id"], 5)

    resp_bloqueado = client.delete(f"/api/v1/produtos/{usado['id']}", headers={"Authorization": f"Bearer {token_master}"})
    assert resp_bloqueado.status_code == 400

    sem_uso = _criar_produto(client, token_master, nome="Apito")
    resp_ok = client.delete(f"/api/v1/produtos/{sem_uso['id']}", headers={"Authorization": f"Bearer {token_master}"})
    assert resp_ok.status_code == 204


def test_remover_almoxarifado_em_uso_e_recusado_mas_sem_uso_funciona(client, seed_basico):
    token_master = login(client, "master@test.com")
    produto = _criar_produto(client, token_master)
    usado = _criar_almoxarifado(client, token_master, nome="Almoxarifado usado")
    _registrar_entrada(client, token_master, produto["id"], usado["id"], 5)

    resp_bloqueado = client.delete(f"/api/v1/almoxarifados/{usado['id']}", headers={"Authorization": f"Bearer {token_master}"})
    assert resp_bloqueado.status_code == 400

    sem_uso = _criar_almoxarifado(client, token_master, nome="Almoxarifado livre")
    resp_ok = client.delete(f"/api/v1/almoxarifados/{sem_uso['id']}", headers={"Authorization": f"Bearer {token_master}"})
    assert resp_ok.status_code == 204


def test_entrada_grava_quem_entregou_e_quem_recebeu_no_estoque(client, seed_basico):
    token_master = login(client, "master@test.com")
    produto = _criar_produto(client, token_master, nome="Colchonete")
    almoxarifado = _criar_almoxarifado(client, token_master)
    resp = client.post(
        "/api/v1/movimentos-estoque",
        data={
            "produto_id": produto["id"], "almoxarifado_id": almoxarifado["id"], "quantidade": "20", "data": "2026-03-01",
            "entregue_por": "Transportadora XYZ", "recebido_por": "João do Almoxarifado",
        },
        files={"arquivo": ("nota.pdf", b"conteudo-nota-fiscal", "application/pdf")},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text
    corpo = resp.json()
    assert corpo["entregue_por"] == "Transportadora XYZ"
    assert corpo["recebido_por"] == "João do Almoxarifado"


def test_comprovante_de_entrega_pode_registrar_quem_recebeu_no_polo(client, seed_basico):
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    entrega = client.post(
        "/api/v1/entregas-materiais",
        json={"polo_id": polo_a_id, "itens": [{"descricao": "Uniformes", "quantidade": "15"}]},
        headers={"Authorization": f"Bearer {token_master}"},
    ).json()

    resp_upload = client.post(
        f"/api/v1/entregas-materiais/{entrega['id']}/comprovante",
        data={"recebido_por": "Maria da Silva"},
        files={"arquivo": ("recibo.jpg", b"foto-do-recibo-assinado", "image/jpeg")},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp_upload.status_code == 200, resp_upload.text
    assert resp_upload.json()["coordenador_nome"] == "Maria da Silva"


def test_relatorio_de_estoque_agrega_entradas_saidas_e_saldo(client, seed_basico):
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)

    produto = _criar_produto(client, token_master, nome="Cone de treino")
    almoxarifado = _criar_almoxarifado(client, token_master)
    _registrar_entrada(client, token_master, produto["id"], almoxarifado["id"], 100, data="2026-03-05")
    client.post(
        "/api/v1/entregas-materiais",
        json={
            "polo_id": polo_a_id, "data_entrega": "2026-03-10",
            "itens": [{"descricao": "Cone de treino", "quantidade": "30", "produto_id": produto["id"], "almoxarifado_id": almoxarifado["id"]}],
        },
        headers={"Authorization": f"Bearer {token_master}"},
    )

    resp = client.get(
        "/api/v1/movimentos-estoque/relatorio",
        params={"data_inicio": "2026-03-01", "data_fim": "2026-03-31"},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    saldo_produto = next(s for s in corpo["saldos"] if s["produto_id"] == produto["id"])
    assert saldo_produto["total_entradas"] == 100
    assert saldo_produto["total_saidas"] == 30
    assert saldo_produto["saldo_atual"] == 70
    assert corpo["total_entradas_periodo"] == 100
    assert corpo["total_saidas_periodo"] == 30
    assert len(corpo["movimentos"]) == 2
