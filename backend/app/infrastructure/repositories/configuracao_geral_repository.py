"""Repositório da Configuração Geral — registro único (singleton) com os
dados globais do projeto/convênio."""
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
    ) -> ConfiguracaoGeral:
        m = self.db.scalars(select(ConfiguracaoGeralModel).limit(1)).first()
        if not m:
            m = ConfiguracaoGeralModel()
            self.db.add(m)
        m.nome_projeto = nome_projeto
        m.numero_convenio = numero_convenio
        m.data_inicio_projeto = data_inicio_projeto
        m.data_fim_projeto = data_fim_projeto
        m.atualizado_por_id = atualizado_por_id
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)
