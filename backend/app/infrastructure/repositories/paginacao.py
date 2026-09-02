"""Helper de paginação reaproveitado pelos repositórios das telas de
listagem principais (Beneficiários, Turmas, Professores, Polos, Entregas de
Materiais, Fichas de Execução) — faz a contagem total e a página pedida em
duas consultas no banco (LIMIT/OFFSET), em vez de carregar tudo pra memória
e cortar em Python."""
from typing import TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

ModeloORM = TypeVar("ModeloORM")


def paginar(db: Session, stmt: Select, pagina: int, tamanho_pagina: int) -> tuple[list[ModeloORM], int]:
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    pagina_stmt = stmt.limit(tamanho_pagina).offset((pagina - 1) * tamanho_pagina)
    itens = list(db.scalars(pagina_stmt))
    return itens, total
