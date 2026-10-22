"""Importação em massa de BENEFICIÁRIOS a partir de planilha (.xlsx).
Reaproveita `BeneficiarioService.validar`/`criar` — as mesmas regras do
cadastro individual (documento único, responsável legal se menor) valem
aqui, linha a linha."""
import re
import unicodedata
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.beneficiario.interesse_service import BeneficiarioInteresseService
from app.application.beneficiario.service import BeneficiarioService
from app.application.importacao.campos import (
    booleano,
    data,
    data_obrigatoria,
    resolver_por_nome,
    texto,
    texto_obrigatorio,
)
from app.application.importacao.executor import executar_importacao
from app.application.importacao.planilha import ColunaModelo, gerar_modelo
from app.application.importacao.resultado import ResultadoImportacao
from app.domain.shared.exceptions import RegraDeNegocioViolada
from app.infrastructure.repositories.modalidade_repository import ModalidadeRepository
from app.infrastructure.repositories.polo_repository import PoloRepository

COL_NOME = "Nome completo*"
COL_NASCIMENTO = "Data de nascimento (DD/MM/AAAA)*"
COL_DOCUMENTO = "Documento (CPF)*"
COL_POLO = "Polo*"
COL_RESP_NOME = "Nome do responsável legal"
COL_RESP_NASCIMENTO = "Data de nascimento do responsável (DD/MM/AAAA)"
COL_RESP_PARENTESCO = "Parentesco do responsável"
COL_RESP_TEL1 = "Telefone do responsável 1"
COL_RESP_TEL2 = "Telefone do responsável 2"
COL_RESP_EMAIL = "E-mail do responsável"
COL_RESP_REDE_SOCIAL = "Rede social do responsável"
COL_ENDERECO = "Endereço"
COL_WHATSAPP = "Autoriza uso de imagem/WhatsApp? (Sim/Não)"
COL_OBSERVACOES = "Observações médicas"
COL_INTERESSES = "Modalidades de interesse"


def _colunas(incluir_polo: bool) -> list[ColunaModelo]:
    colunas = [
        ColunaModelo(COL_NOME, True, "Maria da Silva"),
        ColunaModelo(COL_NASCIMENTO, True, "15/03/2015", "Formato DD/MM/AAAA."),
        ColunaModelo(
            COL_DOCUMENTO, True, "123.456.789-00", "CPF ou outro documento de identificação — precisa ser único."
        ),
    ]
    if incluir_polo:
        colunas.append(ColunaModelo(COL_POLO, True, "Polo Zona Norte", "Nome exato de um polo já cadastrado."))
    colunas += [
        ColunaModelo(COL_RESP_NOME, False, "João da Silva", "Obrigatório se o beneficiário for menor de idade."),
        ColunaModelo(COL_RESP_NASCIMENTO, False, "10/01/1985", "Formato DD/MM/AAAA."),
        ColunaModelo(COL_RESP_PARENTESCO, False, "Pai", "Ex.: Pai, Mãe, Avó, Responsável legal."),
        ColunaModelo(COL_RESP_TEL1, False, "(11) 91234-5678"),
        ColunaModelo(COL_RESP_TEL2, False, ""),
        ColunaModelo(COL_RESP_EMAIL, False, "joao@email.com"),
        ColunaModelo(COL_RESP_REDE_SOCIAL, False, ""),
        ColunaModelo(COL_ENDERECO, False, "Rua das Flores, 123"),
        ColunaModelo(COL_WHATSAPP, False, "Sim", "Sim ou Não. Em branco conta como Não."),
        ColunaModelo(COL_OBSERVACOES, False, "Alergia a amendoim"),
        ColunaModelo(
            COL_INTERESSES, False, "Futebol, Vôlei",
            "Modalidades em que o beneficiário quer participar, separadas por vírgula (nomes já cadastrados). "
            "Se o documento já estiver cadastrado, a linha só acrescenta essas modalidades ao beneficiário existente.",
        ),
    ]
    return colunas


class BeneficiarioImportacaoService:
    def __init__(self, db: Session):
        self.db = db
        self.service = BeneficiarioService(db)
        self.polo_repo = PoloRepository(db)
        self.modalidade_repo = ModalidadeRepository(db)
        self.interesse_service = BeneficiarioInteresseService(db)

    def gerar_modelo(self, polo_fixo_id: UUID | None):
        """`polo_fixo_id` vem preenchido quando quem importa é GESTOR_POLO — a
        coluna "Polo" some do modelo porque só existe uma opção possível."""
        return gerar_modelo("Modelo de Importação — Beneficiários", _colunas(incluir_polo=polo_fixo_id is None))

    def importar(self, linhas: list[dict], confirmar: bool, polo_fixo_id: UUID | None) -> ResultadoImportacao:
        opcoes_polo = [(p.id, p.nome) for p in self.polo_repo.listar()] if polo_fixo_id is None else []

        opcoes_modalidade = [(m.id, m.nome) for m in self.modalidade_repo.listar()]

        def processar(linha: dict) -> str | tuple[str, str | None]:
            nome = texto_obrigatorio(linha, COL_NOME)
            polo_id = polo_fixo_id or resolver_por_nome(COL_POLO, texto(linha, COL_POLO), opcoes_polo)
            modalidade_ids = _resolver_modalidades(texto(linha, COL_INTERESSES), opcoes_modalidade)
            documento = texto_obrigatorio(linha, COL_DOCUMENTO)

            # Beneficiário já cadastrado + modalidades informadas: só acrescenta
            # os interesses (permite reimportar a planilha pra completar esse dado).
            # Removido (inativo) não conta: segue pro `criar`, que reativa o cadastro.
            existente = self._buscar_por_documento(documento) if modalidade_ids else None
            if existente and existente.ativo:
                assert existente.id is not None
                if polo_fixo_id and existente.polo_id != polo_fixo_id:
                    raise RegraDeNegocioViolada("Documento já cadastrado em outro polo.")
                if confirmar:
                    self.interesse_service.adicionar(existente.id, modalidade_ids)
                return nome, "Já cadastrado — só as modalidades de interesse foram acrescentadas."

            dados = dict(
                nome_completo=nome,
                data_nascimento=data_obrigatoria(linha, COL_NASCIMENTO),
                documento=documento,
                polo_id=polo_id,
                responsavel_legal_nome=texto(linha, COL_RESP_NOME),
                responsavel_legal_data_nascimento=data(linha, COL_RESP_NASCIMENTO),
                responsavel_legal_tipo_relacao=texto(linha, COL_RESP_PARENTESCO),
                responsavel_legal_telefone_1=texto(linha, COL_RESP_TEL1),
                responsavel_legal_telefone_2=texto(linha, COL_RESP_TEL2),
                responsavel_legal_email=texto(linha, COL_RESP_EMAIL),
                responsavel_legal_rede_social=texto(linha, COL_RESP_REDE_SOCIAL),
                endereco=texto(linha, COL_ENDERECO),
                autoriza_whatsapp=booleano(linha, COL_WHATSAPP),
                observacoes_medicas=texto(linha, COL_OBSERVACOES),
            )
            if confirmar:
                criado = self.service.criar(**dados)
                assert criado.id is not None
                if modalidade_ids:
                    self.interesse_service.adicionar(criado.id, modalidade_ids)
            else:
                self.service.validar(**dados)
            return nome

        return executar_importacao(self.db, linhas, processar, confirmar)

    def _buscar_por_documento(self, documento: str):
        """Documentos são gravados como digitados (com ou sem pontuação) — tenta
        as duas formas pra achar o mesmo CPF."""
        digitos = re.sub(r"\D", "", documento)
        candidatos = [documento, digitos]
        if len(digitos) == 11:
            candidatos.append(f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}")
        for candidato in dict.fromkeys(candidatos):
            encontrado = self.service.repo.buscar_por_documento(candidato)
            if encontrado:
                return encontrado
        return None


def _normalizar(nome: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", sem_acento.lower())


def _resolver_modalidades(valor: str | None, opcoes: list[tuple[UUID, str]]) -> list[UUID]:
    """"Futebol, Vôlei" → [id_futebol, id_volei]. Ignora acento, caixa, espaço
    e hífen ("Volei" casa com "Vôlei", "jiu jitsu" com "Jiu-Jitsu")."""
    if not valor:
        return []
    por_nome = {_normalizar(nome): id_opcao for id_opcao, nome in opcoes}
    ids: list[UUID] = []
    for parte in re.split(r"[,;/]", valor):
        if not parte.strip():
            continue
        id_opcao = por_nome.get(_normalizar(parte))
        if id_opcao is None:
            disponiveis = ", ".join(sorted(nome for _, nome in opcoes)) or "nenhuma cadastrada"
            raise RegraDeNegocioViolada(
                f'Coluna "{COL_INTERESSES}": "{parte.strip()}" não encontrada. Modalidades disponíveis: {disponiveis}.'
            )
        ids.append(id_opcao)
    return list(dict.fromkeys(ids))
