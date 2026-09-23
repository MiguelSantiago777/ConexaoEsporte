import re
from dataclasses import dataclass
from uuid import UUID


@dataclass
class Produto:
    """Item do catálogo central de Estoque (bolas, uniformes, materiais em
    geral) — a quantidade em si nunca fica neste registro; ela é sempre
    calculada a partir da soma dos Movimentos de Estoque (ver
    app/domain/estoque/entities.py)."""

    id: UUID | None
    nome: str
    unidade_medida: str
    descricao: str | None = None
    ativo: bool = True
    ncm: str | None = None

    def __post_init__(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ValueError("Nome do Produto é obrigatório.")
        if not self.unidade_medida or not self.unidade_medida.strip():
            raise ValueError("Unidade de medida do Produto é obrigatória.")
        self.ncm = normalizar_ncm(self.ncm)


def normalizar_ncm(ncm: str | None) -> str | None:
    """Aceita o NCM com ou sem pontuação ("9506.62.00" ou "95066200") e
    guarda só os 8 dígitos. Vazio vira None (o campo é opcional)."""
    if ncm is None or not str(ncm).strip():
        return None
    digitos = re.sub(r"[.\s-]", "", str(ncm).strip())
    if not re.fullmatch(r"\d{8}", digitos):
        raise ValueError(f'NCM inválido "{ncm}" — informe os 8 dígitos (ex.: 9506.62.00).')
    return digitos
