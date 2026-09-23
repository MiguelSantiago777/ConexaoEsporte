"""Use cases de Produto (catálogo central de Estoque)."""
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.estoque.entities import MovimentoEstoque
from app.domain.produto.entities import Produto, normalizar_ncm
from app.domain.shared.exceptions import RecursoNaoEncontrado, RegraDeNegocioViolada
from app.infrastructure.repositories.movimento_estoque_repository import MovimentoEstoqueRepository
from app.infrastructure.repositories.produto_repository import ProdutoRepository


class ProdutoService:
    def __init__(self, db: Session):
        self.repo = ProdutoRepository(db)
        self.movimento_repo = MovimentoEstoqueRepository(db)

    def listar(self, apenas_ativos: bool = False) -> list[Produto]:
        return self.repo.listar(apenas_ativos=apenas_ativos)

    def listar_pagina(self, pagina: int, tamanho_pagina: int, nome: str | None = None) -> tuple[list[Produto], int]:
        return self.repo.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, nome=nome)

    def buscar(self, produto_id: UUID) -> Produto | None:
        return self.repo.buscar_por_id(produto_id)

    def saldo_atual(self, produto_id: UUID, almoxarifado_id: UUID | None = None) -> int:
        return self.repo.saldo_atual(produto_id, almoxarifado_id)

    def saldos_em_lote(self, produto_ids: list[UUID]) -> dict[UUID, int]:
        return self.repo.saldos_em_lote(produto_ids)

    def saldo_por_almoxarifado(self, produto_id: UUID) -> list[dict]:
        return self.repo.saldo_por_almoxarifado(produto_id)

    def saldos_por_produto_de(self, almoxarifado_id: UUID) -> list[dict]:
        return self.repo.saldos_por_produto_de(almoxarifado_id)

    def validar(
        self, nome: str, unidade_medida: str, descricao: str | None,
        ncm: str | None = None, quantidade_inicial: int = 0,
    ) -> Produto:
        """Monta e valida o produto sem gravar — reaproveitado por `criar` e pela
        prévia de importação em massa (que precisa validar sem persistir)."""
        if quantidade_inicial < 0:
            raise ValueError("Quantidade não pode ser negativa.")
        return Produto(id=None, nome=nome, unidade_medida=unidade_medida, descricao=descricao, ncm=ncm)

    def criar(
        self, nome: str, unidade_medida: str, descricao: str | None,
        ncm: str | None = None, quantidade_inicial: int = 0, criado_por_id: UUID | None = None,
    ) -> Produto:
        """Cadastra o produto e, se vier `quantidade_inicial`, já lança a
        ENTRADA correspondente no estoque — é assim que o operador informa
        "quanto tem" sem precisar de um segundo passo."""
        produto = self.validar(
            nome=nome, unidade_medida=unidade_medida, descricao=descricao,
            ncm=ncm, quantidade_inicial=quantidade_inicial,
        )
        criado = self.repo.criar(produto)
        if quantidade_inicial > 0:
            self.movimento_repo.criar(MovimentoEstoque(
                id=None, produto_id=criado.id, almoxarifado_id=None, tipo="ENTRADA",
                quantidade=quantidade_inicial, data=date.today(),
                observacao="Quantidade inicial informada no cadastro do produto.", criado_por_id=criado_por_id,
            ))
        return criado

    def atualizar(
        self, produto_id: UUID, nome: str | None, unidade_medida: str | None, descricao: str | None,
        ativo: bool | None = None, ncm: str | None = None,
    ) -> Produto:
        campos = dict(nome=nome, unidade_medida=unidade_medida, descricao=descricao, ativo=ativo)
        if ncm is not None:  # "" apaga o NCM
            campos["ncm"] = normalizar_ncm(ncm)
        atualizado = self.repo.atualizar(produto_id, **campos)
        if not atualizado:
            raise RecursoNaoEncontrado("Produto não encontrado.")
        return atualizado

    def remover(self, produto_id: UUID) -> None:
        # ON DELETE RESTRICT em movimentos_estoque.produto_id já bloqueia isso
        # no banco, mas aqui dá uma mensagem específica em vez de deixar o
        # handler genérico de IntegrityError responder algo mais vago.
        _, total_movimentos = self.movimento_repo.listar_pagina(pagina=1, tamanho_pagina=1, produto_id=produto_id)
        if total_movimentos > 0:
            raise RegraDeNegocioViolada(
                "Não é possível remover: existem movimentações de estoque registradas para este produto. "
                "Desative-o em vez de remover."
            )
        if not self.repo.remover(produto_id):
            raise RecursoNaoEncontrado("Produto não encontrado.")
