"""Use cases de Polo (apenas MASTER cria/edita Polos)."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.polo.entities import Polo
from app.domain.shared.exceptions import RecursoJaExiste, RecursoNaoEncontrado, RegraDeNegocioViolada
from app.infrastructure.repositories.beneficiario_repository import BeneficiarioRepository
from app.infrastructure.repositories.ficha_execucao_repository import FichaExecucaoRepository
from app.infrastructure.repositories.polo_repository import PoloRepository
from app.infrastructure.repositories.turma_repository import TurmaRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository


class PoloService:
    def __init__(self, db: Session):
        self.repo = PoloRepository(db)
        self.turma_repo = TurmaRepository(db)
        self.usuario_repo = UsuarioRepository(db)
        self.beneficiario_repo = BeneficiarioRepository(db)
        self.ficha_execucao_repo = FichaExecucaoRepository(db)

    def listar(self) -> list[Polo]:
        return self.repo.listar()

    def listar_pagina(self, pagina: int, tamanho_pagina: int, nome: str | None = None) -> tuple[list[Polo], int]:
        return self.repo.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, nome=nome)

    def buscar(self, polo_id: UUID) -> Polo | None:
        return self.repo.buscar_por_id(polo_id)

    def _validar_codigo_disponivel(self, codigo: str | None, ignorar_polo_id: UUID | None = None) -> None:
        if not codigo:
            return
        existente = self.repo.buscar_por_codigo(codigo)
        if existente and existente.id != ignorar_polo_id:
            raise RecursoJaExiste(f"Já existe um polo com o código '{codigo}'.")

    def validar(
        self, nome: str, codigo: str | None, endereco: str | None, gestor_responsavel_id: UUID | None,
        horario_funcionamento: str | None = None, **dados_parceria,
    ) -> Polo:
        """Monta e valida o polo sem gravar — reaproveitado por `criar` e pela
        prévia de importação em massa (que precisa validar sem persistir)."""
        self._validar_codigo_disponivel(codigo)
        return Polo(id=None, nome=nome, codigo=codigo, endereco=endereco,
                    horario_funcionamento=horario_funcionamento, status="ATIVO",
                    gestor_responsavel_id=gestor_responsavel_id, **dados_parceria)

    def criar(
        self, nome: str, codigo: str | None, endereco: str | None, gestor_responsavel_id: UUID | None,
        horario_funcionamento: str | None = None, **dados_parceria,
    ) -> Polo:
        polo = self.validar(
            nome=nome, codigo=codigo, endereco=endereco, gestor_responsavel_id=gestor_responsavel_id,
            horario_funcionamento=horario_funcionamento, **dados_parceria,
        )
        return self.repo.criar(polo)

    def atualizar(self, polo_id: UUID, **campos) -> Polo | None:
        if "codigo" in campos:
            self._validar_codigo_disponivel(campos["codigo"], ignorar_polo_id=polo_id)
        return self.repo.atualizar(polo_id, **campos)

    def remover(self, polo_id: UUID) -> None:
        """Exclusão de verdade (não é 'desativar') — recusa se ainda existir
        algo vinculado ao polo, pra nunca apagar histórico de atendimento
        (turmas, beneficiários, usuários, fichas de execução) sem querer.
        Desativar (`status=INATIVO`) continua disponível via PATCH pra quem
        só quer tirar o polo de uso, sem excluir nada."""
        if not self.repo.buscar_por_id(polo_id):
            raise RecursoNaoEncontrado("Polo não encontrado.")

        bloqueios = []
        if self.turma_repo.listar(polo_id=polo_id):
            bloqueios.append("turmas")
        if self.usuario_repo.listar(polo_id=polo_id):
            bloqueios.append("usuários (gestor/professores)")
        if self.beneficiario_repo.listar(polo_id=polo_id):
            bloqueios.append("beneficiários")
        if self.ficha_execucao_repo.listar(polo_id=polo_id):
            bloqueios.append("fichas de execução")
        if bloqueios:
            raise RegraDeNegocioViolada(
                f"Não é possível excluir: este polo ainda tem {', '.join(bloqueios)} vinculados. "
                "Remova ou transfira esses vínculos primeiro, ou desative o polo em vez de excluir."
            )
        self.repo.remover(polo_id)
