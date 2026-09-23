"""
Entidade de domínio INSCRIÇÃO NA LISTA DE ESPERA: pré-cadastro público de
interesse, preenchido pela família (via formulário embutido na landing page
do projeto), antes de virar um BENEFICIÁRIO de verdade. Vira Beneficiário +
Matrícula só quando um GESTOR_POLO/MASTER aceita (ver
app/application/lista_espera/service.py).
"""
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from app.domain.beneficiario.entities import validar_tamanhos

# Faixa etária atendida pelo projeto — participantes fora disso não podem
# se inscrever na lista de espera (ver ListaEsperaService.inscrever).
IDADE_MINIMA_PROJETO = 6
IDADE_MAXIMA_PROJETO = 17


@dataclass
class InscricaoListaEspera:
    id: UUID | None
    nome_completo: str
    data_nascimento: date
    documento: str
    nome_responsavel: str | None
    documento_responsavel: str | None
    telefone_whatsapp: str
    email: str
    bairro: str | None
    cidade: str | None
    modalidade_id: UUID
    polo_id: UUID
    como_conheceu: str | None
    tamanho_camisa: str | None = None
    tamanho_calcado: str | None = None
    # Preenchidos só no aceite (ver LiataEsperaService.aceitar) — None = pendente.
    beneficiario_id: UUID | None = None
    turma_id: UUID | None = None
    aceito_por_id: UUID | None = None
    aceito_em: datetime | None = None
    criado_em: datetime | None = None

    def __post_init__(self) -> None:
        if not self.nome_completo or not self.nome_completo.strip():
            raise ValueError("Nome completo é obrigatório.")
        if not self.documento or not self.documento.strip():
            raise ValueError("Documento (CPF ou equivalente) é obrigatório.")
        if not self.telefone_whatsapp or not self.telefone_whatsapp.strip():
            raise ValueError("Telefone/WhatsApp é obrigatório.")
        if not self.email or not self.email.strip():
            raise ValueError("Email é obrigatório.")
        validar_tamanhos(self.tamanho_camisa, self.tamanho_calcado)

    @property
    def pendente(self) -> bool:
        return self.beneficiario_id is None

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

    def validar_faixa_etaria(self) -> None:
        """Só chamado na inscrição (ver ListaEsperaService.inscrever), nunca ao
        reconstruir uma inscrição já existente a partir do banco — senão uma
        inscrição pendente faria essa validação falhar sozinha no dia em que
        o participante fizesse aniversário e saísse da faixa."""
        if not (IDADE_MINIMA_PROJETO <= self.idade <= IDADE_MAXIMA_PROJETO):
            raise ValueError(
                f"O projeto atende participantes de {IDADE_MINIMA_PROJETO} a {IDADE_MAXIMA_PROJETO} anos."
            )

    def validar_responsavel_se_menor(self) -> None:
        if not self.eh_menor_de_idade:
            return
        if not (self.nome_responsavel and self.nome_responsavel.strip()):
            raise ValueError("Inscrição de menor de idade requer o nome do responsável.")
        if not (self.documento_responsavel and self.documento_responsavel.strip()):
            raise ValueError("Inscrição de menor de idade requer o documento (CPF) do responsável.")
