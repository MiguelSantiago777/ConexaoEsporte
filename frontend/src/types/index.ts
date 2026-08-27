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
