"""
Testes de Entrega de Materiais (Termo de Entrega de Materiais) e do Termo
de Responsabilidade — ambos exportados em .docx, no layout oficial do
modelo. Cobre:
- RBAC: MASTER e COORDENADOR_ALMOXARIFADO — GESTOR_POLO não cadastra/
  exporta entregas, nem mesmo do próprio polo.
- Coordenador só despacha itens do próprio almoxarifado, e só enxerga/
  exporta/edita as entregas que ele mesmo criou (nunca as de outro
  coordenador) — MASTER continua com acesso irrestrito a tudo.
- A entrega nasce com o coordenador copiado do responsável do polo.
- O termo de entrega e o termo de responsabilidade trazem os dados
  cadastrados (do polo/entrega) nos parágrafos e células certas.
"""
import io
import shutil
from pathlib import Path

import docx
import pytest

from tests.conftest import login


@pytest.fixture(autouse=True)
def _limpar_uploads_teste():
    yield
    shutil.rmtree(Path("uploads/comprovantes_entrega"), ignore_errors=True)


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


def _registrar_entrada(client, token_master, produto_id, almoxarifado_id, quantidade):
    resp = client.post(
        "/api/v1/movimentos-estoque",
        data={"produto_id": produto_id, "almoxarifado_id": almoxarifado_id, "quantidade": str(quantidade), "data": "2026-03-01"},
        files={"arquivo": ("nota.pdf", b"conteudo", "application/pdf")},
        headers={"Authorization": f"Bearer {token_master}"},
    )
    assert resp.status_code == 201, resp.text


def test_gestor_de_polo_nao_cria_entrega(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    resp = client.post(
        "/api/v1/entregas-materiais",
        json={"polo_id": polo_a_id, "itens": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_coordenador_cria_entrega_so_com_itens_do_proprio_almoxarifado(client, seed_basico):
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    almox_proprio = _criar_almoxarifado(client, token_master, nome="Almoxarifado do Coordenador")
    almox_outro = _criar_almoxarifado(client, token_master, nome="Outro Almoxarifado")
    produto = _criar_produto(client, token_master)
    _registrar_entrada(client, token_master, produto["id"], almox_proprio["id"], 20)
    _registrar_entrada(client, token_master, produto["id"], almox_outro["id"], 20)
    _criar_coordenador(client, token_master, almox_proprio["id"])

    token_coord = login(client, "coordenador@test.com")
    headers_coord = {"Authorization": f"Bearer {token_coord}"}

    resp_ok = client.post(
        "/api/v1/entregas-materiais",
        json={
            "polo_id": polo_a_id,
            "itens": [{"descricao": produto["nome"], "quantidade": "10", "produto_id": produto["id"], "almoxarifado_id": almox_proprio["id"]}],
        },
        headers=headers_coord,
    )
    assert resp_ok.status_code == 201, resp_ok.text

    resp_negado = client.post(
        "/api/v1/entregas-materiais",
        json={
            "polo_id": polo_a_id,
            "itens": [{"descricao": produto["nome"], "quantidade": "5", "produto_id": produto["id"], "almoxarifado_id": almox_outro["id"]}],
        },
        headers=headers_coord,
    )
    assert resp_negado.status_code == 403


def test_coordenador_so_ve_e_acessa_as_proprias_entregas(client, seed_basico):
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    almox_a = _criar_almoxarifado(client, token_master, nome="Almoxarifado A")
    almox_b = _criar_almoxarifado(client, token_master, nome="Almoxarifado B")
    _criar_coordenador(client, token_master, almox_a["id"], email="coord.a@test.com")
    _criar_coordenador(client, token_master, almox_b["id"], email="coord.b@test.com")

    token_coord_a = login(client, "coord.a@test.com")
    token_coord_b = login(client, "coord.b@test.com")

    entrega_a = client.post(
        "/api/v1/entregas-materiais",
        json={"polo_id": polo_a_id, "itens": [{"descricao": "Kit livre", "quantidade": "3"}]},
        headers={"Authorization": f"Bearer {token_coord_a}"},
    ).json()

    # Coordenador B não vê a entrega do Coordenador A na listagem...
    resp_lista_b = client.get("/api/v1/entregas-materiais", headers={"Authorization": f"Bearer {token_coord_b}"})
    assert resp_lista_b.status_code == 200
    assert all(e["id"] != entrega_a["id"] for e in resp_lista_b.json())

    # ...nem acessa por ID direto (buscar, exportar ou anexar comprovante).
    assert client.get(f"/api/v1/entregas-materiais/{entrega_a['id']}", headers={"Authorization": f"Bearer {token_coord_b}"}).status_code == 403
    assert client.get(f"/api/v1/entregas-materiais/{entrega_a['id']}/exportar", headers={"Authorization": f"Bearer {token_coord_b}"}).status_code == 403

    # Coordenador A enxerga e exporta a própria entrega normalmente.
    resp_lista_a = client.get("/api/v1/entregas-materiais", headers={"Authorization": f"Bearer {token_coord_a}"})
    assert any(e["id"] == entrega_a["id"] for e in resp_lista_a.json())
    assert client.get(f"/api/v1/entregas-materiais/{entrega_a['id']}/exportar", headers={"Authorization": f"Bearer {token_coord_a}"}).status_code == 200

    # MASTER continua vendo tudo, sem filtro nenhum.
    token_master_check = login(client, "master@test.com")
    resp_lista_master = client.get("/api/v1/entregas-materiais", headers={"Authorization": f"Bearer {token_master_check}"})
    assert any(e["id"] == entrega_a["id"] for e in resp_lista_master.json())


def test_coordenador_confirma_recebimento_da_propria_entrega(client, seed_basico):
    token_master = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    almoxarifado = _criar_almoxarifado(client, token_master)
    _criar_coordenador(client, token_master, almoxarifado["id"])
    token_coord = login(client, "coordenador@test.com")
    headers_coord = {"Authorization": f"Bearer {token_coord}"}

    entrega = client.post(
        "/api/v1/entregas-materiais",
        json={"polo_id": polo_a_id, "itens": [{"descricao": "Kit livre", "quantidade": "3"}]},
        headers=headers_coord,
    ).json()

    resp = client.post(
        f"/api/v1/entregas-materiais/{entrega['id']}/comprovante",
        data={"recebido_por": "Coordenador do Polo A"},
        files={"arquivo": ("comprovante.jpg", b"foto-assinada", "image/jpeg")},
        headers=headers_coord,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["comprovante_nome_arquivo"] == "comprovante.jpg"

    # O comprovante continua acessível ao MASTER (ex.: via Anexos Gerais).
    token_master_check = login(client, "master@test.com")
    resp_baixar = client.get(
        f"/api/v1/entregas-materiais/{entrega['id']}/comprovante", headers={"Authorization": f"Bearer {token_master_check}"}
    )
    assert resp_baixar.status_code == 200
    assert resp_baixar.content == b"foto-assinada"


def test_entrega_nasce_com_coordenador_do_polo(client, seed_basico):
    token_master = login(client, "master@test.com")
    headers_master = {"Authorization": f"Bearer {token_master}"}
    polo_a_id = str(seed_basico["polo_a"].id)
    client.patch(f"/api/v1/polos/{polo_a_id}", json={"responsavel_nome": "Coordenadora Fulana"}, headers=headers_master)

    resp = client.post(
        "/api/v1/entregas-materiais",
        json={
            "polo_id": polo_a_id, "data_entrega": "2026-03-01",
            "itens": [{"descricao": "Bolas de futebol", "quantidade": "10"}],
        },
        headers=headers_master,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["coordenador_nome"] == "Coordenadora Fulana"


def test_exportar_termo_entrega_reflete_itens_e_coordenador(client, seed_basico):
    token_master = login(client, "master@test.com")
    headers_master = {"Authorization": f"Bearer {token_master}"}
    polo_a_id = str(seed_basico["polo_a"].id)
    client.patch(f"/api/v1/polos/{polo_a_id}", json={"responsavel_nome": "Coordenadora Fulana"}, headers=headers_master)

    headers = headers_master
    entrega = client.post(
        "/api/v1/entregas-materiais",
        json={
            "polo_id": polo_a_id, "data_entrega": "2026-03-01",
            "itens": [
                {"descricao": "Bolas de futebol", "quantidade": "10"},
                {"descricao": "Coletes", "quantidade": "20"},
            ],
        },
        headers=headers,
    ).json()

    resp = client.get(f"/api/v1/entregas-materiais/{entrega['id']}/exportar", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    doc = docx.Document(io.BytesIO(resp.content))
    textos = [p.text for p in doc.paragraphs]
    assert any(t == "NÚCLEO: Polo A" for t in textos)
    assert any(t == "COORDENADOR: Coordenadora Fulana" for t in textos)

    tabela = doc.tables[0]
    assert tabela.cell(1, 0).text == "Bolas de futebol"
    assert tabela.cell(1, 1).text == "10"
    assert tabela.cell(2, 0).text == "Coletes"
    assert tabela.cell(2, 1).text == "20"


def test_exportar_termo_responsabilidade_reflete_dados_do_polo(client, seed_basico):
    token = login(client, "master@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    polo_a_id = str(seed_basico["polo_a"].id)
    client.patch(
        f"/api/v1/polos/{polo_a_id}",
        json={
            "representante_legal_nome": "Fulana de Tal",
            "representante_legal_cpf": "111.222.333-44",
            "representante_legal_rg": "12.345.678-9",
            "representante_legal_endereco": "Rua das Flores, 100",
            "representante_legal_bairro": "Centro",
            "representante_legal_cidade": "São Paulo",
        },
        headers=headers,
    )

    resp = client.get(f"/api/v1/polos/{polo_a_id}/termo-responsabilidade/exportar", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    doc = docx.Document(io.BytesIO(resp.content))
    texto_completo = "\n".join(p.text for p in doc.paragraphs)
    assert "Fulana de Tal" in texto_completo
    assert "RG nº 12.345.678-9" in texto_completo
    assert "CPF nº 111.222.333-44" in texto_completo
    assert "Rua das Flores, 100" in texto_completo
    assert "Bairro Centro" in texto_completo
    assert "Cidade São Paulo" in texto_completo
    assert any(p.text.startswith("São Paulo,") for p in doc.paragraphs)
