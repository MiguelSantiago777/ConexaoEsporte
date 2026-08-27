"""Repositório de Polo."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.polo.entities import Polo
from app.infrastructure.database.models import PoloModel


def _to_entity(m: PoloModel) -> Polo:
    return Polo(
        id=m.id, nome=m.nome, codigo=m.codigo, endereco=m.endereco,
        horario_funcionamento=m.horario_funcionamento, status=m.status,
        gestor_responsavel_id=m.gestor_responsavel_id,
        processo_sei=m.processo_sei, termo_fomento_numero=m.termo_fomento_numero,
        nome_entidade=m.nome_entidade, cnpj=m.cnpj,
        representante_legal_nome=m.representante_legal_nome, representante_legal_cpf=m.representante_legal_cpf,
        objeto=m.objeto, vigencia_inicio=m.vigencia_inicio, vigencia_fim=m.vigencia_fim,
        valor_pactuado=m.valor_pactuado, valor_executado=m.valor_executado,
        parlamentar=m.parlamentar, emenda=m.emenda, termos_aditivos=m.termos_aditivos or [],
        responsavel_nome=m.responsavel_nome, responsavel_email=m.responsavel_email,
        responsavel_telefone=m.responsavel_telefone,
        representante_legal_rg=m.representante_legal_rg,
        representante_legal_endereco=m.representante_legal_endereco,
        representante_legal_bairro=m.representante_legal_bairro,
        representante_legal_cidade=m.representante_legal_cidade,
    )


class PoloRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self) -> list[Polo]:
        return [_to_entity(m) for m in self.db.scalars(select(PoloModel))]

    def buscar_por_id(self, polo_id: UUID) -> Polo | None:
        m = self.db.get(PoloModel, polo_id)
        return _to_entity(m) if m else None

    def buscar_por_codigo(self, codigo: str) -> Polo | None:
        m = self.db.scalar(select(PoloModel).where(PoloModel.codigo == codigo))
        return _to_entity(m) if m else None

    def criar(self, polo: Polo) -> Polo:
        m = PoloModel(
            nome=polo.nome, codigo=polo.codigo, endereco=polo.endereco,
            horario_funcionamento=polo.horario_funcionamento, status=polo.status,
            gestor_responsavel_id=polo.gestor_responsavel_id,
            processo_sei=polo.processo_sei, termo_fomento_numero=polo.termo_fomento_numero,
            nome_entidade=polo.nome_entidade, cnpj=polo.cnpj,
            representante_legal_nome=polo.representante_legal_nome,
            representante_legal_cpf=polo.representante_legal_cpf,
            objeto=polo.objeto, vigencia_inicio=polo.vigencia_inicio, vigencia_fim=polo.vigencia_fim,
            valor_pactuado=polo.valor_pactuado, valor_executado=polo.valor_executado,
            parlamentar=polo.parlamentar, emenda=polo.emenda, termos_aditivos=polo.termos_aditivos,
            responsavel_nome=polo.responsavel_nome, responsavel_email=polo.responsavel_email,
            responsavel_telefone=polo.responsavel_telefone,
            representante_legal_rg=polo.representante_legal_rg,
            representante_legal_endereco=polo.representante_legal_endereco,
            representante_legal_bairro=polo.representante_legal_bairro,
            representante_legal_cidade=polo.representante_legal_cidade,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)

    def atualizar(self, polo_id: UUID, **campos) -> Polo | None:
        m = self.db.get(PoloModel, polo_id)
        if not m:
            return None
        for k, v in campos.items():
            if v is not None:
                setattr(m, k, v)
        self.db.commit()
        self.db.refresh(m)
        return _to_entity(m)
