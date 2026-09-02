"""Helper compartilhado para servir um arquivo anexado como resposta HTTP
de download — usado por todo endpoint `.../arquivo` (beneficiário, usuário,
anexo geral). Escapa o nome do arquivo com segurança no Content-Disposition:
o nome veio do upload do usuário, então nunca é interpolado bruto no
header (uma aspa ou quebra de linha poderiam quebrá-lo)."""
from typing import Literal
from urllib.parse import quote

from fastapi import HTTPException, status
from fastapi.responses import Response

from app.application.relatorios.pdf_convert import LibreOfficeIndisponivel, converter_para_pdf

_MEDIA_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
}


def resposta_download(conteudo: bytes, content_type: str | None, nome_arquivo: str) -> Response:
    nome_seguro = nome_arquivo.replace("\\", "_").replace('"', "_")
    nome_ascii = nome_seguro.encode("ascii", errors="replace").decode("ascii")
    content_disposition = f'attachment; filename="{nome_ascii}"; filename*=UTF-8\'\'{quote(nome_seguro)}'
    return Response(
        content=conteudo,
        media_type=content_type or "application/octet-stream",
        headers={"Content-Disposition": content_disposition},
    )


def resposta_relatorio(
    buffer, nome_base: str, extensao_original: Literal["xlsx", "docx"], formato: Literal["xlsx", "docx", "pdf"]
) -> Response:
    """Devolve um relatório gerado (.xlsx ou .docx) no formato original ou,
    se `formato="pdf"`, convertido via LibreOffice headless (mesmo motor de
    renderização de quem abre o arquivo — preserva cabeçalho, colunas,
    gráficos e imagens fielmente)."""
    if formato == "pdf":
        try:
            conteudo = converter_para_pdf(buffer.getvalue(), extensao_original)
        except LibreOfficeIndisponivel as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
        return resposta_download(conteudo, _MEDIA_TYPES["pdf"], f"{nome_base}.pdf")
    return resposta_download(buffer.getvalue(), _MEDIA_TYPES[extensao_original], f"{nome_base}.{extensao_original}")
