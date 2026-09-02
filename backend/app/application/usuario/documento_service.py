"""Use cases dos documentos anexados a um USUÁRIO (foto, documentos e
contrato do cadastro de professor)."""
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.shared.exceptions import ArquivoMuitoGrande, RecursoNaoEncontrado, TipoArquivoNaoSuportado
from app.domain.usuario.entities import UsuarioDocumento
from app.infrastructure.repositories.usuario_documento_repository import UsuarioDocumentoRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.infrastructure.storage.armazenamento_documentos import armazenamento_usuario_documentos

CONTENT_TYPES_ACEITOS = {"application/pdf", "image/jpeg", "image/png", "image/webp"}


class UsuarioDocumentoService:
    def __init__(self, db: Session):
        self.repo = UsuarioDocumentoRepository(db)
        self.usuario_repo = UsuarioRepository(db)

    def listar(self, usuario_id: UUID) -> list[UsuarioDocumento]:
        return self.repo.listar_por_usuario(usuario_id)

    def buscar(self, documento_id: UUID) -> UsuarioDocumento | None:
        return self.repo.buscar_por_id(documento_id)

    async def enviar(
        self, usuario_id: UUID, tipo: str, arquivo: UploadFile, enviado_por_id: UUID
    ) -> UsuarioDocumento:
        if not self.usuario_repo.buscar_por_id(usuario_id):
            raise RecursoNaoEncontrado("Usuário não encontrado.")

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

        caminho = armazenamento_usuario_documentos.salvar(str(usuario_id), arquivo.filename or "arquivo", conteudo)

        documento = UsuarioDocumento(
            id=None, usuario_id=usuario_id, tipo=tipo,
            nome_arquivo=arquivo.filename or "arquivo", caminho_arquivo=caminho,
            content_type=arquivo.content_type, tamanho_bytes=len(conteudo),
            enviado_por_id=enviado_por_id,
        )
        return self.repo.criar(documento)

    def remover(self, documento_id: UUID) -> None:
        documento = self.repo.buscar_por_id(documento_id)
        if not documento:
            raise RecursoNaoEncontrado("Documento não encontrado.")
        armazenamento_usuario_documentos.remover(documento.caminho_arquivo)
        self.repo.remover(documento_id)
