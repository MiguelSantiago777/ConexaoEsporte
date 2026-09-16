"""Leitura da planilha enviada pelo usuário e geração do modelo (.xlsx) pra
importação em massa. Único formato suportado é .xlsx — mesma biblioteca
(`openpyxl`) já usada nos demais relatórios exportados pelo sistema; não há
parser de CSV/pandas no projeto."""
import io
from dataclasses import dataclass

import openpyxl
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.worksheet import Worksheet

from app.application.relatorios.xlsx_estilo import AZUL_MARCA, cabecalho_documento, escrever_tabela
from app.domain.shared.exceptions import RegraDeNegocioViolada

NOME_ABA_DADOS = "Dados"
NOME_ABA_INSTRUCOES = "Instruções"


@dataclass
class ColunaModelo:
    rotulo: str  # cabeçalho exibido na planilha — usado como chave pra ler a linha de volta
    obrigatoria: bool
    exemplo: str = ""
    ajuda: str = ""  # explicação exibida na aba "Instruções" (ex.: valores aceitos)


def gerar_modelo(titulo: str, colunas: list[ColunaModelo]) -> io.BytesIO:
    """`titulo` nomeia o arquivo gerado e a aba de instruções — a aba "Dados"
    em si começa com o cabeçalho já na linha 1 (sem linha de título acima),
    de propósito: `ler_planilha` espera o cabeçalho na primeira linha, e é
    a mesma aba "Dados" que o usuário reenvia preenchida."""
    wb = openpyxl.Workbook()

    ws_dados: Worksheet = wb.active
    ws_dados.title = NOME_ABA_DADOS
    rotulos = [c.rotulo for c in colunas]
    escrever_tabela(ws_dados, rotulos, [[c.exemplo for c in colunas]])

    ws_instrucoes = wb.create_sheet(NOME_ABA_INSTRUCOES)
    linha = cabecalho_documento(
        ws_instrucoes, titulo, "Preencha os dados na aba \"Dados\" e reenvie o arquivo no sistema."
    )
    ws_instrucoes.cell(row=linha, column=1, value="Coluna").font = Font(bold=True, color=AZUL_MARCA)
    ws_instrucoes.cell(row=linha, column=2, value="Obrigatória?").font = Font(bold=True, color=AZUL_MARCA)
    ws_instrucoes.cell(row=linha, column=3, value="Como preencher").font = Font(bold=True, color=AZUL_MARCA)
    for i, coluna in enumerate(colunas, start=linha + 1):
        ws_instrucoes.cell(row=i, column=1, value=coluna.rotulo)
        ws_instrucoes.cell(row=i, column=2, value="Sim" if coluna.obrigatoria else "Não")
        celula_ajuda = ws_instrucoes.cell(row=i, column=3, value=coluna.ajuda)
        celula_ajuda.alignment = Alignment(wrap_text=True, vertical="top")
    ws_instrucoes.column_dimensions["A"].width = 32
    ws_instrucoes.column_dimensions["B"].width = 14
    ws_instrucoes.column_dimensions["C"].width = 70

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def ler_planilha(conteudo: bytes) -> list[dict[str, str | None]]:
    """Lê a planilha enviada e devolve uma lista de linhas (uma por
    beneficiário/turma/etc.), cada uma como {rótulo_da_coluna: valor}. Pula
    linhas totalmente vazias. Aceita tanto o modelo gerado por
    `gerar_modelo` (aba "Dados") quanto uma planilha de aba única."""
    try:
        wb = openpyxl.load_workbook(io.BytesIO(conteudo), data_only=True)
    except Exception:
        raise RegraDeNegocioViolada("Não foi possível ler o arquivo — envie um .xlsx válido (use o modelo fornecido).")

    ws = wb[NOME_ABA_DADOS] if NOME_ABA_DADOS in wb.sheetnames else wb.worksheets[0]

    linhas_brutas = list(ws.iter_rows(values_only=True))
    if not linhas_brutas:
        return []

    cabecalho = [str(c).strip() if c is not None else "" for c in linhas_brutas[0]]
    resultado: list[dict[str, str | None]] = []
    for linha_valores in linhas_brutas[1:]:
        if linha_valores is None or all(v is None or str(v).strip() == "" for v in linha_valores):
            continue
        linha = {cabecalho[i]: linha_valores[i] for i in range(len(cabecalho)) if i < len(linha_valores)}
        resultado.append(linha)
    return resultado
