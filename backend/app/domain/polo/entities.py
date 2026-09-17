from dataclasses import dataclass
from uuid import UUID


@dataclass
class Polo:
    id: UUID | None
    nome: str
    codigo: str | None
    endereco: str | None
    horario_funcionamento: str | None
    status: str  # "ATIVO" | "INATIVO"
    gestor_responsavel_id: UUID | None

    # Representante legal do polo, pro Termo de Responsabilidade — é por
    # polo (mais de um polo pode ter o mesmo representante, sem problema).
    representante_legal_nome: str | None = None
    representante_legal_cpf: str | None = None
    representante_legal_rg: str | None = None

    # Contato do núcleo para a seção "Identificação dos Núcleos" da Ficha
    responsavel_nome: str | None = None
    responsavel_email: str | None = None
    responsavel_telefone: str | None = None

    # Coordenadas do endereço, para exibir o polo no mapa do Dashboard.
    latitude: float | None = None
    longitude: float | None = None

    def __post_init__(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ValueError("Nome do Polo é obrigatório.")
        if self.status not in ("ATIVO", "INATIVO"):
            raise ValueError("Status do Polo deve ser ATIVO ou INATIVO.")
