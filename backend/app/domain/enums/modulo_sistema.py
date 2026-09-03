"""
Catálogo fixo dos módulos (áreas) do sistema que a Central de Acessos deixa
o MASTER escolher, um a um, ao montar um Papel personalizado — cada chave
aqui corresponde a uma seção do menu e a um bloco de rotas do backend (ver
`require_papel_ou_perfis` em app/core/dependencies.py, usado nos routers).
"""

MODULOS_SISTEMA: dict[str, str] = {
    "beneficiarios": "Beneficiários",
    "polos": "Polos",
    "professores": "Professores",
    "turmas": "Turmas",
    "modalidades": "Modalidades",
    "almoxarifados": "Almoxarifados",
    "estoque": "Estoque",
    "entregas_materiais": "Entregas de Materiais",
    "relatorios_gerenciais": "Relatórios",
    "anexos_gerais": "Anexos Gerais",
    "fichas_execucao": "Fichas de Execução",
    "configuracoes": "Configurações",
}


def modulo_valido(modulo: str) -> bool:
    return modulo in MODULOS_SISTEMA
