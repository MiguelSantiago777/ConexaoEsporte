"""
Ponto único de composição (template + envio) para todo email disparado pelo
sistema. Qualquer feature nova que precise mandar email (ex.: confirmação
de inscrição na lista de espera de um beneficiário) ganha um método aqui e
um template em app/infrastructure/email/templates/ — nunca chama o
enviador diretamente.
"""
from app.infrastructure.email import enviador
from app.infrastructure.email.templates import renderizar


class EmailService:
    def enviar_redefinicao_senha(self, destinatario: str, nome: str, link: str, horas_validade: int) -> None:
        """`horas_validade` deve ser o mesmo prazo usado para expirar o token no
        banco (ver AuthService.solicitar_redefinicao_senha) — passado pelo
        chamador em vez de fixo aqui pra nunca divergir do que o link aceita
        de verdade."""
        html = renderizar("redefinir_senha.html", nome=nome, link=link, horas_validade=horas_validade)
        texto_alternativo = (
            f"Olá, {nome}.\n\n"
            "Recebemos uma solicitação para redefinir a senha da sua conta no Conexão Esporte. "
            f"Acesse o link abaixo para escolher uma nova senha (válido por {horas_validade} hora(s)):\n{link}\n\n"
            "Se você não solicitou essa redefinição, ignore este email — sua senha continua a mesma."
        )
        enviador.enviador_email.enviar(
            destinatario=destinatario,
            assunto="Redefinição de senha — Conexão Esporte",
            html=html,
            texto_alternativo=texto_alternativo,
        )

    def enviar_confirmacao_inscricao_lista_espera(
        self, destinatario: str, nome_responsavel_ou_participante: str, nome_participante: str,
        modalidade_nome: str, polo_nome: str,
    ) -> None:
        html = renderizar(
            "confirmacao_inscricao_lista_espera.html",
            nome_responsavel_ou_participante=nome_responsavel_ou_participante,
            nome_participante=nome_participante, modalidade_nome=modalidade_nome, polo_nome=polo_nome,
        )
        texto_alternativo = (
            f"Olá, {nome_responsavel_ou_participante}.\n\n"
            f"Recebemos a inscrição de {nome_participante} na lista de espera do Conexão Esporte, "
            f"para a modalidade {modalidade_nome} no polo {polo_nome}. A equipe do polo vai analisar "
            "a disponibilidade de vagas e entrar em contato em breve."
        )
        enviador.enviador_email.enviar(
            destinatario=destinatario,
            assunto="Inscrição recebida — Conexão Esporte",
            html=html,
            texto_alternativo=texto_alternativo,
        )

    def enviar_aceite_lista_espera(
        self, destinatario: str, nome_responsavel_ou_participante: str, nome_participante: str,
        modalidade_nome: str, polo_nome: str, dias_semana: str, horario_inicio: str, horario_fim: str,
    ) -> None:
        html = renderizar(
            "aceite_lista_espera.html",
            nome_responsavel_ou_participante=nome_responsavel_ou_participante,
            nome_participante=nome_participante, modalidade_nome=modalidade_nome, polo_nome=polo_nome,
            dias_semana=dias_semana, horario_inicio=horario_inicio, horario_fim=horario_fim,
        )
        texto_alternativo = (
            f"Olá, {nome_responsavel_ou_participante}.\n\n"
            f"{nome_participante} foi aceito(a) no Conexão Esporte e já está matriculado(a) na turma de "
            f"{modalidade_nome} no polo {polo_nome}. Dias de aula: {dias_semana}. "
            f"Horário: {horario_inicio} às {horario_fim}."
        )
        enviador.enviador_email.enviar(
            destinatario=destinatario,
            assunto="Inscrição aceita — Conexão Esporte",
            html=html,
            texto_alternativo=texto_alternativo,
        )
