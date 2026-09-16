import { Badge } from "@/components/ui/Badge";
import type { LinhaImportacao } from "@/types";

/** Relatório linha a linha de uma importação em massa — mostrado tanto na
 * prévia (nada gravado ainda) quanto depois de confirmar. */
export function ResultadoImportacaoTable({ linhas }: { linhas: LinhaImportacao[] }) {
  return (
    <div className="max-h-72 overflow-y-auto border border-slate-300 rounded-lg">
      <table className="w-full text-sm">
        <thead className="bg-slate-300/10 sticky top-0">
          <tr className="text-left text-slate-500">
            <th className="px-3 py-2 font-medium font-mono tabular-nums w-14">Linha</th>
            <th className="px-3 py-2 font-medium">Registro</th>
            <th className="px-3 py-2 font-medium w-20">Situação</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-300/40">
          {linhas.map((l) => (
            <tr key={l.linha}>
              <td className="px-3 py-2 align-top font-mono tabular-nums text-slate-500">{l.linha}</td>
              <td className="px-3 py-2 align-top">
                <div className="text-ink">{l.resumo || "—"}</div>
                {l.erro && <div className="text-xs text-danger mt-0.5">{l.erro}</div>}
              </td>
              <td className="px-3 py-2 align-top">
                {l.status === "ok" ? <Badge variant="court">OK</Badge> : <Badge variant="danger">Erro</Badge>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
