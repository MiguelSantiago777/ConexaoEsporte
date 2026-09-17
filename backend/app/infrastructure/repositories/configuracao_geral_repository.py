"""Repositório da Configuração Geral — registro único (singleton) com os
dados globais do projeto/convênio, incluindo o Termo de Fomento (entidade
parceira, CNPJ, vigência, valores, termos aditivos)."""
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.configuracao_geral.entities import ConfiguracaoGeral
from app.infrastructure.database.models import ConfiguracaoGeralModel


def _to_entity(m: ConfiguracaoGeralModel) -> ConfiguracaoGeral:
    return ConfiguracaoGeral(
        id=m.id, nome_projeto=m.nome_projeto, numero_convenio=m.numero_convenio,
        data_inicio_projeto=m.data_inicio_projeto, data_fim_projeto=m.data_fim_projeto,
        processo_sei=m.processo_sei, termo_fomento_numero=m.termo_fomento_numero,
        nome_entidade=m.nome_entidade, cnpj=m.cnpj,
        objeto=m.objeto, vigencia_inicio=m.vigencia_inicio, vigencia_fim=m.vigencia_fim,
        valor_pactuado=m.valor_pactuado, valor_executado=m.valor_executado,
        parlamentar=m.parlamentar, emenda=m.emenda, termos_aditivos=m.termos_aditivos or [],
        atualizado_por_id=m.atualizado_por_id, atualizado_em=m.atualizado_em,
    )


class ConfiguracaoGeralRepository:
    def __init__(self, db: Session):
        self.db = db

    def buscar(self) -> ConfiguracaoGeral | None:
        m = self.db.scalars(select(ConfiguracaoGeralModel).limit(1)).first()
        return _to_entity(m) if m else None

    def salvar(
        self, nome_projeto: str | None, numero_convenio: str | None, data_inicio_projeto: date | None,
        data_fim_projeto: date | None, atualizado_por_id: UUID,
        processo_sei: str | None = None, termo_fomento_numero: str | None = None,
        nome_entidade: str | None = None, cnpj: str | None = None,
        objeto: str | None = None, vigencia_inicio: date | None = None, vigencia_fim: date | None = None,
        valor_pactuado: str | None = None, valor_executado: str | None = None,
        parlamentar: str | None = None, emenda: str | None = None, termos_aditivos: list[dict] | None = None,
    ) -> ConfiguracaoGeral:
        m = self.db.scalars(select(ConfiguracaoGeralModel).limit(1)).first()
        if not m:
            m = ConfiguracaoGeralModel()
            self.db.add(m)
        m.nome_projeto = nome_projeto
        m.numero_convenio = numero_convenio
        m.data_inicio_projeto = data_inicio_projeto
        m.data_fim_projeto = data_fim_projeto
        m.processo_sei = processo_sei
        m.termo_fomento_numero = termo_fomento_numero
        m.nome_entidade = nome_entidade
        m.cnpj = cnpj
        m.objeto = objeto
        m.vigencia_inicio = vigencia_inicio
        m.vigencia_fim = vigencia_fim
        m.valor_pactuado = valor_pactuado
        m.valor_executado = valor_executado
        m.parlamentar = parlamentar
        m.emenda = emenda
        m.termos_aditivos = termos_aditivos or []
        m.atualizado_por_id = atualizado_por_id
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)
