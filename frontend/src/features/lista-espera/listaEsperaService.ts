import { api } from "@/lib/api";
import type { InscricaoListaEspera, OpcoesPublicasListaEspera } from "@/types";

export interface InscricaoListaEsperaPayload {
  nome_completo: string;
  data_nascimento: string;
  documento: string;
  nome_responsavel: string | null;
  documento_responsavel: string | null;
  telefone_whatsapp: string;
  email: string;
  bairro: string | null;
  cidade: string | null;
  modalidade_id: string;
  polo_id: string;
  como_conheceu: string | null;
}

export async function buscarOpcoesPublicas(): Promise<OpcoesPublicasListaEspera> {
  const { data } = await api.get<OpcoesPublicasListaEspera>("/lista-espera/opcoes");
  return data;
}

export async function inscreverNaListaEspera(payload: InscricaoListaEsperaPayload): Promise<InscricaoListaEspera> {
  const { data } = await api.post<InscricaoListaEspera>("/lista-espera", payload);
  return data;
}

export async function listarInscricoesPendentes(poloId?: string): Promise<InscricaoListaEspera[]> {
  const { data } = await api.get<InscricaoListaEspera[]>("/lista-espera", { params: { polo_id: poloId } });
  return data;
}

export async function aceitarInscricao(inscricaoId: string, turmaId: string): Promise<void> {
  await api.post(`/lista-espera/${inscricaoId}/aceitar`, { turma_id: turmaId });
}
