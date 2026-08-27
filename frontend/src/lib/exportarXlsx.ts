import { api } from "@/lib/api";

/**
 * Gera o .xlsx no backend (estilo com cor da marca, bordas, largura de
 * coluna automática) a partir de linhas já prontas — os dados que a tela já
 * filtrou/mascarou (ex.: com "Uso externo" ligado). O front não sabe montar
 * um Excel bonito sozinho (a lib client-side não escreve estilo nenhum),
 * então isso vira uma chamada pro endpoint genérico de exportação.
 */
async function baixarXlsxDoBackend(
  abas: { nome: string; colunas: string[]; linhas: (string | number | null)[][] }[],
  nomeArquivo: string,
  titulo?: string
) {
  const resp = await api.post("/relatorios/exportar-xlsx", { titulo, abas }, { responseType: "blob" });
  const objectUrl = window.URL.createObjectURL(resp.data);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = nomeArquivo;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(objectUrl);
}

function linhasParaMatriz(linhas: Record<string, string | number>[]) {
  const colunas = linhas.length > 0 ? Object.keys(linhas[0]) : [];
  const matriz = linhas.map((linha) => colunas.map((c) => linha[c] ?? null));
  return { colunas, matriz };
}

export async function exportarXlsx(
  linhas: Record<string, string | number>[],
  nomeArquivo: string,
  nomeAba = "Planilha"
) {
  const { colunas, matriz } = linhasParaMatriz(linhas);
  await baixarXlsxDoBackend([{ nome: nomeAba, colunas, linhas: matriz }], nomeArquivo);
}

/** Várias abas num único arquivo — usado nos relatórios com mais de uma tabela (KPIs + rankings etc.). */
export async function exportarXlsxMultiplasAbas(
  abas: { nome: string; linhas: Record<string, string | number>[] }[],
  nomeArquivo: string
) {
  const abasPayload = abas.map(({ nome, linhas }) => {
    const { colunas, matriz } = linhasParaMatriz(linhas);
    return { nome, colunas, linhas: matriz };
  });
  await baixarXlsxDoBackend(abasPayload, nomeArquivo);
}
