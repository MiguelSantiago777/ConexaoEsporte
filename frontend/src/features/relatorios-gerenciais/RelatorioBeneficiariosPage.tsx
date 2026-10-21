import { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Beneficiario, Modalidade, Polo } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { staggerStyle } from "@/lib/animation";
import { formatarData } from "@/lib/format";
import { maskCPF, maskTelefone, mascararCPFLGPD, mascararNomeLGPD } from "@/lib/masks";
import { exportarPdf } from "@/lib/exportarPdf";
import { exportarXlsx } from "@/lib/exportarXlsx";
import { useToast } from "@/components/ui/toast/ToastContext";

/**
 * Ficha cadastral geral de todos os beneficiários ativos, opcionalmente
 * filtrada por polo (o filtro também vale pro PDF e o Excel). Uso externo
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
  const { data: modalidades = [] } = useQuery({
    queryKey: ["modalidades"],
    queryFn: () => api.get<Modalidade[]>("/modalidades").then((r) => r.data),
  });
  const [usoExterno, setUsoExterno] = useState(false);
  const [filtroPolo, setFiltroPolo] = useState("");
  const [exportando, setExportando] = useState(false);
  const [exportandoXlsx, setExportandoXlsx] = useState(false);
  const conteudoRef = useRef<HTMLDivElement>(null);

  function poloNome(id: string | null) {
    return polos.find((p) => p.id === id)?.nome ?? "—";
  }

  /** "Futebol, Vôlei" — matriculadas primeiro, depois as de interesse (ainda aguardando turma). */
  function modalidadesTexto(b: Beneficiario) {
    const nome = (id: string) => modalidades.find((m) => m.id === id)?.nome ?? "—";
    const partes = [...new Set([
      ...(b.modalidades_matriculado ?? []).map(nome),
      ...(b.modalidades_interesse ?? []).map(nome),
    ])];
    return partes.length ? partes.join(", ") : "—";
  }

  async function baixarPdf() {
    if (!conteudoRef.current) return;
    setExportando(true);
    try {
      await exportarPdf(conteudoRef.current, `ficha-cadastral-beneficiarios${sufixoArquivo}.pdf`);
    } catch {
      toast.error("Não foi possível gerar o PDF. Tente novamente.");
    } finally {
      setExportando(false);
    }
  }

  async function baixarXlsx() {
    setExportandoXlsx(true);
    try {
      const linhas = ativos.map((b) => ({
        Nome: usoExterno ? mascararNomeLGPD(b.nome_completo) : b.nome_completo,
        CPF: usoExterno ? mascararCPFLGPD(b.documento) : maskCPF(b.documento),
        Nascimento: formatarData(b.data_nascimento),
        Polo: poloNome(b.polo_id),
        Modalidades: modalidadesTexto(b),
        Responsável: b.responsavel_legal_nome
          ? usoExterno
            ? mascararNomeLGPD(b.responsavel_legal_nome)
            : b.responsavel_legal_nome
          : "—",
        Contato: b.responsavel_legal_telefone_1 ? maskTelefone(b.responsavel_legal_telefone_1) : "—",
      }));
      await exportarXlsx(linhas, `ficha-cadastral-beneficiarios${sufixoArquivo}.xlsx`, "Beneficiários");
    } catch {
      toast.error("Não foi possível gerar o Excel. Tente novamente.");
    } finally {
      setExportandoXlsx(false);
    }
  }

  const ativos = beneficiarios.filter((b) => b.ativo && (!filtroPolo || b.polo_id === filtroPolo));
  const poloFiltrado = filtroPolo ? poloNome(filtroPolo) : null;
  const sufixoArquivo = poloFiltrado
    ? `-${poloFiltrado.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}`
    : "";

  return (
    <div className="space-y-6">
      <Card className="animate-fade-in-up" style={staggerStyle(0)}>
        <div className="flex flex-col sm:flex-row gap-4 sm:items-center justify-between">
          <div className="flex flex-col sm:flex-row gap-4 sm:items-center">
            <div className="sm:w-72">
              <Select aria-label="Filtrar por polo" value={filtroPolo} onChange={(e) => setFiltroPolo(e.target.value)}>
                <option value="">Todos os polos</option>
                {polos.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nome}
                  </option>
                ))}
              </Select>
            </div>
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
        <div>
          <div className="font-bold text-brand-dark">Ficha Cadastral Geral de Beneficiários</div>
          {poloFiltrado && <div className="text-sm text-gray-600">Polo: {poloFiltrado}</div>}
        </div>
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
          <EmptyState
            message={poloFiltrado ? "Nenhum beneficiário ativo neste polo." : "Nenhum beneficiário ativo cadastrado."}
          />
        ) : (
          <>
            {/* Celular: lista de cards. Telas sm+ (e a captura de PDF/Excel): tabela. */}
            <ul className="sm:hidden divide-y divide-gray-100">
              {ativos.map((b) => (
                <li key={b.id} className="py-3">
                  <div className="font-medium text-gray-800">
                    {usoExterno ? mascararNomeLGPD(b.nome_completo) : b.nome_completo}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {usoExterno ? mascararCPFLGPD(b.documento) : maskCPF(b.documento)} · {formatarData(b.data_nascimento)}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">{poloNome(b.polo_id)}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{modalidadesTexto(b)}</div>
                  {(b.responsavel_legal_nome || b.responsavel_legal_telefone_1) && (
                    <div className="text-xs text-gray-500 mt-0.5">
                      {b.responsavel_legal_nome
                        ? usoExterno
                          ? mascararNomeLGPD(b.responsavel_legal_nome)
                          : b.responsavel_legal_nome
                        : "—"}
                      {b.responsavel_legal_telefone_1 ? ` · ${maskTelefone(b.responsavel_legal_telefone_1)}` : ""}
                    </div>
                  )}
                </li>
              ))}
            </ul>

            <div className="hidden sm:block overflow-x-auto -mx-5 sm:-mx-8">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                    <th className="py-2.5 px-8">Nome</th>
                    <th className="px-3">CPF</th>
                    <th className="px-3">Nascimento</th>
                    <th className="px-3">Polo</th>
                    <th className="px-3">Modalidades</th>
                    <th className="px-3">Responsável</th>
                    <th className="px-3 pr-8">Contato</th>
                  </tr>
                </thead>
                <tbody>
                  {ativos.map((b) => (
                    <tr key={b.id} className="border-t border-gray-100">
                      <td className="py-2.5 px-8 font-medium text-gray-800">
                        {usoExterno ? mascararNomeLGPD(b.nome_completo) : b.nome_completo}
                      </td>
                      <td className="px-3 text-gray-600">
                        {usoExterno ? mascararCPFLGPD(b.documento) : maskCPF(b.documento)}
                      </td>
                      <td className="px-3 text-gray-600">{formatarData(b.data_nascimento)}</td>
                      <td className="px-3 text-gray-600">{poloNome(b.polo_id)}</td>
                      <td className="px-3 text-gray-600">{modalidadesTexto(b)}</td>
                      <td className="px-3 text-gray-600">
                        {b.responsavel_legal_nome
                          ? usoExterno
                            ? mascararNomeLGPD(b.responsavel_legal_nome)
                            : b.responsavel_legal_nome
                          : "—"}
                      </td>
                      <td className="px-3 pr-8 text-gray-600">
                        {b.responsavel_legal_telefone_1 ? maskTelefone(b.responsavel_legal_telefone_1) : "—"}
                      </td>
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
