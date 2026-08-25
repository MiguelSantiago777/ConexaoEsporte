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
        return (self.base_dir / caminho_relativo).open("rb")

    def remover(self, caminho_relativo: str) -> None:
        (self.base_dir / caminho_relativo).unlink(missing_ok=True)


armazenamento_documentos = ArmazenamentoLocalDocumentos(settings.UPLOAD_DIR)
