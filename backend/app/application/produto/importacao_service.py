"""Importação em massa de PRODUTOS (catálogo central de Estoque) a partir de
planilha (.xlsx). É o caso mais simples: só 2 campos obrigatórios, sem FK e
sem checagem de duplicidade (o cadastro individual também permite nomes
repetidos). A Quantidade, quando preenchida, vira a Entrada inicial do
produto no estoque (único) — igual ao cadastro individual."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.importacao.campos import numero_inteiro, texto, texto_obrigatorio
from app.application.importacao.executor import executar_importacao
from app.application.importacao.planilha import ColunaModelo, gerar_modelo
from app.application.importacao.resultado import ResultadoImportacao
from app.application.produto.service import ProdutoService
from app.domain.shared.exceptions import RegraDeNegocioViolada

COL_NOME = "Nome*"
COL_UNIDADE = "Unidade de medida*"
COL_QUANTIDADE = "Quantidade"
COL_NCM = "NCM"
COL_DESCRICAO = "Descrição"

_COLUNAS = [
    ColunaModelo(COL_NOME, True, "Bola de futebol"),
    ColunaModelo(COL_UNIDADE, True, "unidade", "Ex.: unidade, par, caixa."),
    ColunaModelo(COL_DESCRICAO, False, ""),
    ColunaModelo(
        COL_QUANTIDADE, False, "10",
        "Quantidade que já existe em estoque (número inteiro). Vazio = cadastra o produto com saldo 0.",
    ),
    ColunaModelo(
        COL_NCM, False, "9506.62.00",
        "Código NCM do produto, 8 dígitos — com ou sem pontos (ex.: 9506.62.00 ou 95066200).",
    ),
]


def _ncm(linha: dict) -> str | None:
    """O Excel entrega o NCM como número quando a célula não está formatada
    como texto — e aí some o zero à esquerda (ex.: 01012100 vira 1012100) e
    pode vir com ".0". Recompõe os 8 dígitos nesse caso."""
    valor = linha.get(COL_NCM)
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return str(int(valor)).zfill(8)
    return texto(linha, COL_NCM)


def _quantidade(linha: dict) -> int:
    if texto(linha, COL_QUANTIDADE) is None:
        return 0
    quantidade = numero_inteiro(linha, COL_QUANTIDADE)
    if quantidade < 0:
        raise RegraDeNegocioViolada(f'Coluna "{COL_QUANTIDADE}" não pode ser negativa.')
    return quantidade


class ProdutoImportacaoService:
    def __init__(self, db: Session):
        self.db = db
        self.service = ProdutoService(db)

    def gerar_modelo(self):
        return gerar_modelo("Modelo de Importação — Produtos", _COLUNAS)

    def importar(
        self, linhas: list[dict], confirmar: bool, criado_por_id: UUID | None = None,
    ) -> ResultadoImportacao:
        def processar(linha: dict) -> str:
            nome = texto_obrigatorio(linha, COL_NOME)
            dados = dict(
                nome=nome,
                unidade_medida=texto_obrigatorio(linha, COL_UNIDADE),
                descricao=texto(linha, COL_DESCRICAO),
                ncm=_ncm(linha),
                quantidade_inicial=_quantidade(linha),
            )
            if confirmar:
                self.service.criar(**dados, criado_por_id=criado_por_id)
            else:
                self.service.validar(**dados)
            return nome

        return executar_importacao(self.db, linhas, processar, confirmar)
