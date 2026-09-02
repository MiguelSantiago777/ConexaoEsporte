"""Orquestra a montagem dos dados de Polo/Turma/Frequência para os
exportadores de relatórios (os exportadores em si só sabem formatar o
arquivo; quem busca e agrega os dados do banco é este serviço)."""
from calendar import monthrange
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.relatorios.grade_horaria_export_service import TurmaGrade, exportar_grade_horaria
from app.application.relatorios.lista_presenca_export_service import exportar_lista_presenca
from app.application.relatorios.planilha_nucleos_export_service import (
    BeneficiarioNucleoItem,
    RHItem,
    exportar_planilha_nucleos,
)
from app.application.relatorios.cabecalho_convenio import texto_cabecalho
from app.application.relatorios.termo_entrega_export_service import ItemEntrega, exportar_termo_entrega
from app.application.relatorios.termo_responsabilidade_export_service import exportar_termo_responsabilidade
from app.domain.enums import PerfilUsuario
from app.domain.shared.exceptions import RecursoNaoEncontrado
from app.infrastructure.repositories.beneficiario_repository import BeneficiarioRepository
from app.infrastructure.repositories.configuracao_geral_repository import ConfiguracaoGeralRepository
from app.infrastructure.repositories.entrega_material_repository import EntregaMaterialRepository
from app.infrastructure.repositories.frequencia_repository import FrequenciaRepository
from app.infrastructure.repositories.matricula_repository import MatriculaRepository
from app.infrastructure.repositories.modalidade_repository import ModalidadeRepository
from app.infrastructure.repositories.polo_repository import PoloRepository
from app.infrastructure.repositories.turma_repository import TurmaRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository


def _calcular_idade(data_nascimento: date) -> int:
    hoje = date.today()
    idade = hoje.year - data_nascimento.year
    if (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day):
        idade -= 1
    return idade


class RelatorioService:
    def __init__(self, db: Session):
        self.turma_repo = TurmaRepository(db)
        self.polo_repo = PoloRepository(db)
        self.modalidade_repo = ModalidadeRepository(db)
        self.usuario_repo = UsuarioRepository(db)
        self.matricula_repo = MatriculaRepository(db)
        self.frequencia_repo = FrequenciaRepository(db)
        self.beneficiario_repo = BeneficiarioRepository(db)
        self.entrega_material_repo = EntregaMaterialRepository(db)
        self._cabecalho_convenio = texto_cabecalho(ConfiguracaoGeralRepository(db).buscar())

    def gerar_lista_presenca(self, turma_id: UUID, mes: int, ano: int):
        turma = self.turma_repo.buscar_por_id(turma_id)
        if not turma:
            raise RecursoNaoEncontrado("Turma não encontrada.")
        polo = self.polo_repo.buscar_por_id(turma.polo_id)
        modalidade = self.modalidade_repo.buscar_por_id(turma.modalidade_id)
        professor = self.usuario_repo.buscar_por_id(turma.professor_id) if turma.professor_id else None

        beneficiarios = [(str(bid), nome) for bid, nome in self.matricula_repo.listar_beneficiarios_ativos_por_turma(turma_id)]

        ultimo_dia = monthrange(ano, mes)[1]
        registros = self.frequencia_repo.listar_por_turma_e_periodo(
            turma_id, date(ano, mes, 1), date(ano, mes, ultimo_dia)
        )
        presencas = {(str(r.beneficiario_id), r.data.day): r.presente for r in registros}

        entidade_titulo = None
        if polo and polo.nome_entidade:
            entidade_titulo = f"LISTA DE PRESENÇA - {polo.nome_entidade}"
            if polo.termo_fomento_numero:
                entidade_titulo += f" - Termo de Fomento nº {polo.termo_fomento_numero}"

        return exportar_lista_presenca(
            nucleo_nome=polo.nome if polo else "",
            entidade_titulo=entidade_titulo,
            turma_descricao=f"{modalidade.nome} — {turma.horario_inicio}–{turma.horario_fim}" if modalidade else "",
            coordenador_nome=turma.coordenador_nome or "",
            periodicidade=turma.periodicidade or "",
            professor_nome=professor.nome if professor else "",
            modalidade_nome=modalidade.nome if modalidade else "",
            monitor_nome=turma.monitor_nome or "",
            horario=f"{turma.horario_inicio}–{turma.horario_fim}",
            mes=mes, ano=ano,
            beneficiarios=beneficiarios,
            presencas=presencas,
            cabecalho_convenio=self._cabecalho_convenio,
        )

    def gerar_grade_horaria(self, polo_id: UUID, planejamento_horas: float):
        polo = self.polo_repo.buscar_por_id(polo_id)
        if not polo:
            raise RecursoNaoEncontrado("Polo não encontrado.")

        turmas_polo = self.turma_repo.listar(polo_id=polo_id)
        turmas_polo.sort(key=lambda t: t.horario_inicio)
        modalidades = {m.id: m.nome for m in self.modalidade_repo.listar()}

        turmas = [
            TurmaGrade(
                modalidade_nome=modalidades.get(t.modalidade_id, ""),
                horario_inicio=t.horario_inicio, horario_fim=t.horario_fim,
                dias_semana=t.dias_semana,
            )
            for t in turmas_polo
        ]

        return exportar_grade_horaria(
            polo_nome=polo.nome, turmas=turmas, planejamento_horas=planejamento_horas,
            cabecalho_convenio=self._cabecalho_convenio,
        )

    def gerar_planilha_nucleos(self, polo_id: UUID):
        polo = self.polo_repo.buscar_por_id(polo_id)
        if not polo:
            raise RecursoNaoEncontrado("Polo não encontrado.")

        rh_usuarios = [
            u for u in self.usuario_repo.listar(polo_id=polo_id)
            if u.perfil in (PerfilUsuario.GESTOR_POLO, PerfilUsuario.PROFESSOR) and u.ativo
        ]
        rh = [
            RHItem(
                nome=u.nome, carga_horaria=u.carga_horaria_semanal or "", telefone=u.telefone or "", email=u.email,
            )
            for u in rh_usuarios
        ]

        modalidades = {m.id: m.nome for m in self.modalidade_repo.listar()}
        beneficiarios_polo = [b for b in self.beneficiario_repo.listar(polo_id=polo_id) if b.ativo]
        beneficiarios = []
        for b in beneficiarios_polo:
            matriculas = [m for m in self.matricula_repo.listar_por_beneficiario(b.id) if m.ativo]
            nomes_modalidade = []
            for m in matriculas:
                turma = self.turma_repo.buscar_por_id(m.turma_id)
                if turma and turma.modalidade_id in modalidades:
                    nomes_modalidade.append(modalidades[turma.modalidade_id])
            beneficiarios.append(
                BeneficiarioNucleoItem(
                    nome=b.nome_completo, idade=_calcular_idade(b.data_nascimento),
                    modalidades=", ".join(dict.fromkeys(nomes_modalidade)),
                )
            )

        return exportar_planilha_nucleos(
            nome_entidade=polo.nome_entidade or "",
            termo_fomento_numero=polo.termo_fomento_numero or "",
            polo_nome=polo.nome,
            polo_horario_funcionamento=polo.horario_funcionamento or "",
            polo_endereco=polo.endereco or "",
            rh=rh,
            beneficiarios=beneficiarios,
            cabecalho_convenio=self._cabecalho_convenio,
        )

    def gerar_termo_entrega(self, entrega_id: UUID):
        entrega = self.entrega_material_repo.buscar_por_id(entrega_id)
        if not entrega:
            raise RecursoNaoEncontrado("Entrega de materiais não encontrada.")
        polo = self.polo_repo.buscar_por_id(entrega.polo_id)

        itens = [ItemEntrega(descricao=i.get("descricao", ""), quantidade=i.get("quantidade", "")) for i in entrega.itens]
        return exportar_termo_entrega(
            polo_nome=polo.nome if polo else "",
            coordenador_nome=entrega.coordenador_nome or "",
            itens=itens,
            cabecalho_convenio=self._cabecalho_convenio,
        )

    def gerar_termo_responsabilidade(self, polo_id: UUID):
        polo = self.polo_repo.buscar_por_id(polo_id)
        if not polo:
            raise RecursoNaoEncontrado("Polo não encontrado.")

        return exportar_termo_responsabilidade(
            representante_nome=polo.representante_legal_nome or "",
            representante_rg=polo.representante_legal_rg or "",
            representante_cpf=polo.representante_legal_cpf or "",
            endereco=polo.representante_legal_endereco or "",
            bairro=polo.representante_legal_bairro or "",
            cidade=polo.representante_legal_cidade or "",
            cabecalho_convenio=self._cabecalho_convenio,
        )
