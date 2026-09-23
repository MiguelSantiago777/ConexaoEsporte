"""Use cases de Movimento de Estoque. O estoque é único: o saldo de um
produto é sempre o total de todos os movimentos dele. ENTRADA é lançada na
tela de Estoque (comprovante opcional). SAÍDA vem de uma Baixa direta pra
um polo (`dar_baixa`) ou de um item de Entrega de Materiais (ver
app/application/entrega_material/service.py, que chama `registrar_saida`)."""
from datetime import date
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.estoque.entities import MovimentoEstoque
from app.domain.shared.exceptions import ArquivoMuitoGrande, RecursoNaoEncontrado, RegraDeNegocioViolada, TipoArquivoNaoSuportado
from app.infrastructure.repositories.almoxarifado_repository import AlmoxarifadoRepository
from app.infrastructure.repositories.movimento_estoque_repository import MovimentoEstoqueRepository
from app.infrastructure.repositories.polo_repository import PoloRepository
from app.infrastructure.repositories.produto_repository import ProdutoRepository
from app.infrastructure.storage.armazenamento_documentos import armazenamento_estoque

CONTENT_TYPES_ACEITOS = {"application/pdf", "image/jpeg", "image/png", "image/webp"}


class MovimentoEstoqueService:
    def __init__(self, db: Session):
        self.repo = MovimentoEstoqueRepository(db)
        self.produto_repo = ProdutoRepository(db)
        self.almoxarifado_repo = AlmoxarifadoRepository(db)
        self.polo_repo = PoloRepository(db)

    def listar(
        self, produto_id: UUID | None = None, tipo: str | None = None,
        data_inicio: date | None = None, data_fim: date | None = None, almoxarifado_id: UUID | None = None,
    ) -> list[MovimentoEstoque]:
        return self.repo.listar(
            produto_id=produto_id, tipo=tipo, data_inicio=data_inicio, data_fim=data_fim,
            almoxarifado_id=almoxarifado_id,
        )

    def listar_pagina(
        self, pagina: int, tamanho_pagina: int, produto_id: UUID | None = None, tipo: str | None = None,
        data_inicio: date | None = None, data_fim: date | None = None, almoxarifado_id: UUID | None = None,
    ) -> tuple[list[MovimentoEstoque], int]:
        return self.repo.listar_pagina(
            pagina=pagina, tamanho_pagina=tamanho_pagina, produto_id=produto_id, tipo=tipo,
            data_inicio=data_inicio, data_fim=data_fim, almoxarifado_id=almoxarifado_id,
        )

    def listar_por_periodo(self, data_inicio: date, data_fim: date) -> list[MovimentoEstoque]:
        return self.repo.listar_por_periodo(data_inicio, data_fim)

    def buscar(self, movimento_id: UUID) -> MovimentoEstoque | None:
        return self.repo.buscar_por_id(movimento_id)

    async def registrar_entrada(
        self, produto_id: UUID, quantidade: int, data_ref: date, observacao: str | None,
        arquivo: UploadFile | None, criado_por_id: UUID | None,
        entregue_por: str | None = None, recebido_por: str | None = None,
        almoxarifado_id: UUID | None = None,
    ) -> MovimentoEstoque:
        """O comprovante é opcional. `almoxarifado_id` só é aceito por
        compatibilidade com clientes antigos — a tela atual nunca envia
        (estoque único)."""
        if not self.produto_repo.buscar_por_id(produto_id):
            raise RecursoNaoEncontrado("Produto não encontrado.")
        if almoxarifado_id and not self.almoxarifado_repo.buscar_por_id(almoxarifado_id):
            raise RecursoNaoEncontrado("Estoque não encontrado.")

        dados_arquivo = {}
        if arquivo is not None and arquivo.filename:
            if arquivo.content_type not in CONTENT_TYPES_ACEITOS:
                raise TipoArquivoNaoSuportado("Tipo de arquivo não permitido. Envie PDF, JPG, PNG ou WEBP.")

            conteudo = await arquivo.read()
            tamanho_maximo = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
            if len(conteudo) > tamanho_maximo:
                raise ArquivoMuitoGrande(f"Arquivo excede o limite de {settings.UPLOAD_MAX_SIZE_MB}MB.")

            caminho = armazenamento_estoque.salvar(str(produto_id), arquivo.filename, conteudo)
            dados_arquivo = dict(
                nome_arquivo=arquivo.filename, caminho_arquivo=caminho,
                content_type=arquivo.content_type, tamanho_bytes=len(conteudo),
            )

        movimento = MovimentoEstoque(
            id=None, produto_id=produto_id, almoxarifado_id=almoxarifado_id, tipo="ENTRADA",
            quantidade=quantidade, data=data_ref,
            observacao=observacao, entregue_por=entregue_por, recebido_por=recebido_por,
            criado_por_id=criado_por_id, **dados_arquivo,
        )
        return self.repo.criar(movimento)

    def dar_baixa(
        self, produto_id: UUID, polo_id: UUID, quantidade: int, data_ref: date,
        observacao: str | None, recebido_por: str | None, criado_por_id: UUID | None,
    ) -> MovimentoEstoque:
        """Saída direta pela tela de Estoque: tira `quantidade` do estoque e
        registra pra qual polo o material foi."""
        if not self.polo_repo.buscar_por_id(polo_id):
            raise RecursoNaoEncontrado("Polo não encontrado.")
        return self.registrar_saida(
            produto_id=produto_id, quantidade=quantidade, data_ref=data_ref, criado_por_id=criado_por_id,
            polo_id=polo_id, observacao=observacao, recebido_por=recebido_por,
        )

    def registrar_saida(
        self, produto_id: UUID, quantidade: int, data_ref: date, criado_por_id: UUID | None,
        almoxarifado_id: UUID | None = None, entrega_material_id: UUID | None = None,
        polo_id: UUID | None = None, observacao: str | None = None, recebido_por: str | None = None,
    ) -> MovimentoEstoque:
        """Valida o saldo e grava a SAÍDA. Sem `almoxarifado_id` (o normal
        agora) o saldo checado é o total do produto; com ele (só clientes
        antigos que ainda escolhem almoxarifado), é o daquele almoxarifado."""
        produto = self.produto_repo.buscar_por_id(produto_id)
        if not produto:
            raise RecursoNaoEncontrado("Produto não encontrado.")
        if almoxarifado_id and not self.almoxarifado_repo.buscar_por_id(almoxarifado_id):
            raise RecursoNaoEncontrado("Estoque não encontrado.")

        saldo = self.produto_repo.saldo_atual(produto_id, almoxarifado_id)
        if quantidade > saldo:
            raise RegraDeNegocioViolada(
                f"Estoque insuficiente de \"{produto.nome}\": "
                f"disponível {saldo} {produto.unidade_medida}, pedido {quantidade}."
            )

        movimento = MovimentoEstoque(
            id=None, produto_id=produto_id, almoxarifado_id=almoxarifado_id, polo_id=polo_id, tipo="SAIDA",
            quantidade=quantidade, data=data_ref, observacao=observacao, recebido_por=recebido_por,
            entrega_material_id=entrega_material_id, criado_por_id=criado_por_id,
        )
        return self.repo.criar(movimento)

    def buscar_arquivo(self, movimento_id: UUID):
        movimento = self.repo.buscar_por_id(movimento_id)
        if not movimento or not movimento.caminho_arquivo:
            return None, None
        with armazenamento_estoque.abrir(movimento.caminho_arquivo) as f:
            return movimento, f.read()

    def relatorio(self, data_inicio: date, data_fim: date, almoxarifado_id: UUID | None = None) -> dict:
        """Agrega, por produto, o total de Entradas e Saídas dentro do
        período (independente da data em que o produto foi cadastrado) e o
        saldo atual (sempre desde o início — o saldo não é "do período",
        porque não faz sentido mostrar quanto sobrou sem contar tudo que já
        entrou/saiu antes). Quando `almoxarifado_id` é informado (Coordenador
        de Almoxarifado), tudo fica restrito àquele almoxarifado — inclusive
        o saldo, que passa a ser só o dele, não o total do produto."""
        movimentos = self.repo.listar_por_periodo(data_inicio, data_fim, almoxarifado_id=almoxarifado_id)
        produtos = {p.id: p for p in self.produto_repo.listar()}
        if almoxarifado_id:
            saldos = {pid: self.produto_repo.saldo_atual(pid, almoxarifado_id) for pid in produtos}
        else:
            saldos = self.produto_repo.saldos_em_lote(list(produtos.keys()))

        por_produto: dict[UUID, dict[str, int]] = {}
        for mv in movimentos:
            acumulado = por_produto.setdefault(mv.produto_id, {"entradas": 0, "saidas": 0})
            if mv.tipo == "ENTRADA":
                acumulado["entradas"] += mv.quantidade
            else:
                acumulado["saidas"] += mv.quantidade

        saldos_lista = [
            {
                "produto_id": produto_id,
                "produto_nome": produtos[produto_id].nome if produto_id in produtos else "—",
                "unidade_medida": produtos[produto_id].unidade_medida if produto_id in produtos else "—",
                "total_entradas": totais["entradas"],
                "total_saidas": totais["saidas"],
                "saldo_atual": saldos.get(produto_id, 0),
            }
            for produto_id, totais in por_produto.items()
        ]
        saldos_lista.sort(key=lambda item: item["produto_nome"])

        return {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "total_produtos": len(por_produto) if almoxarifado_id else len(produtos),
            "total_entradas_periodo": sum(t["entradas"] for t in por_produto.values()),
            "total_saidas_periodo": sum(t["saidas"] for t in por_produto.values()),
            "saldos": saldos_lista,
            "movimentos": movimentos,
        }
