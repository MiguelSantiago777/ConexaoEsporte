// Tipos derivados do schema OpenAPI do backend (gerado em api.generated.ts via
// `npm run codegen`) — mantém os nomes já usados nas telas, mas a forma de
// cada um vem direto do que o backend realmente declara, não de cópias
// mantidas à mão. Rode `npm run codegen` sempre que um endpoint mudar de
// schema no backend, e o `tsc` aponta exatamente onde o frontend precisa
// se ajustar.
import type { components } from "./api.generated";

// UsuarioLogadoResponse.perfil não é estreitado a nível de schema no backend
// (só UsuarioResponse.perfil é) — sobrescrevemos aqui porque o RBAC do
// frontend inteiro (temPerfil, guards de rota) depende desse union estreito.
export type Perfil = components["schemas"]["PerfilUsuario"];
export type UsuarioLogado = Omit<components["schemas"]["UsuarioLogadoResponse"], "perfil"> & {
  perfil: Perfil;
};

export type TermoAditivo = components["schemas"]["TermoAditivoItem"];
export type Polo = components["schemas"]["PoloResponse"];

export type ItemEntrega = components["schemas"]["ItemEntregaRequest"];
export type EntregaMaterial = components["schemas"]["EntregaMaterialResponse"];

// Estoque — Almoxarifados (locais físicos), catálogo de Produto e
// Movimentos (Entrada/Saída). O saldo de cada Produto é controlado
// separadamente em cada Almoxarifado. A Saída não tem rota própria: nasce
// automaticamente de um item de Entrega de Materiais que referencia um
// produto + almoxarifado.
export type Almoxarifado = components["schemas"]["AlmoxarifadoResponse"];
export type Produto = components["schemas"]["ProdutoResponse"];
export type SaldoAlmoxarifado = components["schemas"]["SaldoAlmoxarifadoItem"];
// Inverso do anterior: saldo de cada produto num almoxarifado já conhecido
// — usado no dashboard do Coordenador de Almoxarifado.
export type SaldoProdutoNoAlmoxarifado = components["schemas"]["SaldoProdutoNoAlmoxarifadoItem"];
export type MovimentoEstoque = components["schemas"]["MovimentoEstoqueResponse"];
export type TipoMovimentoEstoque = MovimentoEstoque["tipo"];
export type SaldoProduto = components["schemas"]["SaldoProdutoItem"];
export type RelatorioEstoque = components["schemas"]["RelatorioEstoqueResponse"];

export type Usuario = components["schemas"]["UsuarioResponse"];

export type Modalidade = components["schemas"]["ModalidadeResponse"];

export type Turma = components["schemas"]["TurmaResponse"];

// Nomenclatura oficial e obrigatória do sistema: BENEFICIÁRIO (nunca "aluno").
export type Beneficiario = components["schemas"]["BeneficiarioResponse"];

// Vínculo N:N entre beneficiário e turma — um beneficiário pode ter várias
// matrículas ativas ao mesmo tempo (ex.: judô e natação).
export type Matricula = components["schemas"]["MatriculaResponse"];

// Foto de evidência anexada a uma chamada (turma + data), comprovando que a
// aula realmente aconteceu.
export type ChamadaEvidencia = components["schemas"]["ChamadaEvidenciaResponse"];

// Relatórios gerenciais (KPIs e séries para gráficos) — Polo e Geral.
export type SeriePonto = components["schemas"]["SeriePonto"];
export type KPIsPolo = components["schemas"]["KPIsPolo"];
export type RelatorioPolo = components["schemas"]["RelatorioPoloResponse"];
export type KPIsGeral = components["schemas"]["KPIsGeral"];
export type RankingPolo = components["schemas"]["RankingPolo"];
export type RelatorioGeral = components["schemas"]["RelatorioGeralResponse"];

export type RelatorioAula = components["schemas"]["RelatorioAulaResponse"];

// Ficha Técnica de Execução da Entidade (Portaria nº 102/2024) — uma por
// polo e por período/trimestre reportado, exclusivo do MASTER.
export type EtapaMeta = components["schemas"]["EtapaMetaItem"];
export type MetaExecucao = components["schemas"]["MetaItem"];
export type AtividadeComparativo = components["schemas"]["AtividadeComparativoItem"];
export type ChecklistDocumento = components["schemas"]["ChecklistDocumentoItem"];

// FichaExecucaoResponse.ajuste_status também não é estreitado no schema do
// backend — este union continua sendo o valor de referência para o <Select>
// da tela de detalhe da ficha.
export type AjusteStatus = "NAO_SOLICITADO" | "APROVADO" | "NAO_APROVADO";

export type FichaExecucao = components["schemas"]["FichaExecucaoResponse"];

export type TokenResponse = components["schemas"]["TokenResponse"];

// Frequência/Chamada — presença por beneficiário+turma+data, com falta
// justificada opcional (texto livre) distinta de falta comum.
export type Frequencia = components["schemas"]["FrequenciaResponse"];

// Impeditivo de Aula — dia em que a turma inteira não teve aula (feriado
// etc.), vale para todos os beneficiários matriculados naquela data.
export type ImpeditivoAula = components["schemas"]["ImpeditivoAulaResponse"];

// Ficha de Chamada mensal agregada — status_por_data não é estreitado no
// schema do backend (é um dict de string→string) porque o valor é
// calculado dinamicamente; este union é o conjunto real de status que o
// backend emite.
export type StatusDia = "PRESENTE" | "FALTA" | "FALTA_JUSTIFICADA" | "IMPEDITIVO" | "SEM_MARCACAO";
export type LinhaFichaChamada = Omit<components["schemas"]["LinhaFichaChamada"], "status_por_data"> & {
  status_por_data: Record<string, StatusDia>;
};
export type ResumoFichaChamada = components["schemas"]["ResumoFichaChamada"];
export type JustificativaFalta = components["schemas"]["JustificativaFaltaItem"];
export type FichaChamada = Omit<components["schemas"]["FichaChamadaResponse"], "linhas"> & {
  linhas: LinhaFichaChamada[];
};

// Anexos do cadastro de professor (foto, documentos, contrato).
export type UsuarioDocumento = components["schemas"]["UsuarioDocumentoResponse"];

// Repositório livre de Anexos Gerais por polo (MASTER e GESTOR_POLO).
export type AnexoGeral = components["schemas"]["AnexoGeralResponse"];

// Visão consolidada e somente leitura de tudo que foi anexado pelos polos
// (Anexos Gerais) ou pelos professores ao lançar a chamada (fotos de
// evidência e observações de relatório de aula).
export type DocumentoConsolidado = components["schemas"]["DocumentoConsolidadoResponse"];
export type TipoDocumentoConsolidado = DocumentoConsolidado["tipo"];

// Envelope de paginação das listagens principais (Beneficiários, Turmas,
// Professores, Polos, Entregas de Materiais, Fichas de Execução) — o
// backend gera um schema nomeado por entidade (ex.:
// `PaginaResponse_BeneficiarioResponse_`), mas a forma é sempre a mesma
// (ver `PaginaResponse` em app/interfaces/api/v1/schemas/paginacao_schemas.py),
// então aqui é só um genérico pra não precisar de um alias por entidade.
export interface Pagina<T> {
  itens: T[];
  total: number;
  pagina: number;
  tamanho_pagina: number;
}

// Configuração Geral — número de convênio e datas do projeto, exibidos no
// rodapé de todos os relatórios exportados.
export type ConfiguracaoGeral = components["schemas"]["ConfiguracaoGeralResponse"];

// Central de Acessos (exclusiva do MASTER) — Papel é um nível de acesso
// personalizado (nome + lista de módulos do sistema); um usuário com perfil
// PERSONALIZADO tem seu acesso definido pelo Papel vinculado a ele.
export type ModuloDisponivel = components["schemas"]["ModuloDisponivelItem"];
export type Papel = components["schemas"]["PapelResponse"];
