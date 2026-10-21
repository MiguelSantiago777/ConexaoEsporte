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
  tamanho_camisa: string | null;
  tamanho_calcado: string | null;
  turno: "MANHA" | "TARDE";
}

export async function buscarOpcoesPublicas(): Promise<OpcoesPublicasListaEspera> {
  const { data } = await api.get<OpcoesPublicasListaEspera>("/lista-espera/opcoes");
  return data;
}

/** multipart: `dados` leva o JSON da inscrição e `documento_identidade` o
 * arquivo (foto ou PDF) da identidade do participante. */
export async function inscreverNaListaEspera(
  payload: InscricaoListaEsperaPayload, documentoIdentidade: File | null,
): Promise<InscricaoListaEspera> {
  const formData = new FormData();
  formData.append("dados", JSON.stringify(payload));
  if (documentoIdentidade) formData.append("documento_identidade", documentoIdentidade);
  const { data } = await api.post<InscricaoListaEspera>("/lista-espera", formData);
  return data;
}

export async function baixarDocumentoIdentidade(inscricaoId: string): Promise<Blob> {
  const { data } = await api.get<Blob>(`/lista-espera/${inscricaoId}/documento-identidade`, { responseType: "blob" });
  return data;
}

export async function listarInscricoesPendentes(poloId?: string): Promise<InscricaoListaEspera[]> {
  const { data } = await api.get<InscricaoListaEspera[]>("/lista-espera", { params: { polo_id: poloId } });
  return data;
}

export async function aceitarInscricao(inscricaoId: string, turmaId: string): Promise<void> {
  await api.post(`/lista-espera/${inscricaoId}/aceitar`, { turma_id: turmaId });
}

export async function excluirInscricao(inscricaoId: string): Promise<void> {
  await api.delete(`/lista-espera/${inscricaoId}`);
}
