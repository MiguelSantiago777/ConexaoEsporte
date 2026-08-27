"""Exportação genérica de tabela(s) já prontas (vindas do frontend, já
filtradas/mascaradas conforme os toggles da tela) para .xlsx estilizado.
Não acessa o banco — só formata os dados que já chegaram, então a mesma
regra de autorização que valeu para buscar os dados na tela original
(LGPD, "incluir demitidos" etc.) já foi aplicada antes de chegar aqui."""
import io

import openpyxl

from app.application.relatorios.xlsx_estilo import escrever_tabela


def exportar_tabelas(abas: list[tuple[str, list[str], list[list]]], titulo: str | None = None) -> io.BytesIO:
    """`abas`: lista de (nome_da_aba, colunas, linhas)."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    for nome_aba, colunas, linhas in abas:
        ws = wb.create_sheet(nome_aba[:31])
        linha_inicial = 1
        aba_titulo = titulo if len(abas) == 1 else None
        escrever_tabela(ws, colunas, linhas, linha_inicial=linha_inicial, titulo=aba_titulo)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
