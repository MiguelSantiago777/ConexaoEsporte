"""Use cases de Papel (Central de Acessos — níveis de acesso personalizados)."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.papel.entities import Papel
from app.domain.shared.exceptions import RecursoNaoEncontrado, RegraDeNegocioViolada
from app.infrastructure.repositories.papel_repository import PapelRepository


class PapelService:
    def __init__(self, db: Session):
        self.repo = PapelRepository(db)

    def listar(self, apenas_ativos: bool = False) -> list[Papel]:
        return self.repo.listar(apenas_ativos=apenas_ativos)

    def listar_pagina(self, pagina: int, tamanho_pagina: int, nome: str | None = None) -> tuple[list[Papel], int]:
        return self.repo.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, nome=nome)

    def buscar(self, papel_id: UUID) -> Papel | None:
        return self.repo.buscar_por_id(papel_id)

    def criar(self, nome: str, descricao: str | None, modulos: list[str]) -> Papel:
        papel = Papel(id=None, nome=nome, descricao=descricao, modulos=modulos)
        return self.repo.criar(papel)

    def atualizar(
        self, papel_id: UUID, nome: str | None, descricao: str | None, modulos: list[str] | None, ativo: bool | None = None,
    ) -> Papel:
        # Valida os módulos antes de gravar (mesma validação do __post_init__
        # da entidade, refeita aqui porque o repositório grava direto no ORM).
        if modulos is not None:
            Papel(id=None, nome=nome or "válido", modulos=modulos)
        atualizado = self.repo.atualizar(papel_id, nome=nome, descricao=descricao, modulos=modulos, ativo=ativo)
        if not atualizado:
            raise RecursoNaoEncontrado("Papel não encontrado.")
        return atualizado

    def remover(self, papel_id: UUID) -> None:
        if self.repo.contar_usuarios_vinculados(papel_id) > 0:
            raise RegraDeNegocioViolada(
                "Não é possível remover: existem usuários vinculados a este Papel. Desative-o em vez de remover."
            )
        if not self.repo.remover(papel_id):
            raise RecursoNaoEncontrado("Papel não encontrado.")
