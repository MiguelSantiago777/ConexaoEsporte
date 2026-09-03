"""Rotas de Polos. Tag Swagger: 'Polos'. Somente MASTER gerencia Polos."""
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.application.polo.service import PoloService
from app.application.relatorios.service import RelatorioService
from app.core.dependencies import (
    CurrentUser,
    DbSession,
    UsuarioAutenticado,
    assert_acesso_ao_polo,
    require_modulo_ou_perfis,
)
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.routers._arquivo_helper import resposta_relatorio
from app.interfaces.api.v1.schemas.paginacao_schemas import PaginaResponse
from app.interfaces.api.v1.schemas.polo_schemas import PoloCreateRequest, PoloResponse, PoloUpdateRequest

router = APIRouter(prefix="/polos", tags=["Polos"])

SomenteMaster = Annotated[
    UsuarioAutenticado, Depends(require_modulo_ou_perfis("polos", PerfilUsuario.MASTER))
]
MasterOuGestor = Annotated[
    UsuarioAutenticado,
    Depends(require_modulo_ou_perfis("polos", PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO)),
]


@router.get(
    "",
    response_model=list[PoloResponse] | PaginaResponse[PoloResponse],
    summary="Listar polos",
    description="MASTER vê todos os polos (informe `pagina` pra paginar — sem isso, devolve a lista "
    "inteira, uso por telas que só precisam das opções, como um <select>). GESTOR_POLO vê apenas o seu.",
)
def listar_polos(
    usuario: CurrentUser, db: DbSession,
    nome: str | None = None,
    pagina: Annotated[int | None, Query(ge=1)] = None,
    tamanho_pagina: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[PoloResponse] | PaginaResponse[PoloResponse]:
    service = PoloService(db)

    if usuario.perfil == PerfilUsuario.GESTOR_POLO:
        todos = [p for p in service.listar() if p.id == usuario.polo_id]
        return [PoloResponse.model_validate(p) for p in todos]

    if pagina is None:
        return [PoloResponse.model_validate(p) for p in service.listar()]

    polos, total = service.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, nome=nome)
    return PaginaResponse(
        itens=[PoloResponse.model_validate(p) for p in polos], total=total, pagina=pagina, tamanho_pagina=tamanho_pagina
    )


@router.post(
    "",
    response_model=PoloResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar polo (somente MASTER)",
)
def criar_polo(body: PoloCreateRequest, usuario: SomenteMaster, db: DbSession) -> PoloResponse:
    service = PoloService(db)
    criado = service.criar(
        nome=body.nome, codigo=body.codigo, endereco=body.endereco,
        horario_funcionamento=body.horario_funcionamento, gestor_responsavel_id=body.gestor_responsavel_id,
        processo_sei=body.processo_sei, termo_fomento_numero=body.termo_fomento_numero,
        nome_entidade=body.nome_entidade, cnpj=body.cnpj,
        representante_legal_nome=body.representante_legal_nome,
        representante_legal_cpf=body.representante_legal_cpf, objeto=body.objeto,
        vigencia_inicio=body.vigencia_inicio, vigencia_fim=body.vigencia_fim,
        valor_pactuado=body.valor_pactuado, valor_executado=body.valor_executado,
        parlamentar=body.parlamentar, emenda=body.emenda,
        # termos_aditivos é coluna JSON — precisa de valores serializáveis
        # (mode="json" converte `date` em string ISO).
        termos_aditivos=[item.model_dump(mode="json") for item in body.termos_aditivos],
        responsavel_nome=body.responsavel_nome, responsavel_email=body.responsavel_email,
        responsavel_telefone=body.responsavel_telefone,
        representante_legal_rg=body.representante_legal_rg,
        representante_legal_endereco=body.representante_legal_endereco,
        representante_legal_bairro=body.representante_legal_bairro,
        representante_legal_cidade=body.representante_legal_cidade,
        latitude=body.latitude, longitude=body.longitude,
    )
    return PoloResponse.model_validate(criado)


@router.patch(
    "/{polo_id}",
    response_model=PoloResponse,
    summary="Editar polo (somente MASTER)",
)
def atualizar_polo(polo_id: UUID, body: PoloUpdateRequest, usuario: SomenteMaster, db: DbSession) -> PoloResponse:
    campos = body.model_dump(exclude_unset=True)
    if campos.get("termos_aditivos") is not None:
        # termos_aditivos é uma coluna JSON — precisa de valores serializáveis
        # (mode="json" converte `date` em string ISO), diferente dos demais
        # campos de data do formulário, que são colunas DATE nativas e devem
        # continuar como objetos `date` para o SQLAlchemy.
        campos["termos_aditivos"] = [item.model_dump(mode="json") for item in body.termos_aditivos]
    service = PoloService(db)
    atualizado = service.atualizar(polo_id, **campos)
    if not atualizado:
        raise HTTPException(status_code=404, detail="Polo não encontrado.")
    return PoloResponse.model_validate(atualizado)


@router.get(
    "/{polo_id}/grade-horaria/exportar",
    summary="Exportar Grade Horária do polo em .docx",
    description="Gera o arquivo preenchido no layout oficial do modelo, com a carga horária "
    "semanal de cada turma do polo (Segunda/Quarta/Sexta) e as horas de planejamento informadas.",
)
def exportar_grade_horaria(
    polo_id: UUID,
    usuario: MasterOuGestor,
    db: DbSession,
    planejamento_horas: Annotated[float, Query(ge=0)] = 0,
    formato: Literal["docx", "pdf"] = "docx",
) -> Response:
    assert_acesso_ao_polo(usuario, polo_id, "polos")
    buffer = RelatorioService(db).gerar_grade_horaria(polo_id, planejamento_horas)
    return resposta_relatorio(buffer, "Grade Horaria", "docx", formato)


@router.get(
    "/{polo_id}/planilha-nucleos/exportar",
    summary="Exportar Planilha de Núcleos — RH e Beneficiário em .xlsx",
    description="Gera o arquivo preenchido no layout oficial do modelo, com a equipe (RH) e os "
    "beneficiários ativos do polo. RH vem do cadastro de usuários (GESTOR_POLO/PROFESSOR do polo, "
    "com telefone e carga horária preenchidos em Professores/Usuários).",
)
def exportar_planilha_nucleos(
    polo_id: UUID, usuario: MasterOuGestor, db: DbSession, formato: Literal["xlsx", "pdf"] = "xlsx"
) -> Response:
    assert_acesso_ao_polo(usuario, polo_id, "polos")
    buffer = RelatorioService(db).gerar_planilha_nucleos(polo_id)
    return resposta_relatorio(buffer, "Planilha de Nucleos", "xlsx", formato)


@router.get(
    "/{polo_id}/termo-responsabilidade/exportar",
    summary="Exportar Termo de Responsabilidade em .docx",
    description="Gera o termo preenchido com os dados pessoais do representante legal "
    "cadastrados no polo (nome, RG, CPF, endereço), pronto para assinatura.",
)
def exportar_termo_responsabilidade(
    polo_id: UUID, usuario: MasterOuGestor, db: DbSession, formato: Literal["docx", "pdf"] = "docx"
) -> Response:
    assert_acesso_ao_polo(usuario, polo_id, "polos")
    buffer = RelatorioService(db).gerar_termo_responsabilidade(polo_id)
    return resposta_relatorio(buffer, "Termo de Responsabilidade", "docx", formato)
