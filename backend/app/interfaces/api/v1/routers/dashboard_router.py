"""Rotas dos relatórios gerenciais com gráficos. Tag Swagger: 'Relatórios Gerenciais'.

Diferente das rotas `/exportar` (que devolvem .xlsx/.docx para a Portaria nº
102/2024), estas devolvem JSON agregado — o frontend desenha os gráficos e o
próprio navegador cuida da impressão/PDF (Ctrl+P).
"""
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.relatorios.dashboard_service import DashboardService
from app.core.dependencies import CurrentUser, DbSession, UsuarioAutenticado, assert_acesso_ao_polo, require_perfis
from app.domain.enums import PerfilUsuario
from app.domain.shared.exceptions import RecursoNaoEncontrado
from app.interfaces.api.v1.schemas.dashboard_schemas import RelatorioGeralResponse, RelatorioPoloResponse

router = APIRouter(prefix="/relatorios", tags=["Relatórios Gerenciais"])

SomenteMaster = Annotated[UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.MASTER))]


@router.get(
    "/polo/{polo_id}",
    response_model=RelatorioPoloResponse,
    summary="Relatório gerencial do polo (KPIs e gráficos)",
    description="MASTER pode consultar qualquer polo; GESTOR_POLO só o próprio. "
    "`data_inicio`/`data_fim` delimitam o período analisado (padrão: mês corrente, se omitidos no frontend).",
)
def relatorio_polo(
    polo_id: UUID,
    data_inicio: date,
    data_fim: date,
    usuario: CurrentUser,
    db: DbSession,
) -> RelatorioPoloResponse:
    assert_acesso_ao_polo(usuario, polo_id)
    try:
        return DashboardService(db).relatorio_polo(polo_id, data_inicio, data_fim)
    except RecursoNaoEncontrado as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/geral",
    response_model=RelatorioGeralResponse,
    summary="Relatório gerencial geral — todos os polos (somente MASTER)",
)
def relatorio_geral(
    data_inicio: date, data_fim: date, usuario: SomenteMaster, db: DbSession
) -> RelatorioGeralResponse:
    return DashboardService(db).relatorio_geral(data_inicio, data_fim)
