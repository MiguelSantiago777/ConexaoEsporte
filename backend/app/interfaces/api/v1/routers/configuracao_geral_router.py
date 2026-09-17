"""Rotas da Configuração Geral (número de convênio e datas do projeto,
exibidos no rodapé de todos os relatórios exportados). Tag Swagger:
'Configuração Geral'. Exclusivo do MASTER."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.configuracao_geral.service import ConfiguracaoGeralService
from app.core.dependencies import DbSession, UsuarioAutenticado, require_modulo_ou_perfis
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.schemas.configuracao_geral_schemas import (
    ConfiguracaoGeralResponse,
    ConfiguracaoGeralUpdateRequest,
)

router = APIRouter(prefix="/configuracao-geral", tags=["Configuração Geral"])

SomenteMaster = Annotated[
    UsuarioAutenticado, Depends(require_modulo_ou_perfis("configuracoes", PerfilUsuario.MASTER))
]


@router.get(
    "", response_model=ConfiguracaoGeralResponse | None,
    summary="Obter a Configuração Geral (somente MASTER)",
)
def obter_configuracao(usuario: SomenteMaster, db: DbSession) -> ConfiguracaoGeralResponse | None:
    config = ConfiguracaoGeralService(db).obter()
    return ConfiguracaoGeralResponse.model_validate(config) if config else None


@router.patch(
    "", response_model=ConfiguracaoGeralResponse,
    summary="Editar a Configuração Geral (somente MASTER)",
    description="Número de convênio, datas de início/fim do projeto e Termo de Fomento (entidade "
    "parceira, vigência, valores, parlamentar/emenda e termos aditivos) — passam a aparecer nos "
    "relatórios exportados pelo sistema. Pode ser alterado a qualquer momento.",
)
def atualizar_configuracao(
    body: ConfiguracaoGeralUpdateRequest, usuario: SomenteMaster, db: DbSession
) -> ConfiguracaoGeralResponse:
    atualizado = ConfiguracaoGeralService(db).atualizar(
        nome_projeto=body.nome_projeto, numero_convenio=body.numero_convenio,
        data_inicio_projeto=body.data_inicio_projeto,
        data_fim_projeto=body.data_fim_projeto, atualizado_por_id=usuario.id,
        processo_sei=body.processo_sei, termo_fomento_numero=body.termo_fomento_numero,
        nome_entidade=body.nome_entidade, cnpj=body.cnpj,
        objeto=body.objeto, vigencia_inicio=body.vigencia_inicio, vigencia_fim=body.vigencia_fim,
        valor_pactuado=body.valor_pactuado, valor_executado=body.valor_executado,
        parlamentar=body.parlamentar, emenda=body.emenda,
        termos_aditivos=[t.model_dump(mode="json") for t in body.termos_aditivos],
    )
    return ConfiguracaoGeralResponse.model_validate(atualizado)
