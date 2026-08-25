"""
Use cases dos documentos anexados a um BENEFICIÁRIO (certidão de nascimento
ou identidade, identidade do responsável, comprovante de residência e
comprovante escolar).
"""
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.beneficiario.entities import BeneficiarioDocumento
from app.domain.shared.exceptions import ArquivoMuitoGrande, RecursoNaoEncontrado, TipoArquivoNaoSuportado
from app.infrastructure.repositories.beneficiario_documento_repository import (
    BeneficiarioDocumentoRepository,
)
from app.infrastructure.repositories.beneficiario_repository import BeneficiarioRepository
from app.infrastructure.storage.armazenamento_documentos import armazenamento_documentos

CONTENT_TYPES_ACEITOS = {"application/pdf", "image/jpeg", "image/png", "image/webp"}


class BeneficiarioDocumentoService:
    def __init__(self, db: Session):
        self.repo = BeneficiarioDocumentoRepository(db)
        self.beneficiario_repo = BeneficiarioRepository(db)

    def listar(self, beneficiario_id: UUID) -> list[BeneficiarioDocumento]:
        return self.repo.listar_por_beneficiario(beneficiario_id)

    def buscar(self, documento_id: UUID) -> BeneficiarioDocumento | None:
        return self.repo.buscar_por_id(documento_id)

    async def enviar(
        self, beneficiario_id: UUID, tipo: str, arquivo: UploadFile, enviado_por_id: UUID
    ) -> BeneficiarioDocumento:
        if not self.beneficiario_repo.buscar_por_id(beneficiario_id):
            raise RecursoNaoEncontrado("Beneficiário não encontrado.")

        if arquivo.content_type not in CONTENT_TYPES_ACEITOS:
            raise TipoArquivoNaoSuportado(
                f"Tipo de arquivo não permitido para '{tipo}'. Envie PDF, JPG, PNG ou WEBP."
            )

        conteudo = await arquivo.read()
        tamanho_maximo = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
        if len(conteudo) > tamanho_maximo:
            raise ArquivoMuitoGrande(
                f"Arquivo de '{tipo}' excede o limite de {settings.UPLOAD_MAX_SIZE_MB}MB."
            )

        caminho = armazenamento_documentos.salvar(str(beneficiario_id), arquivo.filename or "arquivo", conteudo)

        documento = BeneficiarioDocumento(
            id=None, beneficiario_id=beneficiario_id, tipo=tipo,
            nome_arquivo=arquivo.filename or "arquivo", caminho_arquivo=caminho,
            content_type=arquivo.content_type, tamanho_bytes=len(conteudo),
            enviado_por_id=enviado_por_id,
        )
        return self.repo.criar(documento)
