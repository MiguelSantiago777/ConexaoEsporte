"""
Entidade de domínio BENEFICIÁRIO (nomenclatura oficial e obrigatória do
sistema — nunca "aluno"). Representa a pessoa atendida pelos projetos
esportivos do Conexão Esporte.
"""
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class Beneficiario:
    id: UUID | None
    nome_completo: str
    data_nascimento: date
    documento: str
    polo_id: UUID | None
    responsavel_legal_nome: str | None
    responsavel_legal_data_nascimento: date | None
    responsavel_legal_tipo_relacao: str | None
    responsavel_legal_telefone_1: str | None
    responsavel_legal_telefone_2: str | None
    responsavel_legal_email: str | None
    responsavel_legal_rede_social: str | None
    endereco: str | None
    observacoes_medicas: str | None
    autoriza_whatsapp: bool = False
    ativo: bool = True

    def __post_init__(self) -> None:
        if not self.nome_completo or not self.nome_completo.strip():
            raise ValueError("Nome completo do beneficiário é obrigatório.")
        if not self.documento or not self.documento.strip():
            raise ValueError("Documento (CPF ou equivalente) do beneficiário é obrigatório.")

    @property
    def idade(self) -> int:
        hoje = date.today()
        anos = hoje.year - self.data_nascimento.year
        if (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day):
            anos -= 1
        return anos

    @property
    def eh_menor_de_idade(self) -> bool:
        return self.idade < 18

    def validar_responsavel_legal_se_menor(self) -> None:
        """Regra de negócio: beneficiário menor de idade precisa de responsável legal."""
        if self.eh_menor_de_idade and not (self.responsavel_legal_nome and self.responsavel_legal_nome.strip()):
            raise ValueError("Beneficiário menor de idade requer nome do responsável legal.")


# Tipos de documento aceitos no upload de anexos do beneficiário.
TIPOS_DOCUMENTO_BENEFICIARIO = (
    "foto",
    "certidao_nascimento_ou_identidade",
    "identidade_responsavel",
    "comprovante_residencia",
    "comprovante_escolar",
)


@dataclass
class BeneficiarioDocumento:
    id: UUID | None
    beneficiario_id: UUID
    tipo: str
    nome_arquivo: str
    caminho_arquivo: str
    content_type: str | None
    tamanho_bytes: int | None
    enviado_por_id: UUID | None
    criado_em: datetime | None = None

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS_DOCUMENTO_BENEFICIARIO:
            raise ValueError(f"Tipo de documento inválido: {self.tipo}")
