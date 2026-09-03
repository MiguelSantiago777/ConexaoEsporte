"""
Enum de perfis de acesso (RBAC) do sistema Conexão Esporte.
Espelha o tipo ENUM `perfil_usuario` criado no Postgres (database/schema.sql).
"""
import enum


class PerfilUsuario(str, enum.Enum):
    MASTER = "MASTER"
    GESTOR_POLO = "GESTOR_POLO"
    PROFESSOR = "PROFESSOR"
    COORDENADOR_ALMOXARIFADO = "COORDENADOR_ALMOXARIFADO"
    # Perfil dinâmico: o acesso real vem do Papel vinculado (ver
    # app/domain/papel/entities.py), não de regras fixas deste enum — criado
    # pela Central de Acessos, exclusiva do MASTER.
    PERSONALIZADO = "PERSONALIZADO"
