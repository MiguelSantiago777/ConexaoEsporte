"""
Redefine a senha de um usuário existente sem precisar da senha atual — útil
quando as credenciais do primeiro usuário MASTER (criado por
criar_usuario_master.py) foram perdidas. Não existe como "ver" a senha
antiga: ela é armazenada com hash bcrypt, que não é reversível.

Uso (a partir de backend/, com o venv ativado e o .env configurado):
    python scripts/resetar_senha.py

Deixe o email em branco para listar os usuários com perfil MASTER antes de
escolher qual redefinir.
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.domain.enums import PerfilUsuario
from app.infrastructure.repositories.usuario_repository import UsuarioRepository


def main() -> None:
    db = SessionLocal()
    try:
        repo = UsuarioRepository(db)

        email = input("Email do usuário (deixe em branco para listar os MASTER): ").strip()
        if not email:
            masters = [u for u in repo.listar() if u.perfil == PerfilUsuario.MASTER]
            if not masters:
                print("Nenhum usuário com perfil MASTER encontrado.")
                raise SystemExit(1)
            print("Usuários MASTER:")
            for u in masters:
                print(f"  - {u.nome} <{u.email}>")
            print("\nRode o script de novo e informe um desses emails.")
            raise SystemExit(0)

        usuario = repo.buscar_por_email(email)
        if not usuario:
            print(f"Nenhum usuário encontrado com o email {email}.")
            raise SystemExit(1)

        senha = getpass.getpass("Nova senha (mínimo 6 caracteres): ")
        confirmacao = getpass.getpass("Confirme a nova senha: ")
        if senha != confirmacao:
            print("As senhas não conferem.")
            raise SystemExit(1)
        if len(senha) < 6:
            print("A senha deve ter pelo menos 6 caracteres.")
            raise SystemExit(1)

        repo.atualizar_senha(usuario.id, hash_password(senha))
        print(f"Senha redefinida com sucesso para {usuario.email} (perfil={usuario.perfil.value}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
