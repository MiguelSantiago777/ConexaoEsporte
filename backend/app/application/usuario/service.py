"""Use cases de Usuário: cadastro de funcionários (MASTER cria GESTOR_POLO/PROFESSOR)."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.domain.enums import PerfilUsuario
from app.domain.shared.exceptions import RecursoJaExiste, RecursoNaoEncontrado, RegraDeNegocioViolada
from app.domain.usuario.entities import Usuario
from app.infrastructure.repositories.polo_repository import PoloRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository

# Senha padrão de quem é cadastrado sem escolher uma — não depende do envio
# de email (que hoje não está configurado em produção). O usuário é
# obrigado a trocá-la no primeiro acesso (`deve_trocar_senha`, checado em
# `ProtectedRoute` no frontend e liberado em `AuthService.alterar_senha`).
SENHA_TEMPORARIA_PADRAO = "!Nata@!"


class UsuarioService:
    def __init__(self, db: Session):
        self.repo = UsuarioRepository(db)
        self.polo_repo = PoloRepository(db)

    def validar(
        self, nome: str, email: str, senha: str | None, perfil: PerfilUsuario, polo_id: UUID | None,
        criado_por_perfil: PerfilUsuario, criado_por_polo_id: UUID | None,
        telefone: str | None = None, cpf: str | None = None, carga_horaria_semanal: str | None = None,
        almoxarifado_id: UUID | None = None, papel_id: UUID | None = None,
    ) -> Usuario:
        """Monta e valida o usuário sem gravar — reaproveitado por `criar_usuario`
        e pela prévia de importação em massa (que precisa validar sem persistir).
        `senha=None` usa a senha temporária padrão (`SENHA_TEMPORARIA_PADRAO`) e
        marca `deve_trocar_senha=True`, forçando a troca no primeiro acesso."""
        if self.repo.buscar_por_email(email):
            raise RecursoJaExiste("Já existe um usuário com este email.")

        # Regra: GESTOR_POLO só pode cadastrar PROFESSOR, e apenas no próprio
        # polo. PERSONALIZADO com o módulo "professores" tem a mesma
        # restrição de perfil, mas sem forçar um polo (o Papel não é
        # vinculado a nenhum polo específico — quem cadastra escolhe).
        if criado_por_perfil in (PerfilUsuario.GESTOR_POLO, PerfilUsuario.PERSONALIZADO):
            if perfil != PerfilUsuario.PROFESSOR:
                raise RegraDeNegocioViolada("Este usuário só pode cadastrar usuários com perfil PROFESSOR.")
            if criado_por_perfil == PerfilUsuario.GESTOR_POLO:
                polo_id = criado_por_polo_id  # força o polo do próprio gestor

        return Usuario(
            id=None, nome=nome, email=email, senha_hash=hash_password(senha or SENHA_TEMPORARIA_PADRAO),
            perfil=perfil, polo_id=polo_id, ativo=True,
            telefone=telefone, cpf=cpf, carga_horaria_semanal=carga_horaria_semanal,
            almoxarifado_id=almoxarifado_id, papel_id=papel_id, deve_trocar_senha=senha is None,
        )

    def criar_usuario(
        self, nome: str, email: str, senha: str | None, perfil: PerfilUsuario, polo_id: UUID | None,
        criado_por_perfil: PerfilUsuario, criado_por_polo_id: UUID | None,
        telefone: str | None = None, cpf: str | None = None, carga_horaria_semanal: str | None = None,
        almoxarifado_id: UUID | None = None, papel_id: UUID | None = None,
    ) -> Usuario:
        usuario = self.validar(
            nome=nome, email=email, senha=senha, perfil=perfil, polo_id=polo_id,
            criado_por_perfil=criado_por_perfil, criado_por_polo_id=criado_por_polo_id,
            telefone=telefone, cpf=cpf, carga_horaria_semanal=carga_horaria_semanal,
            almoxarifado_id=almoxarifado_id, papel_id=papel_id,
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

    def remover_usuario(self, usuario_id: UUID) -> None:
        """Exclusão de verdade (não é 'desativar') — PROFESSOR nunca é
        excluído aqui: fica só a opção de desativar (`ativo=false`), pra
        preservar o vínculo com turmas/frequências já registradas. Pra
        qualquer outro perfil, tenta excluir de verdade; se o usuário já
        tiver algo vinculado no sistema (anexos, entregas, movimentações
        etc.), o banco recusa a exclusão (violação de chave estrangeira,
        traduzida como erro 400) — nesse caso, desative o acesso em vez de
        excluir."""
        usuario = self.repo.buscar_por_id(usuario_id)
        if not usuario:
            raise RecursoNaoEncontrado("Usuário não encontrado.")
        if usuario.perfil == PerfilUsuario.PROFESSOR:
            raise RegraDeNegocioViolada(
                "Professor não pode ser excluído — desative o acesso em vez disso."
            )
        # Se este usuário é o Gestor de Polo vinculado a algum polo, desfaz
        # o vínculo primeiro — senão a exclusão esbarraria na constraint de
        # chave estrangeira de `polos.gestor_responsavel_id`.
        self.polo_repo.limpar_gestor_responsavel(usuario_id)
        self.repo.remover(usuario_id)
