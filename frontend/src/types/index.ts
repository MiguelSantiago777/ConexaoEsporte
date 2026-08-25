// Perfis de acesso (RBAC) — devem espelhar o enum do backend.
export type Perfil = "MASTER" | "GESTOR_POLO" | "PROFESSOR";

export interface UsuarioLogado {
  id: string;
  nome: string;
  email: string;
  perfil: Perfil;
  polo_id: string | null;
  polo_nome: string | null;
  polo_codigo: string | null;
}

export interface Polo {
  id: string;
  nome: string;
  codigo: string | null;
  endereco: string | null;
  horario_funcionamento: string | null;
  status: "ATIVO" | "INATIVO";
  gestor_responsavel_id: string | null;
}

export interface Usuario {
  id: string;
  nome: string;
  email: string;
  perfil: Perfil;
  polo_id: string | null;
  ativo: boolean;
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
  polo_id: string;
  responsavel_legal_nome: string | null;
  responsavel_legal_data_nascimento: string | null;
  responsavel_legal_tipo_relacao: string | null;
  responsavel_legal_telefone_1: string | null;
  responsavel_legal_telefone_2: string | null;
  responsavel_legal_email: string | null;
  responsavel_legal_rede_social: string | null;
  endereco: string | null;
  autoriza_whatsapp: boolean;
  observacoes_medicas: string | null;
  ativo: boolean;
}

// Vínculo N:N entre beneficiário e turma — um beneficiário pode ter várias
// matrículas ativas ao mesmo tempo (ex.: judô e natação).
export interface Matricula {
  id: string;
  beneficiario_id: string;
  turma_id: string;
  ativo: boolean;
  criado_em: string | null;
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
