import { api } from "@/lib/api";
import type { LancamentoFinanceiro, PortalTransparencia, TipoLancamentoFinanceiro } from "@/types";

export async function buscarPortalTransparencia(): Promise<PortalTransparencia> {
  const { data } = await api.get<PortalTransparencia>("/transparencia/publico");
  return data;
}

export function urlDownloadDocumentoPublico(anexoId: string): string {
  const baseUrl = import.meta.env.VITE_API_URL ?? "/api/v1";
  return `${baseUrl}/transparencia/publico/documentos/${anexoId}/arquivo`;
}

export async function listarLancamentos(poloId?: string): Promise<LancamentoFinanceiro[]> {
  const { data } = await api.get<LancamentoFinanceiro[]>("/transparencia/lancamentos", {
    params: { polo_id: poloId || undefined },
  });
  return data;
}

export interface LancamentoFinanceiroPayload {
  categoria: string;
  tipo: TipoLancamentoFinanceiro;
  valor: number;
  data_lancamento: string;
  descricao: string | null;
  polo_id: string | null;
}

export async function criarLancamento(payload: LancamentoFinanceiroPayload): Promise<LancamentoFinanceiro> {
  const { data } = await api.post<LancamentoFinanceiro>("/transparencia/lancamentos", payload);
  return data;
}

export async function removerLancamento(lancamentoId: string): Promise<void> {
  await api.delete(`/transparencia/lancamentos/${lancamentoId}`);
}

export async function definirVisibilidadeAnexo(anexoId: string, publico: boolean): Promise<void> {
  await api.patch(`/anexos-gerais/${anexoId}/visibilidade`, { publico });
}
