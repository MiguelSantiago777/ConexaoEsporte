"""Use cases de Almoxarifado (locais físicos do estoque central)."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.almoxarifado.entities import Almoxarifado
from app.domain.shared.exceptions import RecursoNaoEncontrado, RegraDeNegocioViolada
from app.infrastructure.repositories.almoxarifado_repository import AlmoxarifadoRepository
from app.infrastructure.repositories.movimento_estoque_repository import MovimentoEstoqueRepository


class AlmoxarifadoService:
    def __init__(self, db: Session):
        self.repo = AlmoxarifadoRepository(db)
        self.movimento_repo = MovimentoEstoqueRepository(db)

    def listar(self, apenas_ativos: bool = False) -> list[Almoxarifado]:
        return self.repo.listar(apenas_ativos=apenas_ativos)

    def listar_pagina(self, pagina: int, tamanho_pagina: int, nome: str | None = None) -> tuple[list[Almoxarifado], int]:
        return self.repo.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, nome=nome)

    def buscar(self, almoxarifado_id: UUID) -> Almoxarifado | None:
        return self.repo.buscar_por_id(almoxarifado_id)

    def criar(self, nome: str, descricao: str | None) -> Almoxarifado:
        almoxarifado = Almoxarifado(id=None, nome=nome, descricao=descricao)
        return self.repo.criar(almoxarifado)

    def atualizar(self, almoxarifado_id: UUID, nome: str | None, descricao: str | None, ativo: bool | None = None) -> Almoxarifado:
        atualizado = self.repo.atualizar(almoxarifado_id, nome=nome, descricao=descricao, ativo=ativo)
        if not atualizado:
            raise RecursoNaoEncontrado("Almoxarifado não encontrado.")
        return atualizado

    def remover(self, almoxarifado_id: UUID) -> None:
        _, total_movimentos = self.movimento_repo.listar_pagina(pagina=1, tamanho_pagina=1, almoxarifado_id=almoxarifado_id)
        if total_movimentos > 0:
            raise RegraDeNegocioViolada(
                "Não é possível remover: existem movimentações de estoque registradas para este almoxarifado. "
                "Desative-o em vez de remover."
            )
        if not self.repo.remover(almoxarifado_id):
            raise RecursoNaoEncontrado("Almoxarifado não encontrado.")
