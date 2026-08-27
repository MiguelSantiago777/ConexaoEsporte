"""Use cases de Polo (apenas MASTER cria/edita Polos)."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.polo.entities import Polo
from app.domain.shared.exceptions import RecursoJaExiste
from app.infrastructure.repositories.polo_repository import PoloRepository


class PoloService:
    def __init__(self, db: Session):
        self.repo = PoloRepository(db)

    def listar(self) -> list[Polo]:
        return self.repo.listar()

    def buscar(self, polo_id: UUID) -> Polo | None:
        return self.repo.buscar_por_id(polo_id)

    def _validar_codigo_disponivel(self, codigo: str | None, ignorar_polo_id: UUID | None = None) -> None:
        if not codigo:
            return
        existente = self.repo.buscar_por_codigo(codigo)
        if existente and existente.id != ignorar_polo_id:
            raise RecursoJaExiste(f"Já existe um polo com o código '{codigo}'.")

    def criar(
        self, nome: str, codigo: str | None, endereco: str | None, gestor_responsavel_id: UUID | None,
        horario_funcionamento: str | None = None, **dados_parceria,
    ) -> Polo:
        self._validar_codigo_disponivel(codigo)
        polo = Polo(id=None, nome=nome, codigo=codigo, endereco=endereco,
                    horario_funcionamento=horario_funcionamento, status="ATIVO",
                    gestor_responsavel_id=gestor_responsavel_id, **dados_parceria)
        return self.repo.criar(polo)

    def atualizar(self, polo_id: UUID, **campos) -> Polo | None:
        if "codigo" in campos:
            self._validar_codigo_disponivel(campos["codigo"], ignorar_polo_id=polo_id)
        return self.repo.atualizar(polo_id, **campos)
