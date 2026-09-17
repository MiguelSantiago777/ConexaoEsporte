"""Use cases da Configuração Geral (número de convênio, datas do projeto e
Termo de Fomento — entidade parceira, CNPJ, vigência, valores e termos
aditivos — exibidos nos relatórios exportados)."""
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
        processo_sei: str | None = None, termo_fomento_numero: str | None = None,
        nome_entidade: str | None = None, cnpj: str | None = None,
        objeto: str | None = None, vigencia_inicio: date | None = None, vigencia_fim: date | None = None,
        valor_pactuado: str | None = None, valor_executado: str | None = None,
        parlamentar: str | None = None, emenda: str | None = None, termos_aditivos: list[dict] | None = None,
    ) -> ConfiguracaoGeral:
        return self.repo.salvar(
            nome_projeto=nome_projeto, numero_convenio=numero_convenio,
            data_inicio_projeto=data_inicio_projeto, data_fim_projeto=data_fim_projeto,
            atualizado_por_id=atualizado_por_id,
            processo_sei=processo_sei, termo_fomento_numero=termo_fomento_numero,
            nome_entidade=nome_entidade, cnpj=cnpj,
            objeto=objeto, vigencia_inicio=vigencia_inicio, vigencia_fim=vigencia_fim,
            valor_pactuado=valor_pactuado, valor_executado=valor_executado,
            parlamentar=parlamentar, emenda=emenda, termos_aditivos=termos_aditivos,
        )
