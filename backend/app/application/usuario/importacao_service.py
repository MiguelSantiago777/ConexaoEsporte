"""Importação em massa de USUÁRIOS (professores/funcionários) a partir de
planilha (.xlsx). A senha nunca vem da planilha — é gerada aleatoriamente e
enviada por e-mail só na confirmação (nunca durante a prévia), reaproveitando
a mesma infraestrutura de envio usada na redefinição de senha."""
import secrets
import string
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.email.service import EmailService
from app.application.importacao.campos import resolver_por_nome, texto, texto_obrigatorio
from app.application.importacao.executor import executar_importacao
from app.application.importacao.planilha import ColunaModelo, gerar_modelo
from app.application.importacao.resultado import ResultadoImportacao
from app.application.usuario.service import UsuarioService
from app.core.dependencies import UsuarioAutenticado
from app.domain.enums import PerfilUsuario
from app.domain.shared.exceptions import RegraDeNegocioViolada
from app.infrastructure.repositories.almoxarifado_repository import AlmoxarifadoRepository
from app.infrastructure.repositories.papel_repository import PapelRepository
from app.infrastructure.repositories.polo_repository import PoloRepository

COL_NOME = "Nome*"
COL_EMAIL = "E-mail*"
COL_PERFIL = "Perfil*"
COL_POLO = "Polo"
COL_ALMOXARIFADO = "Almoxarifado"
COL_PAPEL = "Papel (Central de Acessos)"
COL_TELEFONE = "Telefone"
COL_CARGA_HORARIA = "Carga horária semanal"


def _gerar_senha_temporaria() -> str:
    alfabeto = string.ascii_letters + string.digits
    return "".join(secrets.choice(alfabeto) for _ in range(12))


def _colunas(perfis_disponiveis: list[PerfilUsuario], incluir_polo: bool) -> list[ColunaModelo]:
    perfis_texto = ", ".join(p.value for p in perfis_disponiveis)
    colunas = [
        ColunaModelo(COL_NOME, True, "João Pereira"),
        ColunaModelo(COL_EMAIL, True, "joao.pereira@email.com", "Precisa ser único no sistema."),
        ColunaModelo(COL_PERFIL, True, perfis_disponiveis[0].value, f"Use exatamente um destes valores: {perfis_texto}."),
    ]
    if incluir_polo:
        colunas.append(
            ColunaModelo(COL_POLO, False, "Polo Zona Norte", "Obrigatório para perfil GESTOR_POLO ou PROFESSOR.")
        )
    colunas += [
        ColunaModelo(COL_ALMOXARIFADO, False, "", "Obrigatório para perfil COORDENADOR_ALMOXARIFADO."),
        ColunaModelo(COL_PAPEL, False, "", "Obrigatório para perfil PERSONALIZADO (Central de Acessos)."),
        ColunaModelo(COL_TELEFONE, False, "(11) 91234-5678"),
        ColunaModelo(COL_CARGA_HORARIA, False, "20h"),
    ]
    return colunas


class UsuarioImportacaoService:
    def __init__(self, db: Session):
        self.db = db
        self.service = UsuarioService(db)
        self.email_service = EmailService()
        self.polo_repo = PoloRepository(db)
        self.almoxarifado_repo = AlmoxarifadoRepository(db)
        self.papel_repo = PapelRepository(db)

    def gerar_modelo(self, criado_por_perfil: PerfilUsuario, polo_fixo_id: UUID | None):
        # GESTOR_POLO/PERSONALIZADO (módulo professores) só pode cadastrar
        # PROFESSOR — mesma restrição do cadastro individual (ver
        # UsuarioService.validar) — então nem oferecemos outro perfil no modelo.
        perfis_disponiveis = (
            [PerfilUsuario.PROFESSOR]
            if criado_por_perfil in (PerfilUsuario.GESTOR_POLO, PerfilUsuario.PERSONALIZADO)
            else list(PerfilUsuario)
        )
        return gerar_modelo(
            "Modelo de Importação — Professores/Usuários",
            _colunas(perfis_disponiveis, incluir_polo=polo_fixo_id is None),
        )

    def importar(self, linhas: list[dict], confirmar: bool, usuario: UsuarioAutenticado) -> ResultadoImportacao:
        polo_fixo_id = usuario.polo_id if usuario.perfil == PerfilUsuario.GESTOR_POLO else None
        opcoes_polo = [(p.id, p.nome) for p in self.polo_repo.listar()] if polo_fixo_id is None else []
        opcoes_almoxarifado = [(a.id, a.nome) for a in self.almoxarifado_repo.listar()]
        opcoes_papel = [(p.id, p.nome) for p in self.papel_repo.listar()]

        def resolver_perfil(valor: str) -> PerfilUsuario:
            alvo = valor.strip().upper()
            for perfil in PerfilUsuario:
                if perfil.value.upper() == alvo:
                    return perfil
            validos = ", ".join(p.value for p in PerfilUsuario)
            raise RegraDeNegocioViolada(f'Coluna "{COL_PERFIL}": "{valor}" não é um perfil válido. Use: {validos}.')

        def processar(linha: dict) -> str:
            nome = texto_obrigatorio(linha, COL_NOME)
            email = texto_obrigatorio(linha, COL_EMAIL)
            perfil = resolver_perfil(texto_obrigatorio(linha, COL_PERFIL))
            polo_id = polo_fixo_id
            if polo_id is None:
                polo_id = resolver_por_nome(COL_POLO, texto(linha, COL_POLO), opcoes_polo, obrigatorio=False)
            almoxarifado_id = resolver_por_nome(
                COL_ALMOXARIFADO, texto(linha, COL_ALMOXARIFADO), opcoes_almoxarifado, obrigatorio=False
            )
            papel_id = resolver_por_nome(COL_PAPEL, texto(linha, COL_PAPEL), opcoes_papel, obrigatorio=False)
            senha_temporaria = _gerar_senha_temporaria()

            dados = dict(
                nome=nome, email=email, senha=senha_temporaria, perfil=perfil, polo_id=polo_id,
                criado_por_perfil=usuario.perfil, criado_por_polo_id=usuario.polo_id,
                telefone=texto(linha, COL_TELEFONE), carga_horaria_semanal=texto(linha, COL_CARGA_HORARIA),
                almoxarifado_id=almoxarifado_id, papel_id=papel_id,
            )
            if not confirmar:
                self.service.validar(**dados)
                return f"{nome} ({email})"

            self.service.criar_usuario(**dados)
            try:
                self.email_service.enviar_credenciais_acesso(email, nome, senha_temporaria)
            except Exception:
                # O usuário já foi criado com sucesso — uma falha no envio do
                # e-mail (SMTP fora do ar, por exemplo) não deve derrubar a
                # linha nem o restante do lote. Quem não recebeu o e-mail
                # ainda consegue entrar via "Esqueci minha senha" na tela de
                # login, usando o mesmo e-mail cadastrado.
                return f"{nome} ({email}) — criado, mas o e-mail de credenciais não pôde ser enviado."
            return f"{nome} ({email})"

        return executar_importacao(self.db, linhas, processar, confirmar)
