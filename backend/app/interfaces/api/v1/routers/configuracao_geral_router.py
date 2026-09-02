"""Rotas da Configuração Geral (número de convênio e datas do projeto,
exibidos no rodapé de todos os relatórios exportados). Tag Swagger:
'Configuração Geral'. Exclusivo do MASTER."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.configuracao_geral.service import ConfiguracaoGeralService
from app.core.dependencies import DbSession, UsuarioAutenticado, require_perfis
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.schemas.configuracao_geral_schemas import (
    ConfiguracaoGeralResponse,
    ConfiguracaoGeralUpdateRequest,
)

router = APIRouter(prefix="/configuracao-geral", tags=["Configuração Geral"])

SomenteMaster = Annotated[UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.MASTER))]


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
    description="Número de convênio e datas de início/fim do projeto — passam a aparecer no rodapé de "
    "todos os relatórios exportados pelo sistema. Pode ser alterado a qualquer momento.",
)
def atualizar_configuracao(
    body: ConfiguracaoGeralUpdateRequest, usuario: SomenteMaster, db: DbSession
) -> ConfiguracaoGeralResponse:
    atualizado = ConfiguracaoGeralService(db).atualizar(
        nome_projeto=body.nome_projeto, numero_convenio=body.numero_convenio,
        data_inicio_projeto=body.data_inicio_projeto,
        data_fim_projeto=body.data_fim_projeto, atualizado_por_id=usuario.id,
    )
    return ConfiguracaoGeralResponse.model_validate(atualizado)
