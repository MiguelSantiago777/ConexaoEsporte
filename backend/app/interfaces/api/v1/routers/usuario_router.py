"""Rotas de Usuários (funcionários). Tag Swagger: 'Usuários'."""
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response

from app.application.importacao.planilha import ler_planilha
from app.application.usuario.documento_service import UsuarioDocumentoService
from app.application.usuario.importacao_service import UsuarioImportacaoService
from app.application.usuario.service import UsuarioService
from app.core.dependencies import DbSession, UsuarioAutenticado, require_modulo_ou_perfis
from app.domain.enums import PerfilUsuario
from app.interfaces.api.v1.routers._arquivo_helper import resposta_download
from app.interfaces.api.v1.schemas.importacao_schemas import ResultadoImportacaoResponse
from app.interfaces.api.v1.schemas.paginacao_schemas import PaginaResponse
from app.interfaces.api.v1.schemas.usuario_schemas import (
    UsuarioCreateRequest,
    UsuarioDocumentoResponse,
    UsuarioResponse,
    UsuarioUpdateRequest,
)

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

# MASTER cria qualquer usuário; GESTOR_POLO só cria PROFESSOR no próprio
# polo. PERSONALIZADO com o módulo "professores" (Central de Acessos) tem
# o mesmo tipo de restrição do GESTOR_POLO, mas sem escopo de polo (o Papel
# não é vinculado a nenhum polo específico).
MasterOuGestor = Annotated[
    UsuarioAutenticado, Depends(require_modulo_ou_perfis("professores", PerfilUsuario.MASTER, PerfilUsuario.GESTOR_POLO))
]
SomenteMaster = Annotated[UsuarioAutenticado, Depends(require_modulo_ou_perfis("professores", PerfilUsuario.MASTER))]


def _assert_acesso_ao_usuario_alvo(usuario: UsuarioAutenticado, db: DbSession, usuario_alvo_id: UUID):
    """GESTOR_POLO só acessa anexos de professores do seu polo. PERSONALIZADO
    (módulo professores) só acessa anexos de professores, de qualquer polo.
    MASTER tem acesso irrestrito."""
    alvo = UsuarioService(db).buscar_usuario(usuario_alvo_id)
    if not alvo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    if usuario.perfil == PerfilUsuario.MASTER:
        return alvo
    if usuario.perfil == PerfilUsuario.PERSONALIZADO:
        if alvo.perfil != PerfilUsuario.PROFESSOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Só é possível acessar anexos de professores.",
            )
        return alvo
    if alvo.perfil != PerfilUsuario.PROFESSOR or alvo.polo_id != usuario.polo_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Gestor só pode acessar anexos de professores do próprio polo.",
        )
    return alvo


@router.post(
    "",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar usuário (funcionário)",
    description="**MASTER** pode cadastrar qualquer perfil. **GESTOR_POLO** pode "
    "cadastrar apenas **PROFESSOR**, sempre vinculado ao seu próprio polo. Se `senha` for omitida, o "
    "usuário recebe a senha temporária padrão (informe-a a ele por fora) e é obrigado a trocá-la no "
    "primeiro acesso.",
)
def criar_usuario(body: UsuarioCreateRequest, usuario: MasterOuGestor, db: DbSession) -> UsuarioResponse:
    service = UsuarioService(db)
    criado = service.criar_usuario(
        nome=body.nome, email=body.email, senha=body.senha, perfil=body.perfil,
        polo_id=body.polo_id, criado_por_perfil=usuario.perfil, criado_por_polo_id=usuario.polo_id,
        telefone=body.telefone, cpf=body.cpf, carga_horaria_semanal=body.carga_horaria_semanal,
        almoxarifado_id=body.almoxarifado_id, papel_id=body.papel_id,
    )
    return UsuarioResponse.model_validate(criado)


@router.get(
    "/importar/modelo",
    summary="Baixar modelo de planilha (.xlsx) para importação em massa de usuários/professores",
)
def baixar_modelo_importacao_usuarios(usuario: MasterOuGestor, db: DbSession) -> Response:
    polo_fixo_id = usuario.polo_id if usuario.perfil == PerfilUsuario.GESTOR_POLO else None
    buffer = UsuarioImportacaoService(db).gerar_modelo(usuario.perfil, polo_fixo_id)
    return resposta_download(
        buffer.getvalue(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "modelo-importacao-usuarios.xlsx",
    )


@router.post(
    "/importar",
    response_model=ResultadoImportacaoResponse,
    summary="Importar usuários/professores em massa a partir de planilha (.xlsx)",
    description="Envie o arquivo preenchido a partir do modelo (`GET /usuarios/importar/modelo`). Com "
    "`confirmar=false` (padrão) só valida e devolve a prévia — nada é gravado, nenhum e-mail é enviado. "
    "Com `confirmar=true` grava as linhas válidas (pulando as com erro); cada uma recebe a senha "
    "temporária padrão (obrigada a trocá-la no primeiro acesso) e, como bônus, um e-mail de aviso — a "
    "senha nunca vem da planilha.",
)
async def importar_usuarios(
    usuario: MasterOuGestor, db: DbSession,
    arquivo: UploadFile = File(...),
    confirmar: bool = Query(False),
) -> ResultadoImportacaoResponse:
    linhas = ler_planilha(await arquivo.read())
    resultado = UsuarioImportacaoService(db).importar(linhas, confirmar, usuario)
    return ResultadoImportacaoResponse.de_resultado(resultado)


@router.get(
    "",
    response_model=list[UsuarioResponse] | PaginaResponse[UsuarioResponse],
    summary="Listar usuários",
    description="MASTER lista todos. GESTOR_POLO lista apenas os do seu polo. Filtre por `perfil` "
    "(ex.: PROFESSOR) e informe `pagina` pra paginar — sem `pagina`, devolve a lista inteira.",
)
def listar_usuarios(
    usuario: MasterOuGestor, db: DbSession,
    perfil: PerfilUsuario | None = None,
    pagina: Annotated[int | None, Query(ge=1)] = None,
    tamanho_pagina: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[UsuarioResponse] | PaginaResponse[UsuarioResponse]:
    service = UsuarioService(db)
    filtro_polo = usuario.polo_id if usuario.perfil == PerfilUsuario.GESTOR_POLO else None
    # PERSONALIZADO (módulo professores) só enxerga professores — nunca a
    # lista de outros funcionários (MASTER, gestores etc.), mesmo pedindo
    # outro filtro de perfil.
    if usuario.perfil == PerfilUsuario.PERSONALIZADO:
        perfil = PerfilUsuario.PROFESSOR

    if pagina is None:
        itens = service.listar_usuarios(polo_id=filtro_polo)
        if perfil:
            itens = [u for u in itens if u.perfil == perfil]
        return [UsuarioResponse.model_validate(u) for u in itens]

    itens, total = service.listar_usuarios_pagina(
        pagina=pagina, tamanho_pagina=tamanho_pagina, polo_id=filtro_polo, perfil=perfil
    )
    return PaginaResponse(
        itens=[UsuarioResponse.model_validate(u) for u in itens], total=total, pagina=pagina, tamanho_pagina=tamanho_pagina
    )


@router.patch(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Editar usuário (funcionário)",
    description="**MASTER** pode editar qualquer usuário. **GESTOR_POLO** só pode editar "
    "**PROFESSOR** do próprio polo (ex.: telefone e carga horária para a Planilha de Núcleos).",
)
def atualizar_usuario(
    usuario_id: UUID, body: UsuarioUpdateRequest, usuario: MasterOuGestor, db: DbSession
) -> UsuarioResponse:
    service = UsuarioService(db)
    alvo = service.buscar_usuario(usuario_id)
    if not alvo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    if usuario.perfil == PerfilUsuario.GESTOR_POLO:
        if alvo.perfil != PerfilUsuario.PROFESSOR or alvo.polo_id != usuario.polo_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Gestor só pode editar professores do próprio polo.",
            )
        if body.polo_id is not None or body.ativo is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Gestor não pode alterar polo/situação do professor.",
            )
    elif usuario.perfil == PerfilUsuario.PERSONALIZADO:
        if alvo.perfil != PerfilUsuario.PROFESSOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Só é possível editar professores.",
            )

    atualizado = service.atualizar_usuario(usuario_id, **body.model_dump(exclude_unset=True))
    return UsuarioResponse.model_validate(atualizado)


@router.delete(
    "/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir usuário definitivamente (somente MASTER)",
    description="Exclusão de verdade — não é o mesmo que desativar (`PATCH` com `ativo=false`). "
    "**PROFESSOR nunca pode ser excluído aqui** (só desativado, pra preservar turmas/frequências já "
    "registradas). Pra qualquer outro perfil, recusa a exclusão se o usuário já tiver algo vinculado no "
    "sistema (anexos, entregas, movimentações etc.) — desative o acesso em vez de excluir nesse caso.",
)
def remover_usuario(usuario_id: UUID, usuario: SomenteMaster, db: DbSession) -> None:
    UsuarioService(db).remover_usuario(usuario_id)


@router.post(
    "/{usuario_id}/documentos",
    response_model=UsuarioDocumentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar anexo do professor (foto, documento ou contrato)",
    description="Envia um arquivo por chamada (multipart/form-data). Tipos aceitos: PDF, JPG, PNG, WEBP — "
    "até 10MB cada. Chame novamente para anexar mais de um documento do mesmo tipo.",
)
async def enviar_documento_usuario(
    usuario_id: UUID,
    usuario: MasterOuGestor,
    db: DbSession,
    tipo: Literal["FOTO", "DOCUMENTO", "CONTRATO"] = Form(...),
    arquivo: UploadFile = File(...),
) -> UsuarioDocumentoResponse:
    _assert_acesso_ao_usuario_alvo(usuario, db, usuario_id)
    criado = await UsuarioDocumentoService(db).enviar(usuario_id, tipo, arquivo, usuario.id)
    return UsuarioDocumentoResponse.model_validate(criado)


@router.get(
    "/{usuario_id}/documentos",
    response_model=list[UsuarioDocumentoResponse],
    summary="Listar anexos do professor",
)
def listar_documentos_usuario(usuario_id: UUID, usuario: MasterOuGestor, db: DbSession) -> list[UsuarioDocumentoResponse]:
    _assert_acesso_ao_usuario_alvo(usuario, db, usuario_id)
    return [UsuarioDocumentoResponse.model_validate(d) for d in UsuarioDocumentoService(db).listar(usuario_id)]


@router.get(
    "/documentos/{documento_id}/arquivo",
    summary="Baixar um anexo do professor",
    description="Retorna o arquivo binário (PDF/imagem). Acesso restrito ao polo do professor dono do anexo.",
)
def baixar_documento_usuario(documento_id: UUID, usuario: MasterOuGestor, db: DbSession) -> Response:
    service = UsuarioDocumentoService(db)
    documento = service.buscar(documento_id)
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")
    _assert_acesso_ao_usuario_alvo(usuario, db, documento.usuario_id)

    from app.infrastructure.storage.armazenamento_documentos import armazenamento_usuario_documentos

    with armazenamento_usuario_documentos.abrir(documento.caminho_arquivo) as f:
        conteudo = f.read()
    return resposta_download(conteudo, documento.content_type, documento.nome_arquivo)


@router.delete(
    "/documentos/{documento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover um anexo do professor",
)
def remover_documento_usuario(documento_id: UUID, usuario: MasterOuGestor, db: DbSession) -> None:
    service = UsuarioDocumentoService(db)
    documento = service.buscar(documento_id)
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")
    _assert_acesso_ao_usuario_alvo(usuario, db, documento.usuario_id)
    service.remover(documento_id)
