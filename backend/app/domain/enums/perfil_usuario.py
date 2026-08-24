"""
Enum de perfis de acesso (RBAC) do sistema Conexão Esporte.
Espelha o tipo ENUM `perfil_usuario` criado no Postgres (database/schema.sql).
"""
import enum


class PerfilUsuario(str, enum.Enum):
    MASTER = "MASTER"
    GESTOR_POLO = "GESTOR_POLO"
    PROFESSOR = "PROFESSOR"
