"""
Entidade de domínio BENEFICIÁRIO (nomenclatura oficial e obrigatória do
sistema — nunca "aluno"). Representa a pessoa atendida pelos projetos
esportivos do Conexão Esporte.
"""
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

# Tamanhos aceitos pra entrega de uniforme/kit: numeração infantil primeiro
# (o projeto atende de 6 a 17 anos), depois a adulta.
TAMANHOS_CAMISA = ("4", "6", "8", "10", "12", "14", "16", "PP", "P", "M", "G", "GG", "XG", "XGG")
# Numeração brasileira de calçado.
TAMANHO_CALCADO_MINIMO = 20
TAMANHO_CALCADO_MAXIMO = 46


def validar_tamanhos(tamanho_camisa: str | None, tamanho_calcado: str | None) -> None:
    """Ambos opcionais; quando vierem, precisam estar na lista/faixa aceita.
    Reaproveitado pela inscrição na lista de espera."""
    if tamanho_camisa and tamanho_camisa not in TAMANHOS_CAMISA:
        raise ValueError(f"Tamanho de camisa inválido: {tamanho_camisa}")
    if tamanho_calcado and not (
        tamanho_calcado.isdigit() and TAMANHO_CALCADO_MINIMO <= int(tamanho_calcado) <= TAMANHO_CALCADO_MAXIMO
    ):
        raise ValueError(
            f"Tamanho de calçado deve ser um número de {TAMANHO_CALCADO_MINIMO} a {TAMANHO_CALCADO_MAXIMO}."
        )


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
    tamanho_camisa: str | None = None
    tamanho_calcado: str | None = None

    def __post_init__(self) -> None:
        if not self.nome_completo or not self.nome_completo.strip():
            raise ValueError("Nome completo do beneficiário é obrigatório.")
        if not self.documento or not self.documento.strip():
            raise ValueError("Documento (CPF ou equivalente) do beneficiário é obrigatório.")
        validar_tamanhos(self.tamanho_camisa, self.tamanho_calcado)

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
