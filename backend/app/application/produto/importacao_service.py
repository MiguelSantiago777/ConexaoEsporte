"""Importação em massa de PRODUTOS (catálogo central de Estoque) a partir de
planilha (.xlsx). É o caso mais simples: só 2 campos obrigatórios, sem FK e
sem checagem de duplicidade (o cadastro individual também permite nomes
repetidos)."""
from sqlalchemy.orm import Session

from app.application.importacao.campos import texto, texto_obrigatorio
from app.application.importacao.executor import executar_importacao
from app.application.importacao.planilha import ColunaModelo, gerar_modelo
from app.application.importacao.resultado import ResultadoImportacao
from app.application.produto.service import ProdutoService

COL_NOME = "Nome*"
COL_UNIDADE = "Unidade de medida*"
COL_DESCRICAO = "Descrição"

_COLUNAS = [
    ColunaModelo(COL_NOME, True, "Bola de futebol"),
    ColunaModelo(COL_UNIDADE, True, "unidade", "Ex.: unidade, par, caixa."),
    ColunaModelo(COL_DESCRICAO, False, ""),
]


class ProdutoImportacaoService:
    def __init__(self, db: Session):
        self.db = db
        self.service = ProdutoService(db)

    def gerar_modelo(self):
        return gerar_modelo("Modelo de Importação — Produtos", _COLUNAS)

    def importar(self, linhas: list[dict], confirmar: bool) -> ResultadoImportacao:
        def processar(linha: dict) -> str:
            nome = texto_obrigatorio(linha, COL_NOME)
            dados = dict(
                nome=nome,
                unidade_medida=texto_obrigatorio(linha, COL_UNIDADE),
                descricao=texto(linha, COL_DESCRICAO),
            )
            if confirmar:
                self.service.criar(**dados)
            else:
                self.service.validar(**dados)
            return nome

        return executar_importacao(self.db, linhas, processar, confirmar)
