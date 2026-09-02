"""Use cases de Usuário: cadastro de funcionários (MASTER cria GESTOR_POLO/PROFESSOR)."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.domain.enums import PerfilUsuario
from app.domain.shared.exceptions import RecursoJaExiste, RegraDeNegocioViolada
from app.domain.usuario.entities import Usuario
from app.infrastructure.repositories.usuario_repository import UsuarioRepository


class UsuarioService:
    def __init__(self, db: Session):
        self.repo = UsuarioRepository(db)

    def criar_usuario(
        self, nome: str, email: str, senha: str, perfil: PerfilUsuario, polo_id: UUID | None,
        criado_por_perfil: PerfilUsuario, criado_por_polo_id: UUID | None,
        telefone: str | None = None, carga_horaria_semanal: str | None = None,
    ) -> Usuario:
        if self.repo.buscar_por_email(email):
            raise RecursoJaExiste("Já existe um usuário com este email.")

        # Regra: GESTOR_POLO só pode cadastrar PROFESSOR, e apenas no próprio polo.
        if criado_por_perfil == PerfilUsuario.GESTOR_POLO:
            if perfil != PerfilUsuario.PROFESSOR:
                raise RegraDeNegocioViolada("Gestor de Polo só pode cadastrar usuários com perfil PROFESSOR.")
            polo_id = criado_por_polo_id  # força o polo do próprio gestor

        usuario = Usuario(
            id=None, nome=nome, email=email, senha_hash=hash_password(senha),
            perfil=perfil, polo_id=polo_id, ativo=True,
            telefone=telefone, carga_horaria_semanal=carga_horaria_semanal,
        )
        return self.repo.criar(usuario)

    def listar_usuarios(self, polo_id: UUID | None = None) -> list[Usuario]:
        return self.repo.listar(polo_id=polo_id)

    def listar_usuarios_pagina(
        self, pagina: int, tamanho_pagina: int, polo_id: UUID | None = None, perfil: PerfilUsuario | None = None,
    ) -> tuple[list[Usuario], int]:
        return self.repo.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, polo_id=polo_id, perfil=perfil)

    def buscar_usuario(self, usuario_id: UUID) -> Usuario | None:
        return self.repo.buscar_por_id(usuario_id)

    def atualizar_usuario(self, usuario_id: UUID, **campos) -> Usuario | None:
        return self.repo.atualizar(usuario_id, **campos)
