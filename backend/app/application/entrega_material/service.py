"""Use casos de Entrega de Materiais (exclusiva do MASTER).

Cada item pode opcionalmente referenciar um `produto_id` do catálogo de
Estoque — quando isso acontece, criar a entrega registra automaticamente
uma Saída de estoque pra cada item (ver `MovimentoEstoqueService`), depois
de validar que há saldo suficiente de cada produto envolvido. Itens sem
`produto_id` continuam sendo só texto livre, sem nenhum efeito no estoque —
mantém compatibilidade com entregas já cadastradas."""
from datetime import date
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.application.estoque.service import MovimentoEstoqueService
from app.core.config import settings
from app.domain.entrega_material.entities import EntregaMaterial
from app.domain.shared.exceptions import (
    ArquivoMuitoGrande,
    RecursoNaoEncontrado,
    RegraDeNegocioViolada,
    TipoArquivoNaoSuportado,
)
from app.infrastructure.repositories.almoxarifado_repository import AlmoxarifadoRepository
from app.infrastructure.repositories.entrega_material_repository import EntregaMaterialRepository
from app.infrastructure.repositories.polo_repository import PoloRepository
from app.infrastructure.repositories.produto_repository import ProdutoRepository
from app.infrastructure.storage.armazenamento_documentos import armazenamento_comprovantes_entrega

CONTENT_TYPES_ACEITOS_COMPROVANTE = {"application/pdf", "image/jpeg", "image/png", "image/webp"}


class EntregaMaterialService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EntregaMaterialRepository(db)
        self.polo_repo = PoloRepository(db)
        self.produto_repo = ProdutoRepository(db)
        self.almoxarifado_repo = AlmoxarifadoRepository(db)

    def listar(self, polo_id: UUID | None = None) -> list[EntregaMaterial]:
        return self.repo.listar(polo_id=polo_id)

    def listar_pagina(self, pagina: int, tamanho_pagina: int, polo_id: UUID | None = None) -> tuple[list[EntregaMaterial], int]:
        return self.repo.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, polo_id=polo_id)

    def buscar(self, entrega_id: UUID) -> EntregaMaterial | None:
        return self.repo.buscar_por_id(entrega_id)

    def _itens_com_produto(self, itens: list[dict]) -> list[tuple[UUID, UUID, int]]:
        """Extrai (produto_id, almoxarifado_id, quantidade) de cada item que
        referencia o catálogo de estoque, validando que a quantidade é um
        inteiro positivo e que um almoxarifado foi escolhido — ambos
        obrigatórios pra virar uma Saída de verdade."""
        trincas = []
        for item in itens:
            produto_id = item.get("produto_id")
            if not produto_id:
                continue
            almoxarifado_id = item.get("almoxarifado_id")
            if not almoxarifado_id:
                raise RegraDeNegocioViolada("Quando o item vem do estoque, escolha de qual almoxarifado ele sai.")
            quantidade_str = str(item.get("quantidade", "")).strip()
            if not quantidade_str.isdigit() or int(quantidade_str) <= 0:
                raise RegraDeNegocioViolada(
                    "Quando o item vem do estoque, a quantidade deve ser um número inteiro positivo."
                )
            trincas.append((UUID(str(produto_id)), UUID(str(almoxarifado_id)), int(quantidade_str)))
        return trincas

    def criar(
        self, polo_id: UUID, data_entrega: date | None, itens: list[dict], criado_por_id: UUID | None,
        entregue_por: str | None = None,
    ) -> EntregaMaterial:
        polo = self.polo_repo.buscar_por_id(polo_id)
        if not polo:
            raise RecursoNaoEncontrado("Polo não encontrado.")

        itens_com_produto = self._itens_com_produto(itens)

        # Valida estoque suficiente de cada par (produto, almoxarifado) ANTES
        # de criar qualquer coisa — evita a entrega ficar registrada com só
        # parte das saídas se faltar estoque de um item no meio da lista. Um
        # produto pode ter saldo num almoxarifado e não ter em outro, então a
        # checagem é sempre por par, nunca pelo total do produto.
        pedido_por_par: dict[tuple[UUID, UUID], int] = {}
        for produto_id, almoxarifado_id, quantidade in itens_com_produto:
            chave = (produto_id, almoxarifado_id)
            pedido_por_par[chave] = pedido_por_par.get(chave, 0) + quantidade
        for (produto_id, almoxarifado_id), quantidade_pedida in pedido_por_par.items():
            produto = self.produto_repo.buscar_por_id(produto_id)
            if not produto:
                raise RecursoNaoEncontrado("Produto do estoque não encontrado.")
            almoxarifado = self.almoxarifado_repo.buscar_por_id(almoxarifado_id)
            if not almoxarifado:
                raise RecursoNaoEncontrado("Almoxarifado não encontrado.")
            saldo = self.produto_repo.saldo_atual(produto_id, almoxarifado_id)
            if quantidade_pedida > saldo:
                raise RegraDeNegocioViolada(
                    f'Estoque insuficiente de "{produto.nome}" no almoxarifado "{almoxarifado.nome}": '
                    f"disponível {saldo} {produto.unidade_medida}, pedido {quantidade_pedida}."
                )

        entrega = EntregaMaterial(
            id=None, polo_id=polo_id, data_entrega=data_entrega,
            coordenador_nome=polo.responsavel_nome, entregue_por=entregue_por,
            itens=itens, criado_por_id=criado_por_id,
        )
        criada = self.repo.criar(entrega)

        if itens_com_produto:
            movimento_service = MovimentoEstoqueService(self.db)
            data_movimento = data_entrega or date.today()
            for produto_id, almoxarifado_id, quantidade in itens_com_produto:
                movimento_service.registrar_saida(
                    produto_id=produto_id, almoxarifado_id=almoxarifado_id, quantidade=quantidade,
                    data_ref=data_movimento,
                    entrega_material_id=criada.id, criado_por_id=criado_por_id,
                )

        return criada

    def atualizar(self, entrega_id: UUID, **campos) -> EntregaMaterial | None:
        return self.repo.atualizar(entrega_id, **campos)

    async def enviar_comprovante(
        self, entrega_id: UUID, arquivo: UploadFile, recebido_por: str | None = None
    ) -> EntregaMaterial:
        """Anexa o comprovante de recebimento no polo — uma foto ou o PDF
        assinado do termo, tirado depois que a entrega já aconteceu. Quando
        informado, `recebido_por` substitui o `coordenador_nome` (que nasce
        só como um snapshot do responsável cadastrado do polo) pelo nome de
        quem de fato assinou o recebimento."""
        entrega = self.repo.buscar_por_id(entrega_id)
        if not entrega:
            raise RecursoNaoEncontrado("Entrega de materiais não encontrada.")

        if arquivo.content_type not in CONTENT_TYPES_ACEITOS_COMPROVANTE:
            raise TipoArquivoNaoSuportado("Tipo de arquivo não permitido. Envie PDF, JPG, PNG ou WEBP.")

        conteudo = await arquivo.read()
        tamanho_maximo = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
        if len(conteudo) > tamanho_maximo:
            raise ArquivoMuitoGrande(f"Arquivo excede o limite de {settings.UPLOAD_MAX_SIZE_MB}MB.")

        if entrega.comprovante_caminho_arquivo:
            armazenamento_comprovantes_entrega.remover(entrega.comprovante_caminho_arquivo)

        caminho = armazenamento_comprovantes_entrega.salvar(str(entrega_id), arquivo.filename or "comprovante", conteudo)
        campos = {
            "comprovante_nome_arquivo": arquivo.filename or "comprovante",
            "comprovante_caminho_arquivo": caminho,
            "comprovante_content_type": arquivo.content_type,
            "comprovante_tamanho_bytes": len(conteudo),
        }
        if recebido_por and recebido_por.strip():
            campos["coordenador_nome"] = recebido_por.strip()
        atualizada = self.repo.atualizar(entrega_id, **campos)
        return atualizada

    def abrir_comprovante(self, entrega_id: UUID) -> tuple[EntregaMaterial, bytes]:
        entrega = self.repo.buscar_por_id(entrega_id)
        if not entrega or not entrega.comprovante_caminho_arquivo:
            raise RecursoNaoEncontrado("Comprovante não encontrado para esta entrega.")
        with armazenamento_comprovantes_entrega.abrir(entrega.comprovante_caminho_arquivo) as f:
            return entrega, f.read()
