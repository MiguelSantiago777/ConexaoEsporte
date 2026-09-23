/** Data de hoje no fuso local, no formato do <input type="date"> (AAAA-MM-DD).
 * `toISOString()` usaria UTC — à noite no Brasil já seria "amanhã". */
export function hoje(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
