"""Importação em massa de POLOS a partir de planilha (.xlsx). Só MASTER
importa polos (mesmo RBAC do cadastro individual).

Escopo: cobre os campos essenciais pra colocar vários polos no sistema
rapidamente (identificação, parceria/convênio básica, contato e
localização). Campos mais específicos de documentação (objeto do convênio,
dados de RG/endereço do representante legal para o Termo de
Responsabilidade, termos aditivos) ficam de fora da planilha — como o
cadastro individual já permite salvar só o básico e completar depois via
edição, o mesmo vale aqui: complete esses campos depois em Polos > Editar."""
from sqlalchemy.orm import Session

from app.application.importacao.campos import data, decimal, texto, texto_obrigatorio
from app.application.importacao.executor import executar_importacao
from app.application.importacao.geocodificacao import geocodificar
from app.application.importacao.planilha import ColunaModelo, gerar_modelo
from app.application.importacao.resultado import ResultadoImportacao
from app.application.polo.service import PoloService
from app.domain.shared.exceptions import RegraDeNegocioViolada
from app.infrastructure.repositories.usuario_repository import UsuarioRepository

COL_NOME = "Nome*"
COL_CODIGO = "Código"
COL_ENDERECO = "Endereço"
COL_HORARIO = "Horário de funcionamento"
COL_GESTOR_EMAIL = "E-mail do gestor responsável"
COL_PROCESSO_SEI = "Processo SEI"
COL_TERMO_FOMENTO = "Número do Termo de Fomento"
COL_NOME_ENTIDADE = "Nome da entidade"
COL_CNPJ = "CNPJ"
COL_REP_LEGAL_NOME = "Nome do representante legal"
COL_REP_LEGAL_CPF = "CPF do representante legal"
COL_VIGENCIA_INICIO = "Início da vigência (DD/MM/AAAA)"
COL_VIGENCIA_FIM = "Fim da vigência (DD/MM/AAAA)"
COL_VALOR_PACTUADO = "Valor pactuado"
COL_VALOR_EXECUTADO = "Valor executado"
COL_RESP_NOME = "Nome do responsável do núcleo"
COL_RESP_EMAIL = "E-mail do responsável do núcleo"
COL_RESP_TELEFONE = "Telefone do responsável do núcleo"
COL_LATITUDE = "Latitude"
COL_LONGITUDE = "Longitude"

_COLUNAS = [
    ColunaModelo(COL_NOME, True, "Polo Zona Norte"),
    ColunaModelo(COL_CODIGO, False, "PZN-01", "Precisa ser único, se preenchido."),
    ColunaModelo(COL_ENDERECO, False, "Rua das Flores, 123"),
    ColunaModelo(COL_HORARIO, False, "Seg a Sex, 8h-18h"),
    ColunaModelo(COL_GESTOR_EMAIL, False, "gestor@email.com", "E-mail de um usuário já cadastrado."),
    ColunaModelo(COL_PROCESSO_SEI, False, ""),
    ColunaModelo(COL_TERMO_FOMENTO, False, ""),
    ColunaModelo(COL_NOME_ENTIDADE, False, ""),
    ColunaModelo(COL_CNPJ, False, ""),
    ColunaModelo(COL_REP_LEGAL_NOME, False, ""),
    ColunaModelo(COL_REP_LEGAL_CPF, False, ""),
    ColunaModelo(COL_VIGENCIA_INICIO, False, "01/01/2026", "Formato DD/MM/AAAA."),
    ColunaModelo(COL_VIGENCIA_FIM, False, "31/12/2026", "Formato DD/MM/AAAA."),
    ColunaModelo(COL_VALOR_PACTUADO, False, "R$ 200.000,00"),
    ColunaModelo(COL_VALOR_EXECUTADO, False, ""),
    ColunaModelo(COL_RESP_NOME, False, ""),
    ColunaModelo(COL_RESP_EMAIL, False, ""),
    ColunaModelo(COL_RESP_TELEFONE, False, ""),
    ColunaModelo(
        COL_LATITUDE, False, "",
        "Opcional — se ficar em branco e o Endereço estiver preenchido, o sistema busca a coordenada automaticamente.",
    ),
    ColunaModelo(
        COL_LONGITUDE, False, "",
        "Opcional — preenchida junto com a Latitude quando buscada automaticamente pelo Endereço.",
    ),
]


class PoloImportacaoService:
    def __init__(self, db: Session):
        self.db = db
        self.service = PoloService(db)
        self.usuario_repo = UsuarioRepository(db)

    def gerar_modelo(self):
        return gerar_modelo("Modelo de Importação — Polos", _COLUNAS)

    def importar(self, linhas: list[dict], confirmar: bool) -> ResultadoImportacao:
        def resolver_gestor(email: str | None):
            if not email or not email.strip():
                return None
            gestor = self.usuario_repo.buscar_por_email(email.strip())
            if not gestor:
                raise RegraDeNegocioViolada(
                    f'Coluna "{COL_GESTOR_EMAIL}": "{email}" não encontrado entre os usuários cadastrados.'
                )
            return gestor.id

        def resolver_coordenadas(linha: dict, endereco: str | None) -> tuple[float | None, float | None]:
            latitude = decimal(linha, COL_LATITUDE)
            longitude = decimal(linha, COL_LONGITUDE)
            if endereco and (latitude is None or longitude is None):
                geocodificado = geocodificar(endereco)
                if geocodificado:
                    latitude, longitude = geocodificado
            return latitude, longitude

        def processar(linha: dict) -> str:
            nome = texto_obrigatorio(linha, COL_NOME)
            endereco = texto(linha, COL_ENDERECO)
            latitude, longitude = resolver_coordenadas(linha, endereco)
            dados = dict(
                nome=nome,
                codigo=texto(linha, COL_CODIGO),
                endereco=endereco,
                horario_funcionamento=texto(linha, COL_HORARIO),
                gestor_responsavel_id=resolver_gestor(texto(linha, COL_GESTOR_EMAIL)),
                processo_sei=texto(linha, COL_PROCESSO_SEI),
                termo_fomento_numero=texto(linha, COL_TERMO_FOMENTO),
                nome_entidade=texto(linha, COL_NOME_ENTIDADE),
                cnpj=texto(linha, COL_CNPJ),
                representante_legal_nome=texto(linha, COL_REP_LEGAL_NOME),
                representante_legal_cpf=texto(linha, COL_REP_LEGAL_CPF),
                vigencia_inicio=data(linha, COL_VIGENCIA_INICIO),
                vigencia_fim=data(linha, COL_VIGENCIA_FIM),
                valor_pactuado=texto(linha, COL_VALOR_PACTUADO),
                valor_executado=texto(linha, COL_VALOR_EXECUTADO),
                responsavel_nome=texto(linha, COL_RESP_NOME),
                responsavel_email=texto(linha, COL_RESP_EMAIL),
                responsavel_telefone=texto(linha, COL_RESP_TELEFONE),
                latitude=latitude,
                longitude=longitude,
            )
            if confirmar:
                self.service.criar(**dados)
            else:
                self.service.validar(**dados)
            return nome

        return executar_importacao(self.db, linhas, processar, confirmar)
