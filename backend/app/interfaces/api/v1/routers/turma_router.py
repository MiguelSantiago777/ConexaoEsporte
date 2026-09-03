"""Rotas de Turmas. Tag Swagger: 'Turmas'."""
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.application.relatorios.service import RelatorioService
from app.application.turma.service import TurmaService
from app.core.dependencies import (
    CurrentUser,
    DbSession,
    UsuarioAutenticado,
    assert_acesso_ao_polo,
    assert_acesso_a_turma,
    require_modulo_ou_perfis,
)
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.routers._arquivo_helper import resposta_relatorio
from app.interfaces.api.v1.schemas.paginacao_schemas import PaginaResponse
from app.interfaces.api.v1.schemas.turma_schemas import TurmaCreateRequest, TurmaResponse, TurmaUpdateRequest

router = APIRouter(prefix="/turmas", tags=["Turmas"])

MasterOuGestor = Annotated[
    UsuarioAutenticado,
    Depends(require_modulo_ou_perfis("turmas", PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO)),
]
# Exportação da Lista de Presença: também liberada para o PROFESSOR da
# turma (é quem lança a chamada) — assert_acesso_a_turma já restringe ao
# professor vinculado, mesma regra usada em POST /frequencias/chamada.
QualquerPerfil = Annotated[
    UsuarioAutenticado,
    Depends(require_modulo_ou_perfis(
        "turmas", PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO, PerfilUsuario.PROFESSOR,
    )),
]


@router.get(
    "",
    response_model=list[TurmaResponse] | PaginaResponse[TurmaResponse],
    summary="Listar turmas",
    description="MASTER vê todas. GESTOR_POLO vê as do seu polo. PROFESSOR vê apenas as suas. "
    "Informe `pagina` pra paginar — sem isso, devolve a lista inteira (uso por telas que só "
    "precisam das opções, como um <select>).",
)
def listar_turmas(
    usuario: CurrentUser, db: DbSession,
    pagina: Annotated[int | None, Query(ge=1)] = None,
    tamanho_pagina: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[TurmaResponse] | PaginaResponse[TurmaResponse]:
    service = TurmaService(db)
    if usuario.perfil == PerfilUsuario.MASTER or usuario.tem_modulo("turmas"):
        filtro_polo, filtro_professor = None, None
    elif usuario.perfil == PerfilUsuario.GESTOR_POLO:
        filtro_polo, filtro_professor = usuario.polo_id, None
    elif usuario.perfil == PerfilUsuario.PROFESSOR:
        filtro_polo, filtro_professor = None, usuario.id
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil sem permissão para executar esta ação.")

    if pagina is None:
        turmas = service.listar(polo_id=filtro_polo, professor_id=filtro_professor)
        return [TurmaResponse(**t) for t in turmas]

    turmas, total = service.listar_pagina(
        pagina=pagina, tamanho_pagina=tamanho_pagina, polo_id=filtro_polo, professor_id=filtro_professor
    )
    return PaginaResponse(
        itens=[TurmaResponse(**t) for t in turmas], total=total, pagina=pagina, tamanho_pagina=tamanho_pagina
    )


@router.post(
    "",
    response_model=TurmaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar turma",
    description="MASTER cria em qualquer polo. GESTOR_POLO só cria turmas no seu próprio polo.",
)
def criar_turma(body: TurmaCreateRequest, usuario: MasterOuGestor, db: DbSession) -> TurmaResponse:
    assert_acesso_ao_polo(usuario, body.polo_id, "turmas")  # bloqueia gestor de outro polo
    service = TurmaService(db)
    criada = service.criar(
        polo_id=body.polo_id, modalidade_id=body.modalidade_id, professor_id=body.professor_id,
        horario_inicio=body.horario_inicio, horario_fim=body.horario_fim,
        dias_semana=body.dias_semana, limite_vagas=body.limite_vagas,
        coordenador_nome=body.coordenador_nome, monitor_nome=body.monitor_nome,
        periodicidade=body.periodicidade,
    )
    return TurmaResponse(**criada)


@router.patch(
    "/{turma_id}",
    response_model=TurmaResponse,
    summary="Editar turma / vincular professor",
    description="MASTER e GESTOR_POLO (do próprio polo) podem editar. É aqui que o "
    "gestor vincula um PROFESSOR à turma via `professor_id`.",
)
def atualizar_turma(
    turma_id: UUID, body: TurmaUpdateRequest, usuario: MasterOuGestor, db: DbSession
) -> TurmaResponse:
    assert_acesso_a_turma(usuario, db, turma_id, "turmas")
    service = TurmaService(db)
    atualizada = service.atualizar(turma_id, **body.model_dump(exclude_unset=True))
    if not atualizada:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return TurmaResponse(**atualizada)


@router.get(
    "/{turma_id}/lista-presenca/exportar",
    summary="Exportar Lista de Presença mensal da turma em .xlsx ou .pdf",
    description="Gera o arquivo preenchido no layout oficial do modelo, com a grade de "
    "presença (P/A) do mês a partir dos registros de frequência já lançados. MASTER e "
    "GESTOR_POLO exportam qualquer turma do seu escopo; PROFESSOR só a(s) sua(s). "
    "`formato=pdf` converte via LibreOffice, preservando o layout.",
)
def exportar_lista_presenca(
    turma_id: UUID,
    usuario: QualquerPerfil,
    db: DbSession,
    mes: Annotated[int, Query(ge=1, le=12)],
    ano: Annotated[int, Query(ge=2000, le=2100)],
    formato: Literal["xlsx", "pdf"] = "xlsx",
) -> Response:
    assert_acesso_a_turma(usuario, db, turma_id, "turmas")
    buffer = RelatorioService(db).gerar_lista_presenca(turma_id, mes, ano)
    return resposta_relatorio(buffer, f"Lista de Presenca - {mes:02d}-{ano}", "xlsx", formato)
