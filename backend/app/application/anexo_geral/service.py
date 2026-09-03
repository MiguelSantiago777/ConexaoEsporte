"""Use cases do repositório livre de Anexos Gerais por polo."""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.anexo_geral.entities import AnexoGeral
from app.domain.shared.exceptions import ArquivoMuitoGrande, RecursoNaoEncontrado, TipoArquivoNaoSuportado
from app.infrastructure.repositories.almoxarifado_repository import AlmoxarifadoRepository
from app.infrastructure.repositories.anexo_geral_repository import AnexoGeralRepository
from app.infrastructure.repositories.chamada_evidencia_repository import ChamadaEvidenciaRepository
from app.infrastructure.repositories.entrega_material_repository import EntregaMaterialRepository
from app.infrastructure.repositories.modalidade_repository import ModalidadeRepository
from app.infrastructure.repositories.movimento_estoque_repository import MovimentoEstoqueRepository
from app.infrastructure.repositories.polo_repository import PoloRepository
from app.infrastructure.repositories.produto_repository import ProdutoRepository
from app.infrastructure.repositories.relatorio_aula_repository import RelatorioAulaRepository
from app.infrastructure.repositories.turma_repository import TurmaRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.infrastructure.storage.armazenamento_documentos import armazenamento_anexos_gerais
from app.interfaces.api.v1.schemas.anexo_geral_schemas import DocumentoConsolidadoResponse

CONTENT_TYPES_ACEITOS = {"application/pdf", "image/jpeg", "image/png", "image/webp"}


class AnexoGeralService:
    def __init__(self, db: Session):
        self.repo = AnexoGeralRepository(db)
        self.polo_repo = PoloRepository(db)
        self.turma_repo = TurmaRepository(db)
        self.modalidade_repo = ModalidadeRepository(db)
        self.usuario_repo = UsuarioRepository(db)
        self.evidencia_repo = ChamadaEvidenciaRepository(db)
        self.relatorio_repo = RelatorioAulaRepository(db)
        self.produto_repo = ProdutoRepository(db)
        self.movimento_repo = MovimentoEstoqueRepository(db)
        self.entrega_repo = EntregaMaterialRepository(db)
        self.almoxarifado_repo = AlmoxarifadoRepository(db)

    def listar(self, polo_id: UUID | None = None) -> list[AnexoGeral]:
        return self.repo.listar(polo_id=polo_id)

    def listar_consolidado(self, polo_id: UUID | None = None) -> list[DocumentoConsolidadoResponse]:
        """Visão somente leitura reunindo, por ordem de envio mais recente:
        os Anexos Gerais enviados pelos polos/gestores, as fotos de evidência
        e as observações de relatório de aula que os professores registram
        ao lançar a chamada."""
        polos_por_id = {p.id: p.nome for p in self.polo_repo.listar()}
        modalidades_por_id = {m.id: m.nome for m in self.modalidade_repo.listar()}
        turmas = self.turma_repo.listar(polo_id=polo_id)
        turmas_por_id = {t.id: t for t in turmas}
        turma_ids = list(turmas_por_id.keys())

        nomes_usuarios: dict[UUID, str] = {}

        def nome_usuario(usuario_id: UUID | None) -> str | None:
            if not usuario_id:
                return None
            if usuario_id not in nomes_usuarios:
                usuario = self.usuario_repo.buscar_por_id(usuario_id)
                nomes_usuarios[usuario_id] = usuario.nome if usuario else "—"
            return nomes_usuarios[usuario_id]

        def nome_turma(turma_id: UUID) -> str | None:
            turma = turmas_por_id.get(turma_id)
            if not turma:
                return None
            modalidade_nome = modalidades_por_id.get(turma.modalidade_id, "—")
            return f"{modalidade_nome} — {turma.horario_inicio}–{turma.horario_fim}"

        documentos: list[DocumentoConsolidadoResponse] = []

        agora = datetime.now(timezone.utc)

        for anexo in self.repo.listar(polo_id=polo_id):
            documentos.append(
                DocumentoConsolidadoResponse(
                    id=anexo.id, tipo="ANEXO_GERAL", titulo=anexo.titulo,
                    polo_id=anexo.polo_id, polo_nome=polos_por_id.get(anexo.polo_id, "—"),
                    autor_nome=nome_usuario(anexo.enviado_por_id),
                    data_evento=(anexo.criado_em or agora).date(),
                    criado_em=anexo.criado_em, nome_arquivo=anexo.nome_arquivo,
                    content_type=anexo.content_type, possui_arquivo=True,
                )
            )

        for evidencia in self.evidencia_repo.listar_por_turmas(turma_ids):
            turma = turmas_por_id.get(evidencia.turma_id)
            if not turma:
                continue
            documentos.append(
                DocumentoConsolidadoResponse(
                    id=evidencia.id, tipo="EVIDENCIA_CHAMADA", titulo="Foto de evidência de chamada",
                    polo_id=turma.polo_id, polo_nome=polos_por_id.get(turma.polo_id, "—"),
                    turma_nome=nome_turma(evidencia.turma_id),
                    autor_nome=nome_usuario(evidencia.enviado_por_id),
                    data_evento=evidencia.data, criado_em=evidencia.criado_em,
                    nome_arquivo=evidencia.nome_arquivo, content_type=evidencia.content_type,
                    possui_arquivo=True,
                )
            )

        for relatorio in self.relatorio_repo.listar_por_turmas(turma_ids):
            if not relatorio.observacoes or not relatorio.observacoes.strip():
                continue
            turma = turmas_por_id.get(relatorio.turma_id)
            if not turma:
                continue
            documentos.append(
                DocumentoConsolidadoResponse(
                    id=relatorio.id, tipo="OBSERVACAO_AULA", titulo="Observação de aula",
                    descricao=relatorio.observacoes,
                    polo_id=turma.polo_id, polo_nome=polos_por_id.get(turma.polo_id, "—"),
                    turma_nome=nome_turma(relatorio.turma_id),
                    autor_nome=nome_usuario(relatorio.professor_id),
                    data_evento=relatorio.data, criado_em=relatorio.criado_em,
                    possui_arquivo=False,
                )
            )

        # Entrada de estoque é um lançamento central (não pertence a nenhum
        # polo), então só entra na visão "todos os polos" — quando a listagem
        # é filtrada por polo_id, ela some da lista, exatamente como o
        # catálogo de Estoque já é invisível pra quem não tem acesso a ele.
        if polo_id is None:
            produtos_por_id = {p.id: p for p in self.produto_repo.listar()}
            almoxarifados_por_id = {a.id: a.nome for a in self.almoxarifado_repo.listar()}
            for movimento in self.movimento_repo.listar(tipo="ENTRADA"):
                if not movimento.nome_arquivo:
                    continue
                produto = produtos_por_id.get(movimento.produto_id)
                produto_nome = produto.nome if produto else "—"
                unidade = produto.unidade_medida if produto else ""
                almoxarifado_nome = almoxarifados_por_id.get(movimento.almoxarifado_id, "Estoque Central")
                documentos.append(
                    DocumentoConsolidadoResponse(
                        id=movimento.id, tipo="ESTOQUE_ENTRADA", titulo=f"Entrada de estoque — {produto_nome}",
                        descricao=(
                            f"{movimento.quantidade} {unidade} · Entregue por: {movimento.entregue_por or '—'} "
                            f"· Recebido por: {movimento.recebido_por or '—'}"
                        ),
                        polo_id=None, polo_nome=almoxarifado_nome,
                        autor_nome=nome_usuario(movimento.criado_por_id),
                        data_evento=movimento.data, criado_em=movimento.criado_em,
                        nome_arquivo=movimento.nome_arquivo, content_type=movimento.content_type,
                        possui_arquivo=True,
                    )
                )

        for entrega in self.entrega_repo.listar(polo_id=polo_id):
            if not entrega.comprovante_nome_arquivo:
                continue
            data_evento = entrega.data_entrega or (entrega.criado_em.date() if entrega.criado_em else agora.date())
            documentos.append(
                DocumentoConsolidadoResponse(
                    id=entrega.id, tipo="ENTREGA_MATERIAIS", titulo="Comprovante de recebimento — Entrega de Materiais",
                    descricao=f"Entregue por: {entrega.entregue_por or '—'} · Recebido por: {entrega.coordenador_nome or '—'}",
                    polo_id=entrega.polo_id, polo_nome=polos_por_id.get(entrega.polo_id, "—"),
                    autor_nome=nome_usuario(entrega.criado_por_id),
                    data_evento=data_evento, criado_em=entrega.criado_em,
                    nome_arquivo=entrega.comprovante_nome_arquivo, content_type=entrega.comprovante_content_type,
                    possui_arquivo=True,
                )
            )

        documentos.sort(
            key=lambda d: d.criado_em or datetime.combine(d.data_evento, datetime.min.time(), tzinfo=timezone.utc),
            reverse=True,
        )
        return documentos

    def buscar(self, anexo_id: UUID) -> AnexoGeral | None:
        return self.repo.buscar_por_id(anexo_id)

    async def enviar(
        self, polo_id: UUID, titulo: str, arquivo: UploadFile, enviado_por_id: UUID
    ) -> AnexoGeral:
        if not self.polo_repo.buscar_por_id(polo_id):
            raise RecursoNaoEncontrado("Polo não encontrado.")

        if arquivo.content_type not in CONTENT_TYPES_ACEITOS:
            raise TipoArquivoNaoSuportado("Tipo de arquivo não permitido. Envie PDF, JPG, PNG ou WEBP.")

        conteudo = await arquivo.read()
        tamanho_maximo = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
        if len(conteudo) > tamanho_maximo:
            raise ArquivoMuitoGrande(f"Arquivo excede o limite de {settings.UPLOAD_MAX_SIZE_MB}MB.")

        caminho = armazenamento_anexos_gerais.salvar(str(polo_id), arquivo.filename or "arquivo", conteudo)

        anexo = AnexoGeral(
            id=None, polo_id=polo_id, titulo=titulo,
            nome_arquivo=arquivo.filename or "arquivo", caminho_arquivo=caminho,
            content_type=arquivo.content_type, tamanho_bytes=len(conteudo),
            enviado_por_id=enviado_por_id,
        )
        return self.repo.criar(anexo)

    def remover(self, anexo_id: UUID) -> None:
        anexo = self.repo.buscar_por_id(anexo_id)
        if not anexo:
            raise RecursoNaoEncontrado("Anexo não encontrado.")
        armazenamento_anexos_gerais.remover(anexo.caminho_arquivo)
        self.repo.remover(anexo_id)
