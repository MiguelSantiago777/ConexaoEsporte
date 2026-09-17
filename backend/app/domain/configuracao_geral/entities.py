"""Entidade de domínio CONFIGURAÇÃO GERAL — registro único (singleton) com
dados globais do projeto/convênio, exibidos no rodapé de todos os
relatórios exportados. Inclui o Termo de Fomento (entidade parceira, CNPJ,
vigência, valores, parlamentar/emenda e termos aditivos) — não é por polo:
a entidade parceira é a mesma em todos os polos do projeto, então isto é
um dado só, da entidade como um todo. O representante legal fica no
cadastro de Polo (`app/domain/polo/entities.py`), não aqui."""
from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID


@dataclass
class ConfiguracaoGeral:
    id: UUID | None
    nome_projeto: str | None
    numero_convenio: str | None
    data_inicio_projeto: date | None
    data_fim_projeto: date | None

    # Termo de Fomento — dados da entidade parceira, únicos pro projeto inteiro.
    processo_sei: str | None = None
    termo_fomento_numero: str | None = None
    nome_entidade: str | None = None
    cnpj: str | None = None
    objeto: str | None = None
    vigencia_inicio: date | None = None
    vigencia_fim: date | None = None
    valor_pactuado: str | None = None
    valor_executado: str | None = None
    parlamentar: str | None = None
    emenda: str | None = None
    termos_aditivos: list[dict] = field(default_factory=list)  # máx. 2: PRIMEIRO/SEGUNDO

    atualizado_por_id: UUID | None = None
    atualizado_em: datetime | None = None
