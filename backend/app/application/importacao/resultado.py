"""Estruturas do relatório de importação em massa — comuns a todas as
entidades importáveis (beneficiário, turma, usuário, produto, polo)."""
from dataclasses import dataclass, field


@dataclass
class LinhaResultado:
    linha: int  # número da linha na planilha (linha 1 é o cabeçalho, dados começam na 2)
    status: str  # "ok" ou "erro"
    resumo: str  # identificação legível do registro (ex.: nome do beneficiário)
    erro: str | None = None


@dataclass
class ResultadoImportacao:
    confirmado: bool  # False = só prévia (nada foi gravado), True = gravação realizada
    linhas: list[LinhaResultado] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.linhas)

    @property
    def sucesso(self) -> int:
        return sum(1 for l in self.linhas if l.status == "ok")

    @property
    def falha(self) -> int:
        return sum(1 for l in self.linhas if l.status == "erro")

    def adicionar_sucesso(self, linha: int, resumo: str) -> None:
        self.linhas.append(LinhaResultado(linha=linha, status="ok", resumo=resumo))

    def adicionar_erro(self, linha: int, resumo: str, erro: str) -> None:
        self.linhas.append(LinhaResultado(linha=linha, status="erro", resumo=resumo, erro=erro))
