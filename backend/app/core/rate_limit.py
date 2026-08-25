"""
Rate limiting (slowapi/limits) — mitiga força bruta em endpoints sensíveis
(login, troca de senha).

Limitação conhecida: o contador é em memória, por processo. Com múltiplos
workers do Gunicorn (ver deploy/conexao-esporte-api.service), o limite
efetivo é aproximadamente `limite × número de workers`, pois cada worker
mantém sua própria contagem. Ainda assim, reduz bastante a superfície para
tentativas automatizadas de senha. Para um limite exato e compartilhado
entre workers, seria necessário um backend compartilhado (ex.: Redis) — não
incluído aqui para não adicionar mais uma peça de infraestrutura obrigatória
a um deploy que já não precisa dela.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
