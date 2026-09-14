"""
Armazenamento dos documentos anexados a beneficiários (certidão, RG, comprovantes).

Implementação padrão: disco local do servidor, sob `settings.UPLOAD_DIR`. Os
arquivos NUNCA são servidos por uma rota estática pública — o download passa
sempre pela rota autenticada em `beneficiario_router`, que reaplica o mesmo
RBAC por polo usado no resto da API.

Para trocar por um backend de armazenamento externo (S3, MinIO etc.), basta
criar uma classe alternativa com a mesma interface (`salvar` / `abrir` /
`remover`) e trocar a instância `armazenamento_documentos` abaixo. Em disco
local, garanta que `UPLOAD_DIR` fique fora da pasta servida por qualquer
proxy estático e tenha backup incluído na rotina de backup do servidor.
"""
import uuid
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException, status

from app.core.config import settings


class ArmazenamentoLocalDocumentos:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def salvar(self, beneficiario_id: str, nome_original: str, conteudo: bytes) -> str:
        """Grava o arquivo em disco e retorna o caminho relativo salvo no banco."""
        extensao = Path(nome_original).suffix
        caminho_relativo = f"{beneficiario_id}/{uuid.uuid4()}{extensao}"
        destino = self.base_dir / caminho_relativo
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(conteudo)
        return caminho_relativo

    def abrir(self, caminho_relativo: str) -> BinaryIO:
        """Abre o arquivo referenciado pelo registro no banco. O registro e o
        arquivo em disco podem divergir (rebuild de container sem volume
        persistente, migração de storage, exclusão manual) — sem esse guard,
        toda rota `.../arquivo` (estoque, anexos gerais, documentos de
        beneficiário/usuário, evidências de chamada, comprovante de entrega)
        derrubava com 500 em vez do 404 que o chamador já está preparado
        para tratar."""
        try:
            return (self.base_dir / caminho_relativo).open("rb")
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado."
            ) from None

    def remover(self, caminho_relativo: str) -> None:
        (self.base_dir / caminho_relativo).unlink(missing_ok=True)


armazenamento_documentos = ArmazenamentoLocalDocumentos(settings.UPLOAD_DIR)
# Fotos de evidência de aula (chamada) — mesma implementação, pasta separada
# dos documentos de beneficiário.
armazenamento_evidencias = ArmazenamentoLocalDocumentos(settings.UPLOAD_DIR_EVIDENCIAS)
# Anexos do cadastro de professor (foto, documentos, contrato).
armazenamento_usuario_documentos = ArmazenamentoLocalDocumentos(settings.UPLOAD_DIR_USUARIOS)
# Repositório de Anexos Gerais por polo.
armazenamento_anexos_gerais = ArmazenamentoLocalDocumentos(settings.UPLOAD_DIR_ANEXOS_GERAIS)
# Nota fiscal/comprovante de uma Entrada de estoque.
armazenamento_estoque = ArmazenamentoLocalDocumentos(settings.UPLOAD_DIR_ESTOQUE)
# Comprovante de recebimento no polo de uma Entrega de Materiais.
armazenamento_comprovantes_entrega = ArmazenamentoLocalDocumentos(settings.UPLOAD_DIR_COMPROVANTES_ENTREGA)
