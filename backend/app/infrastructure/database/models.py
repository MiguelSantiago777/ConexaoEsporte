"""
Modelos ORM (SQLAlchemy) — mapeiam 1:1 as tabelas de database/schema.sql.
Camada de Infraestrutura (DDD): estes modelos NÃO vazam para as regras de
negócio; a camada de Application/Domain trabalha com as entidades puras
definidas em app/domain/**/entities.py.
"""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
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
    registrado_por_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
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
