"""Use cases das fotos de evidência de aula (comprovam que a chamada de uma
turma+data realmente aconteceu — anexadas pelo PROFESSOR ao lançar a chamada)."""
from datetime import date
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.frequencia.entities import ChamadaEvidencia
from app.domain.shared.exceptions import ArquivoMuitoGrande, TipoArquivoNaoSuportado
from app.infrastructure.repositories.chamada_evidencia_repository import ChamadaEvidenciaRepository
from app.infrastructure.storage.armazenamento_documentos import armazenamento_evidencias

CONTENT_TYPES_ACEITOS = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}


class ChamadaEvidenciaService:
    def __init__(self, db: Session):
        self.repo = ChamadaEvidenciaRepository(db)

    def listar(self, turma_id: UUID, data_ref: date) -> list[ChamadaEvidencia]:
        return self.repo.listar_por_turma_e_data(turma_id, data_ref)

    def buscar(self, evidencia_id: UUID) -> ChamadaEvidencia | None:
        return self.repo.buscar_por_id(evidencia_id)

    async def enviar(
        self, turma_id: UUID, data_ref: date, arquivo: UploadFile, enviado_por_id: UUID
    ) -> ChamadaEvidencia:
        if arquivo.content_type not in CONTENT_TYPES_ACEITOS:
            raise TipoArquivoNaoSuportado("Tipo de arquivo não permitido. Envie uma foto em JPG, PNG, WEBP ou HEIC.")

        conteudo = await arquivo.read()
        tamanho_maximo = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
        if len(conteudo) > tamanho_maximo:
            raise ArquivoMuitoGrande(f"A foto excede o limite de {settings.UPLOAD_MAX_SIZE_MB}MB.")

        pasta = f"{turma_id}/{data_ref.isoformat()}"
        caminho = armazenamento_evidencias.salvar(pasta, arquivo.filename or "foto.jpg", conteudo)

        evidencia = ChamadaEvidencia(
            id=None, turma_id=turma_id, data=data_ref,
            nome_arquivo=arquivo.filename or "foto.jpg", caminho_arquivo=caminho,
            content_type=arquivo.content_type, tamanho_bytes=len(conteudo),
            enviado_por_id=enviado_por_id,
        )
        return self.repo.criar(evidencia)
