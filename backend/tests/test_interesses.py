"""
Testes das modalidades de INTERESSE do beneficiário: registro do interesse
enquanto o polo não tem turma, contagem de interessados no cadastro de
turma, matrícula automática dos interessados ao criar a turma e importação
em massa acrescentando interesses a quem já está cadastrado.
"""
from tests.conftest import login
from tests.test_importacao import _planilha, _upload


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _criar_beneficiario(client, token, polo_id, documento, nome="Beneficiário Teste"):
    resp = client.post(
        "/api/v1/beneficiarios",
        json={"nome_completo": nome, "data_nascimento": "2000-01-01", "documento": documento, "polo_id": polo_id},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _definir_interesses(client, token, beneficiario_id, modalidade_ids):
    return client.put(
        f"/api/v1/beneficiarios/{beneficiario_id}/interesses",
        json={"modalidade_ids": modalidade_ids},
        headers=_auth(token),
    )


def _criar_turma(client, token, polo_id, modalidade_id, limite_vagas=10, matricular_interessados=False):
    resp = client.post(
        "/api/v1/turmas",
        json={
            "polo_id": polo_id, "modalidade_id": modalidade_id,
            "horario_inicio": "08:00", "horario_fim": "09:00", "dias_semana": ["SEG"],
            "limite_vagas": limite_vagas, "matricular_interessados": matricular_interessados,
        },
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _contar_interessados(client, token, polo_id, modalidade_id):
    resp = client.get(
        "/api/v1/turmas/interessados",
        params={"polo_id": polo_id, "modalidade_id": modalidade_id},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["total"]


def test_definir_e_listar_interesses(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    judo = str(seed_basico["modalidade"].id)
    volei = client.post("/api/v1/modalidades", json={"nome": "Vôlei"}, headers=_auth(token)).json()["id"]
    b = _criar_beneficiario(client, token, str(seed_basico["polo_a"].id), "111.000.000-00")

    resp = _definir_interesses(client, token, b["id"], [judo, volei])
    assert resp.status_code == 200, resp.text
    assert set(resp.json()["modalidade_ids"]) == {judo, volei}

    _definir_interesses(client, token, b["id"], [volei])  # substitui a lista inteira
    resp = client.get(f"/api/v1/beneficiarios/{b['id']}/interesses", headers=_auth(token))
    assert resp.json()["modalidade_ids"] == [volei]


def test_gestor_nao_define_interesse_de_beneficiario_de_outro_polo(client, seed_basico):
    token_a = login(client, "gestor.a@test.com")
    token_b = login(client, "gestor.b@test.com")
    b = _criar_beneficiario(client, token_a, str(seed_basico["polo_a"].id), "111.000.000-00")

    resp = _definir_interesses(client, token_b, b["id"], [str(seed_basico["modalidade"].id)])
    assert resp.status_code == 403


def test_contagem_ignora_outro_polo_e_quem_ja_esta_matriculado(client, seed_basico):
    token = login(client, "master@test.com")
    polo_a, polo_b = str(seed_basico["polo_a"].id), str(seed_basico["polo_b"].id)
    judo = str(seed_basico["modalidade"].id)

    interessado = _criar_beneficiario(client, token, polo_a, "111.000.000-00")
    ja_matriculado = _criar_beneficiario(client, token, polo_a, "222.000.000-00")
    de_outro_polo = _criar_beneficiario(client, token, polo_b, "333.000.000-00")
    for b in (interessado, ja_matriculado, de_outro_polo):
        _definir_interesses(client, token, b["id"], [judo])
    assert _contar_interessados(client, token, polo_a, judo) == 2

    turma = _criar_turma(client, token, polo_a, judo)
    client.post(
        f"/api/v1/beneficiarios/{ja_matriculado['id']}/matriculas",
        json={"turma_id": turma["id"]}, headers=_auth(token),
    )
    assert _contar_interessados(client, token, polo_a, judo) == 1


def test_criar_turma_matricula_interessados_ate_o_limite_por_ordem_de_interesse(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    polo_a = str(seed_basico["polo_a"].id)
    judo = str(seed_basico["modalidade"].id)
    primeiro = _criar_beneficiario(client, token, polo_a, "111.000.000-00", nome="Zeca Primeiro")
    segundo = _criar_beneficiario(client, token, polo_a, "222.000.000-00", nome="Ana Segunda")
    terceiro = _criar_beneficiario(client, token, polo_a, "333.000.000-00", nome="Bia Terceira")
    for b in (primeiro, segundo, terceiro):
        _definir_interesses(client, token, b["id"], [judo])

    turma = _criar_turma(client, token, polo_a, judo, limite_vagas=2, matricular_interessados=True)
    assert turma["vagas_ocupadas"] == 2

    def matriculado(b):
        matriculas = client.get(f"/api/v1/beneficiarios/{b['id']}/matriculas", headers=_auth(token)).json()
        return any(m["turma_id"] == turma["id"] and m["ativo"] for m in matriculas)

    assert matriculado(primeiro) and matriculado(segundo)
    assert not matriculado(terceiro)
    assert _contar_interessados(client, token, polo_a, judo) == 1


def test_listagem_paginada_traz_resumo_de_modalidades(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    polo_a = str(seed_basico["polo_a"].id)
    judo = str(seed_basico["modalidade"].id)
    volei = client.post("/api/v1/modalidades", json={"nome": "Vôlei"}, headers=_auth(token)).json()["id"]
    b = _criar_beneficiario(client, token, polo_a, "111.000.000-00")
    _definir_interesses(client, token, b["id"], [judo, volei])
    _criar_turma(client, token, polo_a, judo, matricular_interessados=True)

    item = client.get("/api/v1/beneficiarios", params={"pagina": 1}, headers=_auth(token)).json()["itens"][0]
    assert item["modalidades_matriculado"] == [judo]
    assert item["modalidades_interesse"] == [volei]

    # listagem completa (usada pela Ficha Cadastral) traz o mesmo resumo
    item = client.get("/api/v1/beneficiarios", headers=_auth(token)).json()[0]
    assert item["modalidades_matriculado"] == [judo]
    assert item["modalidades_interesse"] == [volei]


def test_criar_turma_sem_a_opcao_nao_matricula_ninguem(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    polo_a = str(seed_basico["polo_a"].id)
    judo = str(seed_basico["modalidade"].id)
    b = _criar_beneficiario(client, token, polo_a, "111.000.000-00")
    _definir_interesses(client, token, b["id"], [judo])

    turma = _criar_turma(client, token, polo_a, judo)
    assert turma["vagas_ocupadas"] == 0


COLUNAS_IMPORTACAO = [
    "Nome completo*", "Data de nascimento (DD/MM/AAAA)*", "Documento (CPF)*", "Polo*", "Modalidades de interesse",
]


def test_importacao_acrescenta_interesse_a_beneficiario_ja_cadastrado(client, seed_basico):
    token = login(client, "master@test.com")
    polo_a = seed_basico["polo_a"]
    judo = str(seed_basico["modalidade"].id)
    volei = client.post("/api/v1/modalidades", json={"nome": "Vôlei"}, headers=_auth(token)).json()["id"]
    existente = _criar_beneficiario(client, token, str(polo_a.id), "209.863.179-03")

    arquivo = _planilha(
        COLUNAS_IMPORTACAO,
        [
            # mesmo CPF gravado com pontuação, digitado só com números; nomes sem acento/caixa
            ["Beneficiário Teste", "01/01/2000", "20986317903", polo_a.nome, "judo, volei"],
            ["Novo Interessado", "01/01/2000", "444.000.000-00", polo_a.nome, "Judô"],
        ],
    )
    resp = _upload(client, token, "/api/v1/beneficiarios/importar", arquivo, confirmar=True)
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["sucesso"] == 2, corpo
    assert corpo["linhas"][0]["aviso"]

    resp = client.get(f"/api/v1/beneficiarios/{existente['id']}/interesses", headers=_auth(token))
    assert set(resp.json()["modalidade_ids"]) == {judo, volei}
    assert len(client.get("/api/v1/beneficiarios", headers=_auth(token)).json()) == 2
    assert _contar_interessados(client, token, str(polo_a.id), judo) == 2


def test_importacao_com_modalidade_inexistente_da_erro(client, seed_basico):
    token = login(client, "master@test.com")
    polo_a = seed_basico["polo_a"]
    arquivo = _planilha(COLUNAS_IMPORTACAO, [["Fulano", "01/01/2000", "555.000.000-00", polo_a.nome, "Basquete"]])
    resp = _upload(client, token, "/api/v1/beneficiarios/importar", arquivo, confirmar=False)
    corpo = resp.json()
    assert corpo["falha"] == 1
    assert "Basquete" in corpo["linhas"][0]["erro"]


def test_importacao_sem_modalidades_continua_rejeitando_documento_repetido(client, seed_basico):
    token = login(client, "master@test.com")
    polo_a = seed_basico["polo_a"]
    _criar_beneficiario(client, token, str(polo_a.id), "666.000.000-00")
    arquivo = _planilha(COLUNAS_IMPORTACAO, [["Fulano", "01/01/2000", "666.000.000-00", polo_a.nome, ""]])
    resp = _upload(client, token, "/api/v1/beneficiarios/importar", arquivo, confirmar=True)
    assert resp.json()["falha"] == 1


def _interesses(client, token, beneficiario_id):
    return client.get(f"/api/v1/beneficiarios/{beneficiario_id}/interesses", headers=_auth(token)).json()[
        "modalidade_ids"
    ]


def _trocar_modalidade(client, token, turma_id, modalidade_id):
    return client.patch(f"/api/v1/turmas/{turma_id}", json={"modalidade_id": modalidade_id}, headers=_auth(token))


def test_trocar_modalidade_da_unica_turma_do_polo_leva_interesses_e_lista_de_espera(client, seed_basico):
    from tests.test_lista_espera import _inscrever

    token = login(client, "gestor.a@test.com")
    token_master = login(client, "master@test.com")
    polo_a, polo_b = str(seed_basico["polo_a"].id), str(seed_basico["polo_b"].id)
    judo = str(seed_basico["modalidade"].id)
    futebol = client.post("/api/v1/modalidades", json={"nome": "Futebol de Campo"}, headers=_auth(token)).json()["id"]

    matriculado = _criar_beneficiario(client, token, polo_a, "111.000.000-01", nome="A Matriculado")
    _definir_interesses(client, token, matriculado["id"], [judo])
    aguardando = _criar_beneficiario(client, token, polo_a, "111.000.000-02", nome="B Aguardando")
    _definir_interesses(client, token, aguardando["id"], [judo])
    outro_polo = _criar_beneficiario(client, token_master, polo_b, "111.000.000-03")
    _definir_interesses(client, token_master, outro_polo["id"], [judo])
    turma = _criar_turma(client, token, polo_a, judo, limite_vagas=1, matricular_interessados=True)
    assert turma["vagas_ocupadas"] == 1
    assert _inscrever(client, polo_a, judo).status_code == 201

    resp = _trocar_modalidade(client, token, turma["id"], futebol)
    assert resp.status_code == 200, resp.text
    assert resp.json()["modalidade_id"] == futebol

    assert _interesses(client, token, matriculado["id"]) == [futebol]
    assert _interesses(client, token, aguardando["id"]) == [futebol]
    assert _interesses(client, token_master, outro_polo["id"]) == [judo]
    pendentes = client.get("/api/v1/lista-espera", headers=_auth(token)).json()
    assert [i["modalidade_id"] for i in pendentes] == [futebol]


def test_trocar_modalidade_com_outra_turma_da_antiga_no_polo_so_leva_os_matriculados(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    polo_a = str(seed_basico["polo_a"].id)
    judo = str(seed_basico["modalidade"].id)
    futebol = client.post("/api/v1/modalidades", json={"nome": "Futebol de Campo"}, headers=_auth(token)).json()["id"]

    matriculado = _criar_beneficiario(client, token, polo_a, "111.000.000-01", nome="A Matriculado")
    _definir_interesses(client, token, matriculado["id"], [judo])
    aguardando = _criar_beneficiario(client, token, polo_a, "111.000.000-02", nome="B Aguardando")
    _definir_interesses(client, token, aguardando["id"], [judo])
    turma = _criar_turma(client, token, polo_a, judo, limite_vagas=1, matricular_interessados=True)
    _criar_turma(client, token, polo_a, judo)  # o polo continua oferecendo Judô

    assert _trocar_modalidade(client, token, turma["id"], futebol).status_code == 200
    assert _interesses(client, token, matriculado["id"]) == [futebol]
    assert _interesses(client, token, aguardando["id"]) == [judo]


def test_trocar_para_modalidade_inexistente_da_404(client, seed_basico):
    token = login(client, "gestor.a@test.com")
    turma = _criar_turma(client, token, str(seed_basico["polo_a"].id), str(seed_basico["modalidade"].id))
    resp = _trocar_modalidade(client, token, turma["id"], "00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404, resp.text
