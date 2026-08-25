"""
Cria o primeiro usuário MASTER do sistema.

Necessário porque o cadastro de usuários pela API (POST /usuarios) exige
estar autenticado como MASTER ou GESTOR_POLO — alguém precisa existir antes.
Use este script uma única vez, logo após aplicar database/schema.sql em um
banco novo. NÃO use database/seed.sql em produção (ele grava usuários de
teste com a senha conhecida "senha123").

Uso (a partir de backend/, com o venv ativado e o .env configurado):
    python scripts/criar_usuario_master.py
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.domain.enums import PerfilUsuario
from app.domain.shared.exceptions import RegraDeNegocioViolada
from app.application.usuario.service import UsuarioService


def main() -> None:
    nome = input("Nome completo: ").strip()
    email = input("Email de login: ").strip()
    senha = getpass.getpass("Senha (mínimo 6 caracteres): ")
    confirmacao = getpass.getpass("Confirme a senha: ")

    if not nome or not email:
        print("Nome e email são obrigatórios.")
        raise SystemExit(1)
    if senha != confirmacao:
        print("As senhas não conferem.")
        raise SystemExit(1)
    if len(senha) < 6:
        print("A senha deve ter pelo menos 6 caracteres.")
        raise SystemExit(1)

    db = SessionLocal()
    try:
        service = UsuarioService(db)
        criado = service.criar_usuario(
            nome=nome, email=email, senha=senha, perfil=PerfilUsuario.MASTER, polo_id=None,
            criado_por_perfil=PerfilUsuario.MASTER, criado_por_polo_id=None,
        )
        print(f"Usuário MASTER criado com sucesso: {criado.email} (id={criado.id})")
    except RegraDeNegocioViolada as e:
        print(f"Erro: {e}")
        raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
