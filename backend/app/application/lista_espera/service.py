"""
Use cases da LISTA DE ESPERA: inscrição pública (formulário embutido na
landing page do projeto) e o aceite por um GESTOR_POLO/MASTER, que vira
Beneficiário + Matrícula na turma escolhida.
"""
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.beneficiario.service import BeneficiarioService
from app.application.email.service import EmailService
from app.application.matricula.service import MatriculaService
from app.domain.lista_espera.entities import InscricaoListaEspera
from app.domain.matricula.entities import Matricula
from app.domain.shared.exceptions import RecursoNaoEncontrado, RegraDeNegocioViolada
from app.infrastructure.repositories.beneficiario_repository import BeneficiarioRepository
from app.infrastructure.repositories.inscricao_lista_espera_repository import InscricaoListaEsperaRepository
from app.infrastructure.repositories.modalidade_repository import ModalidadeRepository
from app.infrastructure.repositories.polo_repository import PoloRepository
from app.infrastructure.repositories.turma_repository import TurmaRepository

DIAS_SEMANA_LEGIVEL = {
    "SEG": "seg", "TER": "ter", "QUA": "qua", "QUI": "qui", "SEX": "sex", "SAB": "sáb", "DOM": "dom",
}


class ListaEsperaService:
    def __init__(self, db: Session):
        self.repo = InscricaoListaEsperaRepository(db)
        self.beneficiario_repo = BeneficiarioRepository(db)
        self.beneficiario_service = BeneficiarioService(db)
        self.matricula_service = MatriculaService(db)
        self.modalidade_repo = ModalidadeRepository(db)
        self.polo_repo = PoloRepository(db)
        self.turma_repo = TurmaRepository(db)
        self.email_service = EmailService()

    def opcoes_publicas(self) -> tuple[list, list]:
        """Polos ativos e modalidades, pro <select> do formulário público —
        sem nenhum outro dado sensível do polo."""
        polos = [p for p in self.polo_repo.listar() if p.status == "ATIVO"]
        modalidades = self.modalidade_repo.listar()
        return polos, modalidades

    def inscrever(
        self, nome_completo: str, data_nascimento: date, documento: str, nome_responsavel: str | None,
        documento_responsavel: str | None, telefone_whatsapp: str, email: str, bairro: str | None,
        cidade: str | None, modalidade_id: UUID, polo_id: UUID, como_conheceu: str | None,
        tamanho_camisa: str | None = None, tamanho_calcado: str | None = None,
    ) -> InscricaoListaEspera:
        modalidade = self.modalidade_repo.buscar_por_id(modalidade_id)
        if not modalidade:
            raise RecursoNaoEncontrado("Modalidade não encontrada.")
        polo = self.polo_repo.buscar_por_id(polo_id)
        if not polo or polo.status != "ATIVO":
            raise RecursoNaoEncontrado("Polo não encontrado.")

        inscricao = InscricaoListaEspera(
            id=None, nome_completo=nome_completo, data_nascimento=data_nascimento, documento=documento,
            nome_responsavel=nome_responsavel, documento_responsavel=documento_responsavel,
            telefone_whatsapp=telefone_whatsapp, email=email,
            bairro=bairro, cidade=cidade, modalidade_id=modalidade_id, polo_id=polo_id,
            como_conheceu=como_conheceu, tamanho_camisa=tamanho_camisa, tamanho_calcado=tamanho_calcado,
        )
        inscricao.validar_faixa_etaria()
        inscricao.validar_responsavel_se_menor()

        criada = self.repo.criar(inscricao)

        self.email_service.enviar_confirmacao_inscricao_lista_espera(
            destinatario=email,
            nome_responsavel_ou_participante=nome_responsavel or nome_completo,
            nome_participante=nome_completo, modalidade_nome=modalidade.nome, polo_nome=polo.nome,
        )
        return criada

    def listar_pendentes(self, polo_id: UUID | None = None) -> list[InscricaoListaEspera]:
        return self.repo.listar_pendentes(polo_id=polo_id)

    def aceitar(self, inscricao_id: UUID, turma_id: UUID, usuario_id: UUID) -> Matricula:
        inscricao = self.repo.buscar_por_id(inscricao_id)
        if not inscricao:
            raise RecursoNaoEncontrado("Inscrição não encontrada.")
        if not inscricao.pendente:
            raise RegraDeNegocioViolada("Esta inscrição já foi aceita.")

        turma = self.turma_repo.buscar_por_id(turma_id)
        if not turma:
            raise RecursoNaoEncontrado("Turma não encontrada.")
        if turma.polo_id != inscricao.polo_id or turma.modalidade_id != inscricao.modalidade_id:
            raise RegraDeNegocioViolada("A turma escolhida deve ser do mesmo polo e modalidade da inscrição.")

        # CPF já cadastrado (ex.: irmão já matriculado) reaproveita o Beneficiário
        # existente em vez de duplicar o cadastro — só cria um novo quando não existe.
        beneficiario = self.beneficiario_repo.buscar_por_documento(inscricao.documento)
        if not beneficiario:
            beneficiario = self.beneficiario_service.criar(
                nome_completo=inscricao.nome_completo, data_nascimento=inscricao.data_nascimento,
                documento=inscricao.documento, polo_id=inscricao.polo_id,
                responsavel_legal_nome=inscricao.nome_responsavel,
                responsavel_legal_data_nascimento=None, responsavel_legal_tipo_relacao=None,
                responsavel_legal_telefone_1=inscricao.telefone_whatsapp,
                responsavel_legal_telefone_2=None, responsavel_legal_email=inscricao.email,
                responsavel_legal_rede_social=None,
                endereco=", ".join(p for p in [inscricao.bairro, inscricao.cidade] if p),
                autoriza_whatsapp=True, observacoes_medicas=None,
                tamanho_camisa=inscricao.tamanho_camisa, tamanho_calcado=inscricao.tamanho_calcado,
            )

        matricula = self.matricula_service.matricular(beneficiario.id, turma_id)

        assert beneficiario.id is not None
        self.repo.marcar_aceita(
            inscricao_id, beneficiario_id=beneficiario.id, turma_id=turma_id, aceito_por_id=usuario_id,
        )

        modalidade = self.modalidade_repo.buscar_por_id(inscricao.modalidade_id)
        polo = self.polo_repo.buscar_por_id(inscricao.polo_id)
        dias = ", ".join(DIAS_SEMANA_LEGIVEL.get(d, d) for d in turma.dias_semana)
        self.email_service.enviar_aceite_lista_espera(
            destinatario=inscricao.email,
            nome_responsavel_ou_participante=inscricao.nome_responsavel or inscricao.nome_completo,
            nome_participante=inscricao.nome_completo,
            modalidade_nome=modalidade.nome if modalidade else "—", polo_nome=polo.nome if polo else "—",
            dias_semana=dias, horario_inicio=turma.horario_inicio, horario_fim=turma.horario_fim,
        )
        return matricula
