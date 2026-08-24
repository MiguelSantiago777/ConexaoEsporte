// Perfis de acesso (RBAC) — devem espelhar o enum do backend.
export type Perfil = "MASTER" | "GESTOR_POLO" | "PROFESSOR";

export interface UsuarioLogado {
  id: string;
  nome: string;
  email: string;
  perfil: Perfil;
  polo_id: string | null;
}

export interface Polo {
  id: string;
  nome: string;
  endereco: string | null;
  status: "ATIVO" | "INATIVO";
  gestor_responsavel_id: string | null;
}

export interface Modalidade {
  id: string;
  nome: string;
  descricao: string | null;
}

export interface Turma {
  id: string;
  polo_id: string;
  modalidade_id: string;
  professor_id: string | null;
  horario_inicio: string;
  horario_fim: string;
  dias_semana: string[];
  limite_vagas: number;
  vagas_ocupadas: number;
}

// Nomenclatura oficial e obrigatória do sistema: BENEFICIÁRIO (nunca "aluno").
export interface Beneficiario {
  id: string;
  nome_completo: string;
  data_nascimento: string;
  documento: string;
  responsavel_legal_nome: string | null;
  responsavel_legal_contato: string | null;
  contato: string | null;
  endereco: string | null;
  turma_id: string | null;
  observacoes_medicas: string | null;
  ativo: boolean;
}

export interface RegistroFrequencia {
  id: string;
  turma_id: string;
  beneficiario_id: string;
  data: string;
  presente: boolean;
  registrado_por_id: string;
}

export interface RelatorioAula {
  id: string;
  turma_id: string;
  professor_id: string;
  data: string;
  conteudo_trabalhado: string;
  observacoes: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
