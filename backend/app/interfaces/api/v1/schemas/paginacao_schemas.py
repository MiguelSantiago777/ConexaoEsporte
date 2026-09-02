"""Envelope genérico de paginação, reaproveitado pelas listagens principais.
Cada rota de listagem devolve a lista completa de sempre quando `pagina` não
é informado (mantendo compatibilidade com quem só quer todas as opções pra
um <select>, por exemplo), e passa a devolver este envelope — com o total
de itens pra montar os controles de "página X de Y" — quando `pagina` é
informado."""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginaResponse(BaseModel, Generic[T]):
    itens: list[T]
    total: int
    pagina: int
    tamanho_pagina: int
