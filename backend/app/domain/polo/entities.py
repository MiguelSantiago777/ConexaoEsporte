from dataclasses import dataclass, field
from datetime import date
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

    # Dados da parceria (Termo de Fomento) — cada polo é sua própria
    # entidade parceira para fins da Ficha Técnica de Execução.
    processo_sei: str | None = None
    termo_fomento_numero: str | None = None
    nome_entidade: str | None = None
    cnpj: str | None = None
    representante_legal_nome: str | None = None
    representante_legal_cpf: str | None = None
    objeto: str | None = None
    vigencia_inicio: date | None = None
    vigencia_fim: date | None = None
    valor_pactuado: str | None = None
    valor_executado: str | None = None
    parlamentar: str | None = None
    emenda: str | None = None
    termos_aditivos: list[dict] = field(default_factory=list)  # máx. 2: PRIMEIRO/SEGUNDO

    # Contato do núcleo para a seção "Identificação dos Núcleos" da Ficha
    responsavel_nome: str | None = None
    responsavel_email: str | None = None
    responsavel_telefone: str | None = None

    # Dados pessoais do representante legal para o Termo de Responsabilidade
    representante_legal_rg: str | None = None
    representante_legal_endereco: str | None = None
    representante_legal_bairro: str | None = None
    representante_legal_cidade: str | None = None

    def __post_init__(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ValueError("Nome do Polo é obrigatório.")
        if self.status not in ("ATIVO", "INATIVO"):
            raise ValueError("Status do Polo deve ser ATIVO ou INATIVO.")
