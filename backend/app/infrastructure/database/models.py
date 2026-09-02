"""
Modelos ORM (SQLAlchemy) — mapeiam 1:1 as tabelas de database/schema.sql.
Camada de Infraestrutura (DDD): estes modelos NÃO vazam para as regras de
negócio; a camada de Application/Domain trabalha com as entidades puras
definidas em app/domain/**/entities.py.
"""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid_col(primary_key: bool = False, fk: str | None = None, nullable: bool = False):
    kwargs = {"primary_key": primary_key, "nullable": nullable, "default": uuid.uuid4 if primary_key else None}
    if fk:
        return mapped_column(PG_UUID(as_uuid=True), ForeignKey(fk), **kwargs)
    return mapped_column(PG_UUID(as_uuid=True), **kwargs)


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[str] = mapped_column(String(20), nullable=False)  # MASTER | GESTOR_POLO | PROFESSOR
    polo_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("polos.id", use_alter=True), nullable=True
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # RH do núcleo (Planilha de Núcleos — RH e Beneficiário)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    carga_horaria_semanal: Mapped[str | None] = mapped_column(String(20), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    polo: Mapped["PoloModel"] = relationship(foreign_keys=[polo_id], back_populates="usuarios_vinculados")


class PoloModel(Base):
    __tablename__ = "polos"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    codigo: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    endereco: Mapped[str] = mapped_column(String(255), nullable=True)
    horario_funcionamento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ATIVO", nullable=False)
    gestor_responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )

    # Dados da parceria (Termo de Fomento) — próprios deste polo; cada polo
    # é sua própria entidade parceira para fins da Ficha Técnica de Execução.
    processo_sei: Mapped[str | None] = mapped_column(String(50), nullable=True)
    termo_fomento_numero: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nome_entidade: Mapped[str | None] = mapped_column(String(150), nullable=True)
    cnpj: Mapped[str | None] = mapped_column(String(20), nullable=True)
    representante_legal_nome: Mapped[str | None] = mapped_column(String(150), nullable=True)
    representante_legal_cpf: Mapped[str | None] = mapped_column(String(20), nullable=True)
    objeto: Mapped[str | None] = mapped_column(Text, nullable=True)
    vigencia_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    vigencia_fim: Mapped[date | None] = mapped_column(Date, nullable=True)
    valor_pactuado: Mapped[str | None] = mapped_column(String(50), nullable=True)
    valor_executado: Mapped[str | None] = mapped_column(String(50), nullable=True)
    parlamentar: Mapped[str | None] = mapped_column(String(150), nullable=True)
    emenda: Mapped[str | None] = mapped_column(String(100), nullable=True)
    termos_aditivos: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Contato do núcleo para a seção "Identificação dos Núcleos" da Ficha
    responsavel_nome: Mapped[str | None] = mapped_column(String(150), nullable=True)
    responsavel_email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    responsavel_telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Dados pessoais do representante legal para o Termo de Responsabilidade
    representante_legal_rg: Mapped[str | None] = mapped_column(String(20), nullable=True)
    representante_legal_endereco: Mapped[str | None] = mapped_column(String(255), nullable=True)
    representante_legal_bairro: Mapped[str | None] = mapped_column(String(100), nullable=True)
    representante_legal_cidade: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Coordenadas do endereço, para exibir o polo no mapa do Dashboard.
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    usuarios_vinculados: Mapped[list["UsuarioModel"]] = relationship(
        foreign_keys="UsuarioModel.polo_id", back_populates="polo"
    )
    turmas: Mapped[list["TurmaModel"]] = relationship(back_populates="polo")


class ModalidadeModel(Base):
    __tablename__ = "modalidades"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TurmaModel(Base):
    __tablename__ = "turmas"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    polo_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("polos.id"), nullable=False)
    modalidade_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("modalidades.id"), nullable=False
    )
    professor_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    horario_inicio: Mapped[str] = mapped_column(String(5), nullable=False)  # "HH:MM"
    horario_fim: Mapped[str] = mapped_column(String(5), nullable=False)
    dias_semana: Mapped[str] = mapped_column(String(50), nullable=False)  # ex: "SEG,QUA,SEX"
    limite_vagas: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    # Coordenador/monitor da turma para a Lista de Presença — não são
    # necessariamente usuários do sistema, por isso são só nomes de impressão.
    coordenador_nome: Mapped[str | None] = mapped_column(String(150), nullable=True)
    monitor_nome: Mapped[str | None] = mapped_column(String(150), nullable=True)
    periodicidade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    polo: Mapped["PoloModel"] = relationship(back_populates="turmas")
    modalidade: Mapped["ModalidadeModel"] = relationship()
    professor: Mapped["UsuarioModel | None"] = relationship(foreign_keys=[professor_id])
    matriculas: Mapped[list["MatriculaModel"]] = relationship(back_populates="turma")


class BeneficiarioModel(Base):
    __tablename__ = "beneficiarios"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    data_nascimento: Mapped[date] = mapped_column(Date, nullable=False)
    documento: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # CPF ou outro doc — sempre exclusivo do próprio beneficiário
    polo_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("polos.id"), nullable=True)
    responsavel_legal_nome: Mapped[str | None] = mapped_column(String(150), nullable=True)
    responsavel_legal_data_nascimento: Mapped[date | None] = mapped_column(Date, nullable=True)
    responsavel_legal_tipo_relacao: Mapped[str | None] = mapped_column(String(50), nullable=True)
    responsavel_legal_telefone_1: Mapped[str | None] = mapped_column(String(20), nullable=True)
    responsavel_legal_telefone_2: Mapped[str | None] = mapped_column(String(20), nullable=True)
    responsavel_legal_email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    responsavel_legal_rede_social: Mapped[str | None] = mapped_column(String(150), nullable=True)
    endereco: Mapped[str | None] = mapped_column(String(255), nullable=True)
    autoriza_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    observacoes_medicas: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    matriculas: Mapped[list["MatriculaModel"]] = relationship(
        back_populates="beneficiario", cascade="all, delete-orphan"
    )
    documentos: Mapped[list["BeneficiarioDocumentoModel"]] = relationship(
        back_populates="beneficiario", cascade="all, delete-orphan"
    )


class MatriculaModel(Base):
    """Vínculo N:N entre beneficiário e turma — permite o mesmo beneficiário
    matriculado em várias turmas/modalidades ao mesmo tempo."""

    __tablename__ = "matriculas"
    __table_args__ = (UniqueConstraint("beneficiario_id", "turma_id", name="uq_matricula_beneficiario_turma"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    beneficiario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("beneficiarios.id", ondelete="CASCADE"), nullable=False
    )
    turma_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("turmas.id", ondelete="CASCADE"), nullable=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    beneficiario: Mapped["BeneficiarioModel"] = relationship(back_populates="matriculas")
    turma: Mapped["TurmaModel"] = relationship(back_populates="matriculas")


class BeneficiarioDocumentoModel(Base):
    __tablename__ = "beneficiario_documentos"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    beneficiario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("beneficiarios.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    caminho_arquivo: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tamanho_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enviado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    beneficiario: Mapped["BeneficiarioModel"] = relationship(back_populates="documentos")


class FrequenciaModel(Base):
    __tablename__ = "frequencias"
    __table_args__ = (UniqueConstraint("turma_id", "beneficiario_id", "data", name="uq_frequencia_dia"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turma_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("turmas.id"), nullable=False)
    beneficiario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("beneficiarios.id"), nullable=False
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    presente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    falta_justificada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    justificativa: Mapped[str | None] = mapped_column(Text, nullable=True)
    registrado_por_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ImpeditivoAulaModel(Base):
    """Dia em que a turma inteira não teve aula (feriado etc.) — vale para
    todos os beneficiários matriculados naquela data."""

    __tablename__ = "impeditivos_aula"
    __table_args__ = (UniqueConstraint("turma_id", "data", name="uq_impeditivo_turma_dia"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turma_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("turmas.id"), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    justificativa: Mapped[str] = mapped_column(Text, nullable=False)
    criado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class UsuarioDocumentoModel(Base):
    """Anexos do cadastro de professor: foto, documentos e contrato."""

    __tablename__ = "usuario_documentos"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # FOTO | DOCUMENTO | CONTRATO
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    caminho_arquivo: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tamanho_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enviado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AnexoGeralModel(Base):
    """Repositório livre de documentos por polo, não ligados a um professor
    ou beneficiário específico (apólices, contratos de aluguel, atas etc.)."""

    __tablename__ = "anexos_gerais"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    polo_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("polos.id", ondelete="CASCADE"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    caminho_arquivo: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tamanho_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enviado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ConfiguracaoGeralModel(Base):
    """Registro único (singleton) com dados globais do projeto/convênio,
    exibidos no rodapé de todos os relatórios exportados."""

    __tablename__ = "configuracao_geral"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_projeto: Mapped[str | None] = mapped_column(String(200), nullable=True)
    numero_convenio: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_inicio_projeto: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_fim_projeto: Mapped[date | None] = mapped_column(Date, nullable=True)
    atualizado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ChamadaEvidenciaModel(Base):
    """Fotos anexadas pelo professor a uma chamada (turma + data), como
    comprovação de que a aula aconteceu."""

    __tablename__ = "chamada_evidencias"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turma_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("turmas.id"), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    caminho_arquivo: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tamanho_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enviado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RelatorioAulaModel(Base):
    __tablename__ = "relatorios_aula"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turma_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("turmas.id"), nullable=False)
    professor_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    conteudo_trabalhado: Mapped[str] = mapped_column(Text, nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class FichaExecucaoModel(Base):
    """Ficha Técnica de Execução da Entidade — uma por polo e por
    período/trimestre reportado (Portaria nº 102/2024). Só o MASTER
    cadastra/edita/exporta."""

    __tablename__ = "fichas_execucao"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    polo_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("polos.id"), nullable=True)
    periodo_referencia: Mapped[str] = mapped_column(String(100), nullable=False)
    data_documento: Mapped[date | None] = mapped_column(Date, nullable=True)

    valor_recebido_periodo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    valor_recebido_extenso: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_recebimento: Mapped[date | None] = mapped_column(Date, nullable=True)

    ajuste_status: Mapped[str] = mapped_column(String(20), nullable=False, default="NAO_SOLICITADO")
    ajuste_justificativa: Mapped[str | None] = mapped_column(Text, nullable=True)

    metas: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    atividades_comparativo: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    checklist_documentos: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    periodo_inscricao_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    periodo_inscricao_fim: Mapped[date | None] = mapped_column(Date, nullable=True)
    inscricao_todos_nucleos: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    qtd_inscritos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observacoes_inscricao: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 7 - Identificação do núcleo: nome/endereço/responsável/e-mail/telefone
    # vêm do próprio polo — aqui só a narrativa do período.
    quantitativo_beneficiados: Mapped[str | None] = mapped_column(String(50), nullable=True)
    modalidades: Mapped[str | None] = mapped_column(String(255), nullable=True)
    periodo_funcionamento: Mapped[str | None] = mapped_column(String(50), nullable=True)  # ex.: "MANHA,TARDE"
    descricao_atividades: Mapped[str | None] = mapped_column(Text, nullable=True)
    dificuldades: Mapped[str | None] = mapped_column(Text, nullable=True)

    impactos_sociais: Mapped[str | None] = mapped_column(Text, nullable=True)
    consideracoes_finais: Mapped[str | None] = mapped_column(Text, nullable=True)

    criado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class EntregaMaterialModel(Base):
    """Termo de Entrega de Materiais — um registro por entrega física de
    materiais/uniformes ao núcleo. MASTER/GESTOR_POLO do próprio polo
    cadastram e exportam o termo assinável em .docx."""

    __tablename__ = "entregas_materiais"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    polo_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("polos.id"), nullable=False)
    data_entrega: Mapped[date | None] = mapped_column(Date, nullable=True)
    coordenador_nome: Mapped[str | None] = mapped_column(String(150), nullable=True)
    entregue_por: Mapped[str | None] = mapped_column(String(150), nullable=True)
    itens: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    criado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
