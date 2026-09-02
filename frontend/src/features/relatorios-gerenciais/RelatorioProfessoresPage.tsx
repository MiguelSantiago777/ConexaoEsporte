import { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Polo, Usuario } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { staggerStyle } from "@/lib/animation";
import { mascararNomeLGPD } from "@/lib/masks";
import { exportarPdf } from "@/lib/exportarPdf";
import { exportarXlsx } from "@/lib/exportarXlsx";
import { useToast } from "@/components/ui/toast/ToastContext";

/**
 * Ficha cadastral geral de todos os professores ativos (opcionalmente
 * incluindo os demitidos). Uso externo mascara o nome (LGPD) — uso interno
 * mostra os dados completos. Professores não têm CPF cadastrado no sistema,
 * então só o nome é mascarado (diferente da ficha de beneficiários).
 */
export function RelatorioProfessoresPage() {
  const toast = useToast();
  const { data: usuarios = [], isLoading: carregando } = useQuery({
    queryKey: ["usuarios"],
    queryFn: () => api.get<Usuario[]>("/usuarios").then((r) => r.data),
  });
  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
  });
  const [usoExterno, setUsoExterno] = useState(false);
  const [incluirDemitidos, setIncluirDemitidos] = useState(false);
  const [exportando, setExportando] = useState(false);
  const [exportandoXlsx, setExportandoXlsx] = useState(false);
  const conteudoRef = useRef<HTMLDivElement>(null);

  function poloNome(id: string | null) {
    return polos.find((p) => p.id === id)?.nome ?? "—";
  }

  async function baixarPdf() {
    if (!conteudoRef.current) return;
    setExportando(true);
    try {
      await exportarPdf(conteudoRef.current, "ficha-cadastral-professores.pdf");
    } catch {
      toast.error("Não foi possível gerar o PDF. Tente novamente.");
    } finally {
      setExportando(false);
    }
  }

  async function baixarXlsx() {
    setExportandoXlsx(true);
    try {
      const linhas = ativos.map((p) => ({
        Nome: usoExterno ? mascararNomeLGPD(p.nome) : p.nome,
        Email: p.email,
        Telefone: p.telefone ?? "—",
        Polo: poloNome(p.polo_id),
        "Carga horária": p.carga_horaria_semanal ?? "—",
        ...(incluirDemitidos ? { Situação: p.ativo ? "Ativo" : "Demitido" } : {}),
      }));
      await exportarXlsx(linhas, "ficha-cadastral-professores.xlsx", "Professores");
    } catch {
      toast.error("Não foi possível gerar o Excel. Tente novamente.");
    } finally {
      setExportandoXlsx(false);
    }
  }

  const ativos = usuarios.filter((u) => u.perfil === "PROFESSOR" && (incluirDemitidos || u.ativo));

  return (
    <div className="space-y-6">
      <Card className="animate-fade-in-up" style={staggerStyle(0)}>
        <div className="flex flex-col sm:flex-row gap-4 sm:items-center justify-between">
          <div className="flex flex-col sm:flex-row gap-4 sm:items-center">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                className="w-5 h-5 accent-[#fcba27] rounded"
                checked={usoExterno}
                onChange={(e) => setUsoExterno(e.target.checked)}
              />
              <span className="text-sm text-gray-700">
                Uso externo <span className="text-gray-400">— mascara o nome (LGPD)</span>
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                className="w-5 h-5 accent-[#fcba27] rounded"
                checked={incluirDemitidos}
                onChange={(e) => setIncluirDemitidos(e.target.checked)}
              />
              <span className="text-sm text-gray-700">
                Incluir demitidos <span className="text-gray-400">— consta no sistema como inativo</span>
              </span>
            </label>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={baixarXlsx} disabled={ativos.length === 0 || exportandoXlsx}>
              {exportandoXlsx ? "Gerando…" : "Baixar Excel"}
            </Button>
            <Button variant="secondary" onClick={baixarPdf} disabled={exportando}>
              {exportando ? "Gerando…" : "Baixar PDF"}
            </Button>
          </div>
        </div>
      </Card>

      <div ref={conteudoRef} className="bg-white">
      <div className="flex items-center gap-3 mb-4 p-2">
        <img src="/logo.png" alt="Conexão Esporte" className="w-10 h-10 object-contain" />
        <div className="font-bold text-brand-dark">Ficha Cadastral Geral de Professores</div>
      </div>

      <Card
        title="Professores"
        actions={<Badge variant="accent">{ativos.length}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(1)}
      >
        {carregando ? (
          <Spinner label="Carregando professores…" />
        ) : ativos.length === 0 ? (
          <EmptyState message={incluirDemitidos ? "Nenhum professor cadastrado." : "Nenhum professor ativo cadastrado."} />
        ) : (
          <>
            {/* Celular: lista de cards. Telas sm+ (e a captura de PDF): tabela. */}
            <ul className="sm:hidden divide-y divide-gray-100">
              {ativos.map((p) => (
                <li key={p.id} className="py-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-gray-800">{usoExterno ? mascararNomeLGPD(p.nome) : p.nome}</span>
                    {incluirDemitidos && (
                      <Badge variant={p.ativo ? "accent" : "gray"}>{p.ativo ? "Ativo" : "Demitido"}</Badge>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">{p.email}</div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {poloNome(p.polo_id)} · {p.telefone ?? "—"} · {p.carga_horaria_semanal ?? "—"}
                  </div>
                </li>
              ))}
            </ul>

            <div className="hidden sm:block overflow-x-auto -mx-5 sm:-mx-8">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                    <th className="py-2.5 px-8">Nome</th>
                    <th className="px-3">Email</th>
                    <th className="px-3">Telefone</th>
                    <th className="px-3">Polo</th>
                    <th className={`px-3 ${incluirDemitidos ? "" : "pr-8"}`}>Carga horária</th>
                    {incluirDemitidos && <th className="px-3 pr-8">Situação</th>}
                  </tr>
                </thead>
                <tbody>
                  {ativos.map((p) => (
                    <tr key={p.id} className="border-t border-gray-100">
                      <td className="py-2.5 px-8 font-medium text-gray-800">
                        {usoExterno ? mascararNomeLGPD(p.nome) : p.nome}
                      </td>
                      <td className="px-3 text-gray-600">{p.email}</td>
                      <td className="px-3 text-gray-600">{p.telefone ?? "—"}</td>
                      <td className="px-3 text-gray-600">{poloNome(p.polo_id)}</td>
                      <td className={`px-3 text-gray-600 ${incluirDemitidos ? "" : "pr-8"}`}>{p.carga_horaria_semanal ?? "—"}</td>
                      {incluirDemitidos && (
                        <td className="px-3 pr-8">
                          <Badge variant={p.ativo ? "accent" : "gray"}>{p.ativo ? "Ativo" : "Demitido"}</Badge>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </Card>
      </div>
    </div>
  );
}
