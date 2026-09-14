"""Renderização dos templates HTML de email (Jinja2), separados dos
templates de documento (docx/xlsx) em app/infrastructure/templates — são
duas coisas diferentes: aqueles viram anexo/arquivo baixado, estes viram o
corpo de um email."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_DIR_TEMPLATES = Path(__file__).parent / "templates"

_ambiente = Environment(
    loader=FileSystemLoader(_DIR_TEMPLATES),
    autoescape=select_autoescape(["html"]),
)


def renderizar(nome_template: str, **contexto) -> str:
    return _ambiente.get_template(nome_template).render(**contexto)
