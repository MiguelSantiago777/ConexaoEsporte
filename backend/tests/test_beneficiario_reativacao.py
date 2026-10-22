"""
Testes da reativação de beneficiário "removido". Remover na tela só desativa
(`ativo=false`) — o registro continua no banco com o documento, que é único.
Antes, cadastrar de novo o mesmo CPF dava "Já existe um beneficiário com este
documento" mesmo sem ninguém aparecer na listagem nem nos relatórios. Agora o
cadastro reaproveita o registro desativado com os dados novos.
"""
from tests.conftest import login
from tests.test_importacao import _planilha, _upload
from tests.test_lista_espera import _inscrever
from tests.test_matriculas import _criar_turma


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _cadastrar(client, token, polo_id, documento, nome="Beneficiário Teste"):
    return client.post(
        "/api/v1/beneficiarios",
        json={"nome_completo": nome, "data_nascimento": "2000-01-01", "documento": documento, "polo_id": polo_id},
        headers=_headers(token),
    )


def _remover(client, token, beneficiario_id):
    resp = client.patch(f"/api/v1/beneficiarios/{beneficiario_id}", json={"ativo": False}, headers=_headers(token))
    assert resp.status_code == 200, resp.text


def _ativos(client, token):
    resp = client.get("/api/v1/beneficiarios", params={"pagina": 1}, headers=_headers(token))
    assert resp.status_code == 200, resp.text
    return resp.json()["itens"]


def test_cadastrar_documento_de_beneficiario_removido_reativa_com_dados_novos(client, seed_basico):
    token = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    polo_b_id = str(seed_basico["polo_b"].id)

    antigo = _cadastrar(client, token, polo_a_id, "12345678900", nome="Nome Antigo").json()
    _remover(client, token, antigo["id"])
    assert _ativos(client, token) == []

    resp = _cadastrar(client, token, polo_b_id, "12345678900", nome="Nome Novo")
    assert resp.status_code == 201, resp.text
    reativado = resp.json()
    assert reativado["id"] == antigo["id"]
    assert reativado["ativo"] is True
    assert reativado["nome_completo"] == "Nome Novo"
    assert reativado["polo_id"] == polo_b_id

    ativos = _ativos(client, token)
    assert [b["id"] for b in ativos] == [antigo["id"]]


def test_reativacao_nao_traz_de_volta_matriculas_antigas(client, seed_basico):
    token = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    turma = _criar_turma(client, token, polo_a_id, str(seed_basico["modalidade"].id))

    antigo = _cadastrar(client, token, polo_a_id, "98765432100").json()
    resp = client.post(
        f"/api/v1/beneficiarios/{antigo['id']}/matriculas", json={"turma_id": turma["id"]}, headers=_headers(token)
    )
    assert resp.status_code == 201, resp.text
    _remover(client, token, antigo["id"])

    assert _cadastrar(client, token, polo_a_id, "98765432100").status_code == 201

    matriculas = client.get(f"/api/v1/beneficiarios/{antigo['id']}/matriculas", headers=_headers(token)).json()
    assert len(matriculas) == 1  # histórico preservado
    assert matriculas[0]["ativo"] is False


def test_documento_de_beneficiario_ativo_continua_bloqueado(client, seed_basico):
    token = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)

    assert _cadastrar(client, token, polo_a_id, "11122233344").status_code == 201
    resp = _cadastrar(client, token, polo_a_id, "11122233344")
    assert resp.status_code == 409, resp.text


def test_aceitar_lista_espera_com_documento_de_removido_reativa(client, seed_basico, _sem_envio_real_de_email):
    token = login(client, "master@test.com")
    polo_a_id = str(seed_basico["polo_a"].id)
    modalidade_id = str(seed_basico["modalidade"].id)
    turma = _criar_turma(client, token, polo_a_id, modalidade_id)

    antigo = _cadastrar(client, token, polo_a_id, "55555", nome="Nome Antigo").json()
    _remover(client, token, antigo["id"])

    inscricao = _inscrever(client, polo_a_id, modalidade_id, documento="55555").json()
    resp = client.post(
        f"/api/v1/lista-espera/{inscricao['id']}/aceitar", json={"turma_id": turma["id"]}, headers=_headers(token)
    )
    assert resp.status_code == 204, resp.text

    ativos = _ativos(client, token)
    assert [b["id"] for b in ativos] == [antigo["id"]]
    assert ativos[0]["nome_completo"] == inscricao["nome_completo"]


def test_importar_documento_de_removido_reativa(client, seed_basico):
    token = login(client, "master@test.com")
    polo_a = seed_basico["polo_a"]

    antigo = _cadastrar(client, token, str(polo_a.id), "333.333.333-33", nome="Nome Antigo").json()
    _remover(client, token, antigo["id"])

    arquivo = _planilha(
        ["Nome completo*", "Data de nascimento (DD/MM/AAAA)*", "Documento (CPF)*", "Polo*"],
        [["Nome Importado", "10/05/2000", "333.333.333-33", polo_a.nome]],
    )
    resp = _upload(client, token, "/api/v1/beneficiarios/importar", arquivo, confirmar=True)
    assert resp.status_code == 200, resp.text
    assert resp.json()["sucesso"] == 1

    ativos = _ativos(client, token)
    assert [b["id"] for b in ativos] == [antigo["id"]]
    assert ativos[0]["nome_completo"] == "Nome Importado"
