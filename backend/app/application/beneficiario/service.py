"""
Use cases de BENEFICIÁRIO (nomenclatura oficial e obrigatória).
Aplica regras de negócio: documento único e responsável legal se menor.
A matrícula em turmas/modalidades é tratada à parte — ver
app/application/matricula/service.py — porque um beneficiário pode estar
em várias ao mesmo tempo (ex.: judô e natação).
"""
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.beneficiario.entities import Beneficiario
from app.domain.shared.exceptions import RecursoJaExiste
from app.infrastructure.repositories.beneficiario_repository import BeneficiarioRepository


class BeneficiarioService:
    def __init__(self, db: Session):
        self.repo = BeneficiarioRepository(db)

    def listar(self, polo_id: UUID | None = None, turma_id: UUID | None = None) -> list[Beneficiario]:
        return self.repo.listar(polo_id=polo_id, turma_id=turma_id)

    def listar_pagina(
        self, pagina: int, tamanho_pagina: int, polo_id: UUID | None = None, nome: str | None = None,
    ) -> tuple[list[Beneficiario], int]:
        return self.repo.listar_pagina(pagina=pagina, tamanho_pagina=tamanho_pagina, polo_id=polo_id, nome=nome)

    def buscar(self, beneficiario_id: UUID) -> Beneficiario | None:
        return self.repo.buscar_por_id(beneficiario_id)

    def criar(
        self, nome_completo: str, data_nascimento: date, documento: str,
        polo_id: UUID | None,
        responsavel_legal_nome: str | None, responsavel_legal_data_nascimento: date | None,
        responsavel_legal_tipo_relacao: str | None, responsavel_legal_telefone_1: str | None,
        responsavel_legal_telefone_2: str | None, responsavel_legal_email: str | None,
        responsavel_legal_rede_social: str | None, endereco: str | None,
        autoriza_whatsapp: bool, observacoes_medicas: str | None,
    ) -> Beneficiario:
        # O documento é sempre exclusivo do próprio beneficiário — mesmo quando
        # dois irmãos compartilham o mesmo responsável legal, cada um tem seu
        # próprio documento aqui (o do responsável não é validado por unicidade).
        if self.repo.buscar_por_documento(documento):
            raise RecursoJaExiste("Já existe um beneficiário com este documento.")

        beneficiario = Beneficiario(
            id=None, nome_completo=nome_completo, data_nascimento=data_nascimento,
            documento=documento, polo_id=polo_id,
            responsavel_legal_nome=responsavel_legal_nome,
            responsavel_legal_data_nascimento=responsavel_legal_data_nascimento,
            responsavel_legal_tipo_relacao=responsavel_legal_tipo_relacao,
            responsavel_legal_telefone_1=responsavel_legal_telefone_1,
            responsavel_legal_telefone_2=responsavel_legal_telefone_2,
            responsavel_legal_email=responsavel_legal_email,
            responsavel_legal_rede_social=responsavel_legal_rede_social,
            endereco=endereco, autoriza_whatsapp=autoriza_whatsapp,
            observacoes_medicas=observacoes_medicas,
        )
        beneficiario.validar_responsavel_legal_se_menor()

        return self.repo.criar(beneficiario)

    def atualizar(self, beneficiario_id: UUID, **campos) -> Beneficiario | None:
        return self.repo.atualizar(beneficiario_id, **campos)
