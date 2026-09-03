from dataclasses import dataclass, field
from uuid import UUID

from app.domain.enums.modulo_sistema import modulo_valido


@dataclass
class Papel:
    """Um nível de acesso personalizado, criado pelo MASTER na Central de
    Acessos: um nome e a lista de módulos do sistema que ele libera. Um
    usuário com perfil PERSONALIZADO vinculado a este Papel passa a ter
    acesso de leitura/escrita exatamente nesses módulos, em nenhum outro."""

    id: UUID | None
    nome: str
    descricao: str | None = None
    modulos: list[str] = field(default_factory=list)
    ativo: bool = True

    def __post_init__(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ValueError("Nome do Papel é obrigatório.")
        invalidos = [m for m in self.modulos if not modulo_valido(m)]
        if invalidos:
            raise ValueError(f"Módulo(s) inválido(s): {', '.join(invalidos)}.")
