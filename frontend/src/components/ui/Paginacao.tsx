import { Button } from "@/components/ui/Button";

/** Controles de "página X de Y" usados por todas as listagens paginadas no
 * servidor (Beneficiários, Turmas, Professores, Polos, Entregas de
 * Materiais, Fichas de Execução). Não renderiza nada quando tudo cabe numa
 * página só. */
export function Paginacao({
  pagina,
  tamanhoPagina,
  total,
  onChange,
}: {
  pagina: number;
  tamanhoPagina: number;
  total: number;
  onChange: (pagina: number) => void;
}) {
  const totalPaginas = Math.max(1, Math.ceil(total / tamanhoPagina));
  if (totalPaginas <= 1) return null;

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-4 mt-4 border-t border-gray-100">
      <span className="text-xs text-gray-500">
        Página {pagina} de {totalPaginas} — {total} no total
      </span>
      <div className="flex gap-2">
        <Button variant="secondary" onClick={() => onChange(pagina - 1)} disabled={pagina <= 1}>
          Anterior
        </Button>
        <Button variant="secondary" onClick={() => onChange(pagina + 1)} disabled={pagina >= totalPaginas}>
          Próxima
        </Button>
      </div>
    </div>
  );
}
