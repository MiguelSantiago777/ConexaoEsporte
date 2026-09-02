"""Conversão de .xlsx/.docx para PDF via LibreOffice headless.

Por quê LibreOffice: é a única opção que funciona igual neste ambiente de
desenvolvimento (Windows) e no servidor de produção (Linux, ver
DEPLOY.md) — gratuita, roda via linha de comando sem interface, e usa o
mesmo motor de renderização de quem abre o arquivo normalmente, então o
PDF sai fiel ao .xlsx/.docx original (cabeçalho, colunas, gráficos,
imagens). Automação via COM do Word/Excel foi descartada de propósito:
só existe no Windows, e o backend roda em produção num servidor Linux.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

_CAMINHOS_CANDIDATOS_WINDOWS = (
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
)


class LibreOfficeIndisponivel(RuntimeError):
    """LibreOffice (soffice) não encontrado no servidor — ver DEPLOY.md."""


def _localizar_soffice() -> str:
    encontrado = shutil.which("soffice") or shutil.which("soffice.exe")
    if encontrado:
        return encontrado
    for caminho in _CAMINHOS_CANDIDATOS_WINDOWS:
        if Path(caminho).exists():
            return caminho
    raise LibreOfficeIndisponivel(
        "LibreOffice (soffice) não está instalado neste servidor — necessário para exportar em PDF. "
        "Veja a nota sobre 'Exportação de relatórios em PDF' em DEPLOY.md."
    )


def converter_para_pdf(conteudo: bytes, extensao_origem: str) -> bytes:
    """Recebe os bytes de um .xlsx/.docx já gerado e devolve os bytes do PDF equivalente."""
    soffice = _localizar_soffice()
    with tempfile.TemporaryDirectory() as pasta_tmp:
        origem = Path(pasta_tmp) / f"documento.{extensao_origem}"
        origem.write_bytes(conteudo)
        resultado = subprocess.run(
            [
                soffice, "--headless", "--norestore", "--convert-to", "pdf",
                "--outdir", pasta_tmp, str(origem),
            ],
            capture_output=True, timeout=60,
        )
        destino = Path(pasta_tmp) / "documento.pdf"
        if not destino.exists():
            detalhe = resultado.stderr.decode(errors="replace") or resultado.stdout.decode(errors="replace")
            raise RuntimeError(f"Falha ao converter o relatório para PDF: {detalhe}")
        return destino.read_bytes()
