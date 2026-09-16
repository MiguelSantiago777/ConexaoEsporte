import { api } from "@/lib/api";
import type { ResultadoImportacao } from "@/types";

/** Baixa o modelo (.xlsx) de importação em massa de um recurso
 * (`beneficiarios`, `turmas`, `usuarios`, `produtos` ou `polos`). */
export async function baixarModeloImportacao(recurso: string, nomeArquivo: string) {
  const resp = await api.get(`/${recurso}/importar/modelo`, { responseType: "blob" });
  const objectUrl = window.URL.createObjectURL(resp.data);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = nomeArquivo;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(objectUrl);
}

/** Envia a planilha preenchida. Com `confirmar=false` só valida (prévia,
 * nada é gravado); com `confirmar=true` grava as linhas válidas. */
export async function enviarPlanilhaImportacao(
  recurso: string,
  arquivo: File,
  confirmar: boolean
): Promise<ResultadoImportacao> {
  const formData = new FormData();
  formData.append("arquivo", arquivo);
  const resp = await api.post<ResultadoImportacao>(`/${recurso}/importar`, formData, {
    params: { confirmar },
  });
  return resp.data;
}
