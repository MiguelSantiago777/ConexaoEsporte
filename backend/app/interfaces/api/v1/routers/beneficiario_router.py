"""
Rotas de BENEFICIÁRIOS (nomenclatura oficial e obrigatória). Tag Swagger: 'Beneficiários'.
Nunca usar 'aluno' em nenhum ponto da API.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.beneficiario.service import BeneficiarioService
from app.core.dependencies import (
    CurrentUser,
    DbSession,
    UsuarioAutenticado,
    assert_acesso_a_turma,
    require_perfis,
)
from app.domain.enums import PerfilUsuario
from app.domain.shared.exceptions import RegraDeNegocioViolada
from app.interfaces.api.v1.schemas.beneficiario_schemas import (
    BeneficiarioCreateRequest,
    BeneficiarioResponse,
    BeneficiarioUpdateRequest,
)

router = APIRouter(prefix="/beneficiarios", tags=["Beneficiários"])

MasterOuGestor = Annotated[
    UsuarioAutenticado, Depends(require_perfis(PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO))
]


@router.get(
    "",
    response_model=list[BeneficiarioResponse],
    summary="Listar beneficiários",
    description="MASTER vê todos. GESTOR_POLO vê os do seu polo. PROFESSOR vê os das suas turmas "
    "(informe `turma_id`).",
)
def listar_beneficiarios(
    usuario: CurrentUser, db: DbSession, turma_id: UUID | None = None
) -> list[BeneficiarioResponse]:
    service = BeneficiarioService(db)
    if usuario.perfil == PerfilUsuario.MASTER:
        itens = service.listar(turma_id=turma_id)
    elif usuario.perfil == PerfilUsuario.GESTOR_POLO:
        itens = service.listar(polo_id=usuario.polo_id, turma_id=turma_id)
    else:  # PROFESSOR: obrigatório informar turma e ter acesso a ela
        if not turma_id:
            raise HTTPException(status_code=400, detail="Professor deve informar turma_id.")
        assert_acesso_a_turma(usuario, db, turma_id)
        itens = service.listar(turma_id=turma_id)
    return [BeneficiarioResponse.model_validate(b) for b in itens]


@router.post(
    "",
    response_model=BeneficiarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar beneficiário",
    description="MASTER e GESTOR_POLO (no próprio polo) podem cadastrar. Valida documento único, "
    "responsável legal para menores de idade e disponibilidade de vaga na turma.",
)
def criar_beneficiario(
    body: BeneficiarioCreateRequest, usuario: MasterOuGestor, db: DbSession
) -> BeneficiarioResponse:
    if body.turma_id:
        assert_acesso_a_turma(usuario, db, body.turma_id)
    service = BeneficiarioService(db)
    try:
        criado = service.criar(
            nome_completo=body.nome_completo, data_nascimento=body.data_nascimento,
            documento=body.documento, responsavel_legal_nome=body.responsavel_legal_nome,
            responsavel_legal_contato=body.responsavel_legal_contato, contato=body.contato,
            endereco=body.endereco, turma_id=body.turma_id, observacoes_medicas=body.observacoes_medicas,
        )
    except (RegraDeNegocioViolada, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return BeneficiarioResponse.model_validate(criado)


@router.patch(
    "/{beneficiario_id}",
    response_model=BeneficiarioResponse,
    summary="Editar beneficiário",
)
def atualizar_beneficiario(
    beneficiario_id: UUID, body: BeneficiarioUpdateRequest, usuario: MasterOuGestor, db: DbSession
) -> BeneficiarioResponse:
    service = BeneficiarioService(db)
    try:
        atualizado = service.atualizar(beneficiario_id, **body.model_dump(exclude_unset=True))
    except (RegraDeNegocioViolada, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not atualizado:
        raise HTTPException(status_code=404, detail="Beneficiário não encontrado.")
    return BeneficiarioResponse.model_validate(atualizado)
