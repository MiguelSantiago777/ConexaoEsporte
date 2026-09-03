"""
Rotas de BENEFICIÁRIOS (nomenclatura oficial e obrigatória). Tag Swagger: 'Beneficiários'.
Nunca usar 'aluno' em nenhum ponto da API.
"""
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response

from app.application.beneficiario.documento_service import BeneficiarioDocumentoService
from app.application.beneficiario.service import BeneficiarioService
from app.application.matricula.service import MatriculaService
from app.core.dependencies import (
    CurrentUser,
    DbSession,
    UsuarioAutenticado,
    assert_acesso_a_turma,
    assert_acesso_ao_polo,
    require_modulo_ou_perfis,
)
from app.domain.enums import PerfilUsuario
from app.infrastructure.storage.armazenamento_documentos import armazenamento_documentos
from app.interfaces.api.v1.schemas.beneficiario_schemas import (
    BeneficiarioCreateRequest,
    BeneficiarioDocumentoResponse,
    BeneficiarioResponse,
    BeneficiarioUpdateRequest,
)
from app.interfaces.api.v1.schemas.matricula_schemas import MatriculaCreateRequest, MatriculaResponse
from app.interfaces.api.v1.schemas.paginacao_schemas import PaginaResponse

router = APIRouter(prefix="/beneficiarios", tags=["Beneficiários"])

MasterOuGestor = Annotated[
    UsuarioAutenticado, Depends(require_modulo_ou_perfis("beneficiarios", PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO))
]


def _assert_acesso_ao_beneficiario(usuario: UsuarioAutenticado, db: DbSession, beneficiario_id: UUID) -> None:
    """GESTOR_POLO só acessa beneficiários do seu polo. MASTER e
    PERSONALIZADO (módulo beneficiarios) têm acesso irrestrito."""
    if usuario.perfil == PerfilUsuario.MASTER or usuario.tem_modulo("beneficiarios"):
        return

    from app.infrastructure.database.models import BeneficiarioModel  # evita import circular

    beneficiario = db.get(BeneficiarioModel, beneficiario_id)
    if beneficiario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiário não encontrado.")
    assert_acesso_ao_polo(usuario, beneficiario.polo_id)


@router.get(
    "",
    response_model=list[BeneficiarioResponse] | PaginaResponse[BeneficiarioResponse],
    summary="Listar beneficiários",
    description="MASTER vê todos (filtrando opcionalmente por `polo_id`). GESTOR_POLO vê os do seu polo. "
    "PROFESSOR vê os das suas turmas (informe `turma_id`). Informe `pagina` pra paginar — sem "
    "isso, devolve a lista inteira (uso por telas que só precisam das opções, como um <select>).",
)
def listar_beneficiarios(
    usuario: CurrentUser, db: DbSession,
    turma_id: UUID | None = None,
    polo_id: UUID | None = None,
    nome: str | None = None,
    pagina: Annotated[int | None, Query(ge=1)] = None,
    tamanho_pagina: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[BeneficiarioResponse] | PaginaResponse[BeneficiarioResponse]:
    service = BeneficiarioService(db)
    if usuario.perfil == PerfilUsuario.MASTER or usuario.tem_modulo("beneficiarios"):
        filtro_polo = polo_id
    elif usuario.perfil == PerfilUsuario.GESTOR_POLO:
        filtro_polo = usuario.polo_id
    elif usuario.perfil == PerfilUsuario.PROFESSOR:
        if not turma_id:
            raise HTTPException(status_code=400, detail="Professor deve informar turma_id.")
        assert_acesso_a_turma(usuario, db, turma_id, "beneficiarios")
        filtro_polo = None
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil sem permissão para executar esta ação.")

    if pagina is None:
        itens = service.listar(polo_id=filtro_polo, turma_id=turma_id)
        return [BeneficiarioResponse.model_validate(b) for b in itens]

    itens, total = service.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, polo_id=filtro_polo, nome=nome)
    return PaginaResponse(
        itens=[BeneficiarioResponse.model_validate(b) for b in itens],
        total=total, pagina=pagina, tamanho_pagina=tamanho_pagina,
    )


@router.post(
    "",
    response_model=BeneficiarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar beneficiário",
    description="MASTER e GESTOR_POLO (no próprio polo) podem cadastrar. Valida documento único e "
    "responsável legal para menores de idade. A matrícula em turmas/modalidades é feita à parte "
    "(`POST /beneficiarios/{id}/matriculas`), pois um beneficiário pode estar em várias ao mesmo tempo.",
)
def criar_beneficiario(
    body: BeneficiarioCreateRequest, usuario: MasterOuGestor, db: DbSession
) -> BeneficiarioResponse:
    assert_acesso_ao_polo(usuario, body.polo_id, "beneficiarios")
    service = BeneficiarioService(db)
    criado = service.criar(
        nome_completo=body.nome_completo, data_nascimento=body.data_nascimento,
        documento=body.documento, polo_id=body.polo_id,
        responsavel_legal_nome=body.responsavel_legal_nome,
        responsavel_legal_data_nascimento=body.responsavel_legal_data_nascimento,
        responsavel_legal_tipo_relacao=body.responsavel_legal_tipo_relacao,
        responsavel_legal_telefone_1=body.responsavel_legal_telefone_1,
        responsavel_legal_telefone_2=body.responsavel_legal_telefone_2,
        responsavel_legal_email=body.responsavel_legal_email,
        responsavel_legal_rede_social=body.responsavel_legal_rede_social,
        endereco=body.endereco, autoriza_whatsapp=body.autoriza_whatsapp,
        observacoes_medicas=body.observacoes_medicas,
    )
    return BeneficiarioResponse.model_validate(criado)


@router.patch(
    "/{beneficiario_id}",
    response_model=BeneficiarioResponse,
    summary="Editar beneficiário",
)
def atualizar_beneficiario(
    beneficiario_id: UUID, body: BeneficiarioUpdateRequest, usuario: MasterOuGestor, db: DbSession
) -> BeneficiarioResponse:
    _assert_acesso_ao_beneficiario(usuario, db, beneficiario_id)
    if body.polo_id:
        assert_acesso_ao_polo(usuario, body.polo_id, "beneficiarios")
    service = BeneficiarioService(db)
    atualizado = service.atualizar(beneficiario_id, **body.model_dump(exclude_unset=True))
    if not atualizado:
        raise HTTPException(status_code=404, detail="Beneficiário não encontrado.")
    return BeneficiarioResponse.model_validate(atualizado)


# ---------------------------------------------------------------------
# Matrículas (vínculo N:N com turmas/modalidades) — um beneficiário pode
# estar matriculado em várias turmas ao mesmo tempo.
# ---------------------------------------------------------------------


@router.post(
    "/{beneficiario_id}/matriculas",
    response_model=MatriculaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Matricular beneficiário numa turma",
    description="Vincula o beneficiário a uma turma/modalidade. Ele pode ter várias matrículas "
    "ativas simultâneas (ex.: judô e natação). A turma precisa pertencer ao mesmo polo do "
    "beneficiário e ter vaga disponível.",
)
def matricular_beneficiario(
    beneficiario_id: UUID, body: MatriculaCreateRequest, usuario: MasterOuGestor, db: DbSession
) -> MatriculaResponse:
    _assert_acesso_ao_beneficiario(usuario, db, beneficiario_id)
    assert_acesso_a_turma(usuario, db, body.turma_id, "beneficiarios")
    service = MatriculaService(db)
    matricula = service.matricular(beneficiario_id, body.turma_id)
    return MatriculaResponse.model_validate(matricula)


@router.get(
    "/{beneficiario_id}/matriculas",
    response_model=list[MatriculaResponse],
    summary="Listar matrículas do beneficiário",
)
def listar_matriculas(beneficiario_id: UUID, usuario: MasterOuGestor, db: DbSession) -> list[MatriculaResponse]:
    _assert_acesso_ao_beneficiario(usuario, db, beneficiario_id)
    service = MatriculaService(db)
    return [MatriculaResponse.model_validate(m) for m in service.listar_por_beneficiario(beneficiario_id)]


@router.patch(
    "/{beneficiario_id}/matriculas/{matricula_id}",
    response_model=MatriculaResponse,
    summary="Encerrar uma matrícula",
    description="Desativa o vínculo do beneficiário com aquela turma (libera a vaga), sem afetar "
    "as demais matrículas dele nem o histórico de frequência/relatórios já lançado.",
)
def desmatricular_beneficiario(
    beneficiario_id: UUID, matricula_id: UUID, usuario: MasterOuGestor, db: DbSession
) -> MatriculaResponse:
    _assert_acesso_ao_beneficiario(usuario, db, beneficiario_id)
    service = MatriculaService(db)
    matricula = service.desmatricular(beneficiario_id, matricula_id)
    return MatriculaResponse.model_validate(matricula)


# ---------------------------------------------------------------------
# Documentos anexos (certidão de nascimento/identidade, identidade do
# responsável, comprovante de residência, comprovante escolar).
# ---------------------------------------------------------------------


@router.post(
    "/{beneficiario_id}/documentos",
    response_model=list[BeneficiarioDocumentoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Enviar documentos do beneficiário",
    description="Envia um ou mais anexos (multipart/form-data). Cada campo é opcional; envie só os "
    "arquivos que quiser anexar nesta chamada. Tipos aceitos: PDF, JPG, PNG, WEBP — até 10MB cada.",
)
async def enviar_documentos(
    beneficiario_id: UUID,
    usuario: MasterOuGestor,
    db: DbSession,
    foto: UploadFile | None = File(default=None),
    certidao_nascimento_ou_identidade: UploadFile | None = File(default=None),
    identidade_responsavel: UploadFile | None = File(default=None),
    comprovante_residencia: UploadFile | None = File(default=None),
    comprovante_escolar: UploadFile | None = File(default=None),
) -> list[BeneficiarioDocumentoResponse]:
    _assert_acesso_ao_beneficiario(usuario, db, beneficiario_id)

    enviados = {
        "foto": foto,
        "certidao_nascimento_ou_identidade": certidao_nascimento_ou_identidade,
        "identidade_responsavel": identidade_responsavel,
        "comprovante_residencia": comprovante_residencia,
        "comprovante_escolar": comprovante_escolar,
    }
    arquivos = {tipo: arquivo for tipo, arquivo in enviados.items() if arquivo is not None}
    if not arquivos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum arquivo enviado.")

    service = BeneficiarioDocumentoService(db)
    criados = [
        await service.enviar(beneficiario_id, tipo, arquivo, usuario.id)
        for tipo, arquivo in arquivos.items()
    ]
    return [BeneficiarioDocumentoResponse.model_validate(d) for d in criados]


@router.get(
    "/{beneficiario_id}/documentos",
    response_model=list[BeneficiarioDocumentoResponse],
    summary="Listar documentos anexados do beneficiário",
)
def listar_documentos(beneficiario_id: UUID, usuario: MasterOuGestor, db: DbSession) -> list[BeneficiarioDocumentoResponse]:
    _assert_acesso_ao_beneficiario(usuario, db, beneficiario_id)
    service = BeneficiarioDocumentoService(db)
    return [BeneficiarioDocumentoResponse.model_validate(d) for d in service.listar(beneficiario_id)]


@router.get(
    "/documentos/{documento_id}/arquivo",
    summary="Baixar um documento anexado",
    description="Retorna o arquivo binário (PDF/imagem). Acesso restrito ao polo do beneficiário dono do documento.",
)
def baixar_documento(documento_id: UUID, usuario: MasterOuGestor, db: DbSession) -> Response:
    service = BeneficiarioDocumentoService(db)
    documento = service.buscar(documento_id)
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")
    _assert_acesso_ao_beneficiario(usuario, db, documento.beneficiario_id)

    with armazenamento_documentos.abrir(documento.caminho_arquivo) as f:
        conteudo = f.read()

    # O nome do arquivo veio do upload do usuário — nunca interpolar bruto no
    # header. Uma aspa ou quebra de linha no nome poderiam quebrar o
    # Content-Disposition (e, em clientes antigos, falsificar a extensão
    # exibida). filename= (ASCII) é o fallback; filename*= (RFC 5987/6266)
    # carrega o nome original em UTF-8 para os navegadores que o suportam.
    nome_seguro = documento.nome_arquivo.replace("\\", "_").replace('"', "_")
    nome_ascii = nome_seguro.encode("ascii", errors="replace").decode("ascii")
    content_disposition = f'attachment; filename="{nome_ascii}"; filename*=UTF-8\'\'{quote(nome_seguro)}'
    return Response(
        content=conteudo,
        media_type=documento.content_type or "application/octet-stream",
        headers={"Content-Disposition": content_disposition},
    )
