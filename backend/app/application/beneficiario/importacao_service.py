"""Importação em massa de BENEFICIÁRIOS a partir de planilha (.xlsx).
Reaproveita `BeneficiarioService.validar`/`criar` — as mesmas regras do
cadastro individual (documento único, responsável legal se menor) valem
aqui, linha a linha."""
from uuid import UUID

from sqlalchemy.orm import Session

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
    ]
    return colunas


class BeneficiarioImportacaoService:
    def __init__(self, db: Session):
        self.db = db
        self.service = BeneficiarioService(db)
        self.polo_repo = PoloRepository(db)

    def gerar_modelo(self, polo_fixo_id: UUID | None):
        """`polo_fixo_id` vem preenchido quando quem importa é GESTOR_POLO — a
        coluna "Polo" some do modelo porque só existe uma opção possível."""
        return gerar_modelo("Modelo de Importação — Beneficiários", _colunas(incluir_polo=polo_fixo_id is None))

    def importar(self, linhas: list[dict], confirmar: bool, polo_fixo_id: UUID | None) -> ResultadoImportacao:
        opcoes_polo = [(p.id, p.nome) for p in self.polo_repo.listar()] if polo_fixo_id is None else []

        def processar(linha: dict) -> str:
            nome = texto_obrigatorio(linha, COL_NOME)
            polo_id = polo_fixo_id or resolver_por_nome(COL_POLO, texto(linha, COL_POLO), opcoes_polo)
            dados = dict(
                nome_completo=nome,
                data_nascimento=data_obrigatoria(linha, COL_NASCIMENTO),
                documento=texto_obrigatorio(linha, COL_DOCUMENTO),
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
                self.service.criar(**dados)
            else:
                self.service.validar(**dados)
            return nome

        return executar_importacao(self.db, linhas, processar, confirmar)
