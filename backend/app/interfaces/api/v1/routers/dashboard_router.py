"""Rotas dos relatórios gerenciais com gráficos. Tag Swagger: 'Relatórios Gerenciais'.

Diferente das rotas `/exportar` (que devolvem .xlsx/.docx para a Portaria nº
102/2024), estas devolvem JSON agregado — o frontend desenha os gráficos e o
próprio navegador cuida da impressão/PDF (Ctrl+P).
"""
from datetime import date
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.application.relatorios.dashboard_service import DashboardService
from app.application.relatorios.relatorio_geral_export_service import exportar_relatorio_geral
from app.application.relatorios.relatorio_polo_export_service import exportar_relatorio_polo
from app.application.relatorios.tabela_export_service import exportar_tabelas
from app.core.dependencies import CurrentUser, DbSession, UsuarioAutenticado, assert_acesso_ao_polo, require_perfis
from app.domain.enums import PerfilUsuario
from app.domain.shared.exceptions import RecursoNaoEncontrado
from app.interfaces.api.v1.schemas.dashboard_schemas import RelatorioGeralResponse, RelatorioPoloResponse
from app.interfaces.api.v1.schemas.tabela_export_schemas import TabelaExportRequest

router = APIRouter(prefix="/relatorios", tags=["Relatórios Gerenciais"])

SomenteMaster = Annotated[UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.MASTER))]


def _resposta_xlsx(buffer, nome_arquivo: str) -> Response:
    nome_ascii = nome_arquivo.encode("ascii", errors="replace").decode("ascii")
    content_disposition = f'attachment; filename="{nome_ascii}"; filename*=UTF-8\'\'{quote(nome_arquivo)}'
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": content_disposition},
    )


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


@router.get(
    "/polo/{polo_id}/exportar",
    summary="Exportar o Relatório do Polo em .xlsx, com gráficos nativos",
)
def exportar_relatorio_polo_endpoint(
    polo_id: UUID, data_inicio: date, data_fim: date, usuario: CurrentUser, db: DbSession
) -> Response:
    assert_acesso_ao_polo(usuario, polo_id)
    try:
        relatorio = DashboardService(db).relatorio_polo(polo_id, data_inicio, data_fim)
    except RecursoNaoEncontrado as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    buffer = exportar_relatorio_polo(relatorio)
    return _resposta_xlsx(buffer, f"relatorio-do-polo-{relatorio.polo_nome}.xlsx")


@router.get(
    "/geral/exportar",
    summary="Exportar o Relatório Geral em .xlsx, com gráficos nativos (somente MASTER)",
)
def exportar_relatorio_geral_endpoint(data_inicio: date, data_fim: date, usuario: SomenteMaster, db: DbSession) -> Response:
    relatorio = DashboardService(db).relatorio_geral(data_inicio, data_fim)
    buffer = exportar_relatorio_geral(relatorio)
    return _resposta_xlsx(buffer, "relatorio-geral.xlsx")


@router.post(
    "/exportar-xlsx",
    summary="Exportar tabela(s) genéricas em .xlsx estilizado",
    description="Recebe tabela(s) já prontas — o frontend já aplicou filtros/máscaras (LGPD etc.) da própria "
    "tela — e devolve um .xlsx com cabeçalho na cor da marca, bordas e largura de coluna automática. "
    "Não lê nada do banco: só formata o que já chegou.",
)
def exportar_xlsx_generico(body: TabelaExportRequest, usuario: CurrentUser) -> Response:
    abas = [(aba.nome, aba.colunas, aba.linhas) for aba in body.abas]
    buffer = exportar_tabelas(abas, titulo=body.titulo)
    nome_arquivo = f"{(body.titulo or body.abas[0].nome).lower().replace(' ', '-')}.xlsx"
    return _resposta_xlsx(buffer, nome_arquivo)
