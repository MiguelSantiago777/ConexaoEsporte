"""Use cases da Configuração Geral (número de convênio e datas do projeto,
exibidos no rodapé de todos os relatórios exportados)."""
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.configuracao_geral.entities import ConfiguracaoGeral
from app.infrastructure.repositories.configuracao_geral_repository import ConfiguracaoGeralRepository


class ConfiguracaoGeralService:
    def __init__(self, db: Session):
        self.repo = ConfiguracaoGeralRepository(db)

    def obter(self) -> ConfiguracaoGeral | None:
        return self.repo.buscar()

    def atualizar(
        self, nome_projeto: str | None, numero_convenio: str | None, data_inicio_projeto: date | None,
        data_fim_projeto: date | None, atualizado_por_id: UUID,
    ) -> ConfiguracaoGeral:
        return self.repo.salvar(nome_projeto, numero_convenio, data_inicio_projeto, data_fim_projeto, atualizado_por_id)
