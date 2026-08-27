import { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { EntregaMaterial, Polo } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { staggerStyle } from "@/lib/animation";
import { formatarData } from "@/lib/format";
import { exportarPdf } from "@/lib/exportarPdf";
import { exportarXlsx } from "@/lib/exportarXlsx";
import { useToast } from "@/components/ui/toast/ToastContext";

/** Relatório de entregas de materiais: quem entregou, quem recebeu, data e polo. */
export function RelatorioEntregasPage() {
  const toast = useToast();
  const { data: entregas = [], isLoading: carregando } = useQuery({
    queryKey: ["entregas-materiais"],
    queryFn: () => api.get<EntregaMaterial[]>("/entregas-materiais").then((r) => r.data),
  });
  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
  });
  const [exportando, setExportando] = useState(false);
  const [exportandoXlsx, setExportandoXlsx] = useState(false);
  const conteudoRef = useRef<HTMLDivElement>(null);

  function poloNome(id: string) {
    return polos.find((p) => p.id === id)?.nome ?? "—";
  }

  async function baixarPdf() {
    if (!conteudoRef.current) return;
    setExportando(true);
    try {
      await exportarPdf(conteudoRef.current, "relatorio-entregas-materiais.pdf");
    } catch {
      toast.error("Não foi possível gerar o PDF. Tente novamente.");
    } finally {
      setExportando(false);
    }
  }

  async function baixarXlsx() {
    setExportandoXlsx(true);
    try {
      const linhas = entregas.map((e) => ({
        Polo: poloNome(e.polo_id),
        Data: e.data_entrega ? formatarData(e.data_entrega) : "—",
        "Entregue por": e.entregue_por ?? "—",
        "Recebido por": e.coordenador_nome ?? "—",
        Itens:
          e.itens.length === 0 ? "—" : e.itens.map((item) => `${item.descricao} (${item.quantidade})`).join(", "),
      }));
      await exportarXlsx(linhas, "relatorio-entregas-materiais.xlsx", "Entregas");
    } catch {
      toast.error("Não foi possível gerar o Excel. Tente novamente.");
    } finally {
      setExportandoXlsx(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card className="animate-fade-in-up flex justify-end gap-2" style={staggerStyle(0)}>
        <Button variant="secondary" onClick={baixarXlsx} disabled={entregas.length === 0 || exportandoXlsx}>
          {exportandoXlsx ? "Gerando…" : "Baixar Excel"}
        </Button>
        <Button variant="secondary" onClick={baixarPdf} disabled={exportando}>
          {exportando ? "Gerando…" : "Baixar PDF"}
        </Button>
      </Card>

      <div ref={conteudoRef} className="bg-white">
      <div className="flex items-center gap-3 mb-4 p-2">
        <img src="/logo.png" alt="Conexão Esporte" className="w-10 h-10 object-contain" />
        <div>
          <div className="font-bold text-brand-dark">Relatório de Entregas de Materiais</div>
          <div className="text-xs text-gray-500">Todos os polos</div>
        </div>
      </div>

      <Card
        title="Entregas registradas"
        actions={<Badge variant="accent">{entregas.length}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(1)}
      >
        {carregando ? (
          <Spinner label="Carregando entregas…" />
        ) : entregas.length === 0 ? (
          <EmptyState message="Nenhuma entrega registrada ainda." />
        ) : (
          <div className="overflow-x-auto -mx-6">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                  <th className="py-2.5 px-6">Polo</th>
                  <th className="px-3">Data</th>
                  <th className="px-3">Entregue por</th>
                  <th className="px-3">Recebido por</th>
                  <th className="px-3">Itens</th>
                </tr>
              </thead>
              <tbody>
                {entregas.map((e) => (
                  <tr key={e.id} className="border-t border-gray-100">
                    <td className="py-2.5 px-6 font-medium text-gray-800">{poloNome(e.polo_id)}</td>
                    <td className="px-3 text-gray-600">{e.data_entrega ? formatarData(e.data_entrega) : "—"}</td>
                    <td className="px-3 text-gray-600">{e.entregue_por ?? "—"}</td>
                    <td className="px-3 text-gray-600">{e.coordenador_nome ?? "—"}</td>
                    <td className="px-3 text-gray-600">
                      {e.itens.length === 0
                        ? "—"
                        : e.itens.map((item) => `${item.descricao} (${item.quantidade})`).join(", ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      </div>
    </div>
  );
}
