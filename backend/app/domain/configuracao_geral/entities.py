"""Entidade de domínio CONFIGURAÇÃO GERAL — registro único (singleton) com
dados globais do projeto/convênio, exibidos no rodapé de todos os
relatórios exportados. Não é por polo — cada polo já tem seu próprio Termo
de Fomento em `Polo`; isto é um dado só, da entidade como um todo."""
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class ConfiguracaoGeral:
    id: UUID | None
    nome_projeto: str | None
    numero_convenio: str | None
    data_inicio_projeto: date | None
    data_fim_projeto: date | None
    atualizado_por_id: UUID | None = None
    atualizado_em: datetime | None = None
