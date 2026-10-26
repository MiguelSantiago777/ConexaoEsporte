export function formatarData(iso: string | null | undefined): string {
  if (!iso) return "—";
  const [ano, mes, dia] = iso.split("-");
  if (!ano || !mes || !dia) return iso;
  return `${dia}/${mes}/${ano}`;
}

/** Timestamp ISO (com fuso) -> "dd/mm/aaaa às hh:mm" no horário de Brasília. */
export function formatarDataHora(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const fuso = { timeZone: "America/Sao_Paulo" } as const;
  const data = d.toLocaleDateString("pt-BR", fuso);
  const hora = d.toLocaleTimeString("pt-BR", { ...fuso, hour: "2-digit", minute: "2-digit" });
  return `${data} às ${hora}`;
}

export function formatarMoeda(valor: number): string {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
