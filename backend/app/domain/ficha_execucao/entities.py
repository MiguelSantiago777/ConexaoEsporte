from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

AJUSTE_STATUS_VALIDOS = {"NAO_SOLICITADO", "APROVADO", "NAO_APROVADO"}

# Ordem fixa das 15 linhas da seção "4 - Desenvolvimento das Atividades"
# do modelo oficial — usada tanto para semear uma ficha nova quanto pelo
# exportador para posicionar cada item na linha certa da planilha.
ATIVIDADES_COMPARATIVO_ITENS = [
    "Núcleo", "Modalidades", "Beneficiários", "Público", "Horário", "Turno",
    "Periodicidade", "Turmas", "Estruturação", "Execução/Mês", "Vigência",
    "Início das Atividades", "Atividades Extras", "Termo aditivo", "Divulgação do Projeto",
]

# 16 itens fixos da seção "5 - Execução" (checklist de documentação),
# mesma ordem do modelo oficial.
CHECKLIST_DOCUMENTOS_ITENS = [
    "Ficha de Inscrição dos Beneficiários",
    "Planilha de Núcleo/RH/Beneficiado",
    "Folha de Frequência Recursos Humanos",
    "Folha de Frequência Beneficiados",
    "Grade Horária",
    "Registro Fotográfico das Modalidades",
    "Registro fotográficos dos materiais adquiridos",
    "Registro Fotográfico dos uniformes adquiridos",
    "Registro fotográfico dos núcleos/estruturas identificados ou dos espaços onde serão realizados os eventos",
    "Registros Fotográficos da Divulgação do Projeto/Evento",
    "Registro Fotográfico de Identificação dos Núcleos",
    "Registros Fotográficos da equipe de RH",
    "Registros Fotográficos do material em utilização",
    "Registros Fotográficos dos uniformes em utilização",
    "Atividades extras",
    "Transparência e Divulgação das Ações Executadas",
]

# As duas metas fixas da seção "3 - Análise de Valor" do modelo oficial.
METAS_NOMES = [
    "META 01 – Planejamento e Desenvolvimento do Projeto",
    "META 2 – Divulgação do Projeto",
]


def metas_em_branco() -> list[dict]:
    return [{"meta": nome, "etapas": []} for nome in METAS_NOMES]


def atividades_comparativo_em_branco() -> list[dict]:
    return [{"item": item, "pactuado": "", "executado": "", "observacoes": ""} for item in ATIVIDADES_COMPARATIVO_ITENS]


def checklist_em_branco() -> list[dict]:
    return [{"documento": doc, "situacao": "Não Inserido", "observacao": ""} for doc in CHECKLIST_DOCUMENTOS_ITENS]


@dataclass
class FichaExecucao:
    """Ficha Técnica de Execução da Entidade — uma por polo e por
    período/trimestre reportado à prefeitura/governo (Portaria nº
    102/2024). A identificação do núcleo (nome/endereço/responsável/
    e-mail/telefone) vem do próprio Polo — aqui só a narrativa do período."""

    id: UUID | None
    polo_id: UUID
    periodo_referencia: str
    data_documento: date | None
    valor_recebido_periodo: str | None
    valor_recebido_extenso: str | None
    data_recebimento: date | None
    ajuste_status: str
    ajuste_justificativa: str | None
    metas: list[dict]
    atividades_comparativo: list[dict]
    checklist_documentos: list[dict]
    periodo_inscricao_inicio: date | None
    periodo_inscricao_fim: date | None
    inscricao_todos_nucleos: bool | None
    qtd_inscritos: int | None
    observacoes_inscricao: str | None
    quantitativo_beneficiados: str | None
    modalidades: str | None
    periodo_funcionamento: str | None
    descricao_atividades: str | None
    dificuldades: str | None
    impactos_sociais: str | None
    consideracoes_finais: str | None
    criado_por_id: UUID | None = None
    criado_em: object = None

    def __post_init__(self) -> None:
        if not self.periodo_referencia or not self.periodo_referencia.strip():
            raise ValueError("Período de referência da Ficha de Execução é obrigatório.")
        if self.ajuste_status not in AJUSTE_STATUS_VALIDOS:
            raise ValueError(f"ajuste_status deve ser um de: {AJUSTE_STATUS_VALIDOS}")
