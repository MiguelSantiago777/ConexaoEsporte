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


TipoDocumentoConsolidado = Literal["ANEXO_GERAL", "EVIDENCIA_CHAMADA", "OBSERVACAO_AULA"]


class DocumentoConsolidadoResponse(BaseModel):
    """Item da visão consolidada e somente leitura de tudo que foi anexado
    pelos polos (Anexos Gerais), pelos gestores de polo, ou pelos professores
    ao lançar a chamada (fotos de evidência e observações do relatório de
    aula)."""

    id: UUID
    tipo: TipoDocumentoConsolidado
    titulo: str
    descricao: str | None = None
    polo_id: UUID
    polo_nome: str
    turma_nome: str | None = None
    autor_nome: str | None = None
    data_evento: date
    criado_em: datetime | None = None
    nome_arquivo: str | None = None
    content_type: str | None = None
    possui_arquivo: bool
