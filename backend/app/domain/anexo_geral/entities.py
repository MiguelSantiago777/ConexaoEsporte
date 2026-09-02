"""Entidade de domínio ANEXO GERAL — repositório livre de documentos por
polo, não ligado a um professor ou beneficiário específico (apólices,
contratos de aluguel, atas etc.). Cadastrado por MASTER ou GESTOR_POLO."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class AnexoGeral:
    id: UUID | None
    polo_id: UUID
    titulo: str
    nome_arquivo: str
    caminho_arquivo: str
    content_type: str | None
    tamanho_bytes: int | None
    enviado_por_id: UUID | None
    criado_em: datetime | None = None

    def __post_init__(self) -> None:
        if not self.titulo or not self.titulo.strip():
            raise ValueError("Título do anexo é obrigatório.")
