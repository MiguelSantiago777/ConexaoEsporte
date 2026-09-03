"""DTOs de Anexo Geral (repositório livre de documentos por polo)."""
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class AnexoGeralResponse(BaseModel):
    id: UUID
    polo_id: UUID
    titulo: str
    nome_arquivo: str
    content_type: str | None
    tamanho_bytes: int | None
    criado_em: datetime | None

    model_config = {"from_attributes": True}


TipoDocumentoConsolidado = Literal[
    "ANEXO_GERAL", "EVIDENCIA_CHAMADA", "OBSERVACAO_AULA", "ESTOQUE_ENTRADA", "ENTREGA_MATERIAIS"
]


class DocumentoConsolidadoResponse(BaseModel):
    """Item da visão consolidada e somente leitura de tudo que foi anexado
    pelos polos (Anexos Gerais), pelos gestores de polo, pelos professores ao
    lançar a chamada (fotos de evidência e observações do relatório de aula),
    ou gerado pelo módulo de Estoque (nota fiscal da Entrada, comprovante de
    recebimento no polo de uma Entrega de Materiais). `polo_id`/`polo_nome`
    ficam nulos só para a Entrada de estoque, que é um lançamento central e
    não pertence a nenhum polo específico."""

    id: UUID
    tipo: TipoDocumentoConsolidado
    titulo: str
    descricao: str | None = None
    polo_id: UUID | None = None
    polo_nome: str | None = None
    turma_nome: str | None = None
    autor_nome: str | None = None
    data_evento: date
    criado_em: datetime | None = None
    nome_arquivo: str | None = None
    content_type: str | None = None
    possui_arquivo: bool
