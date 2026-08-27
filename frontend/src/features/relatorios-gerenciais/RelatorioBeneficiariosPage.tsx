import { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Beneficiario, Polo } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { staggerStyle } from "@/lib/animation";
import { formatarData } from "@/lib/format";
import { maskCPF, maskTelefone, mascararCPFLGPD, mascararNomeLGPD } from "@/lib/masks";
import { exportarPdf } from "@/lib/exportarPdf";
import { useToast } from "@/components/ui/toast/ToastContext";

/**
 * Ficha cadastral geral de todos os beneficiários ativos. Uso externo
 * mascara nome e CPF (LGPD) — do beneficiário e também do responsável —
 * uso interno mostra os dados completos.
 */
export function RelatorioBeneficiariosPage() {
  const toast = useToast();
  const { data: beneficiarios = [], isLoading: carregando } = useQuery({
    queryKey: ["beneficiarios"],
    queryFn: () => api.get<Beneficiario[]>("/beneficiarios").then((r) => r.data),
  });
  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
  });
  const [usoExterno, setUsoExterno] = useState(false);
  const [exportando, setExportando] = useState(false);
  const conteudoRef = useRef<HTMLDivElement>(null);

  function poloNome(id: string | null) {
    return polos.find((p) => p.id === id)?.nome ?? "—";
  }

  async function baixarPdf() {
    if (!conteudoRef.current) return;
    setExportando(true);
    try {
      await exportarPdf(conteudoRef.current, "ficha-cadastral-beneficiarios.pdf");
    } catch {
      toast.error("Não foi possível gerar o PDF. Tente novamente.");
    } finally {
      setExportando(false);
    }
  }

  const ativos = beneficiarios.filter((b) => b.ativo);

  return (
    <div className="space-y-6">
      <Card className="animate-fade-in-up" style={staggerStyle(0)}>
        <div className="flex flex-col sm:flex-row gap-4 sm:items-center justify-between">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              className="w-5 h-5 accent-[#fcba27] rounded"
              checked={usoExterno}
              onChange={(e) => setUsoExterno(e.target.checked)}
            />
            <span className="text-sm text-gray-700">
              Uso externo <span className="text-gray-400">— mascara nome e CPF (LGPD)</span>
            </span>
          </label>
          <Button variant="secondary" onClick={baixarPdf} disabled={exportando}>
            {exportando ? "Gerando…" : "Baixar PDF"}
          </Button>
        </div>
      </Card>

      <div ref={conteudoRef} className="bg-white">
      <div className="flex items-center gap-3 mb-4 p-2">
        <img src="/logo.png" alt="Conexão Esporte" className="w-10 h-10 object-contain" />
        <div className="font-bold text-brand-dark">Ficha Cadastral Geral de Beneficiários</div>
      </div>

      <Card
        title="Beneficiários"
        actions={<Badge variant="accent">{ativos.length}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(1)}
      >
        {carregando ? (
          <Spinner label="Carregando beneficiários…" />
        ) : ativos.length === 0 ? (
          <EmptyState message="Nenhum beneficiário ativo cadastrado." />
        ) : (
          <div className="overflow-x-auto -mx-6">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                  <th className="py-2.5 px-6">Nome</th>
                  <th className="px-3">CPF</th>
                  <th className="px-3">Nascimento</th>
                  <th className="px-3">Polo</th>
                  <th className="px-3">Responsável</th>
                  <th className="px-3">Contato</th>
                </tr>
              </thead>
              <tbody>
                {ativos.map((b) => (
                  <tr key={b.id} className="border-t border-gray-100">
                    <td className="py-2.5 px-6 font-medium text-gray-800">
                      {usoExterno ? mascararNomeLGPD(b.nome_completo) : b.nome_completo}
                    </td>
                    <td className="px-3 text-gray-600">
                      {usoExterno ? mascararCPFLGPD(b.documento) : maskCPF(b.documento)}
                    </td>
                    <td className="px-3 text-gray-600">{formatarData(b.data_nascimento)}</td>
                    <td className="px-3 text-gray-600">{poloNome(b.polo_id)}</td>
                    <td className="px-3 text-gray-600">
                      {b.responsavel_legal_nome
                        ? usoExterno
                          ? mascararNomeLGPD(b.responsavel_legal_nome)
                          : b.responsavel_legal_nome
                        : "—"}
                    </td>
                    <td className="px-3 text-gray-600">
                      {b.responsavel_legal_telefone_1 ? maskTelefone(b.responsavel_legal_telefone_1) : "—"}
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
