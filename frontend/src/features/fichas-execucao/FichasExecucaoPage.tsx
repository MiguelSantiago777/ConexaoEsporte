import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { FichaExecucao, Pagina, Polo } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";
import { Paginacao } from "@/components/ui/Paginacao";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { PencilIcon } from "@/components/ui/icons";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { formatarData } from "@/lib/format";

const TAMANHO_PAGINA = 10;

export async function baixarExportacao(url: string, nomeArquivo: string) {
  const resp = await api.get(url, { responseType: "blob" });
  const objectUrl = window.URL.createObjectURL(resp.data);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = nomeArquivo;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(objectUrl);
}

export function FichasExecucaoPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [pagina, setPagina] = useState(1);
  const fichasQueryKey = ["fichas-execucao", "pagina", pagina];
  const { data: paginaFichas, isLoading: carregando } = useQuery({
    queryKey: fichasQueryKey,
    queryFn: () =>
      api.get<Pagina<FichaExecucao>>("/fichas-execucao", { params: { pagina, tamanho_pagina: TAMANHO_PAGINA } }).then((r) => r.data),
  });
  const fichas = paginaFichas?.itens ?? [];
  const totalFichas = paginaFichas?.total ?? 0;
  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
  });
  const [salvando, setSalvando] = useState(false);
  const [exportando, setExportando] = useState<string | null>(null);
  const [form, setForm] = useState({ polo_id: "", periodo_referencia: "", data_documento: "" });

  function poloNome(id: string) {
    return polos.find((p) => p.id === id)?.nome ?? "—";
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
      await api.post("/fichas-execucao", {
        polo_id: form.polo_id,
        periodo_referencia: form.periodo_referencia,
        data_documento: form.data_documento || null,
      });
      setForm({ polo_id: "", periodo_referencia: "", data_documento: "" });
      toast.success("Ficha de Execução criada.");
      queryClient.invalidateQueries({ queryKey: ["fichas-execucao"] });
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao criar Ficha de Execução."));
    } finally {
      setSalvando(false);
    }
  }

  async function exportar(ficha: FichaExecucao) {
    setExportando(ficha.id);
    try {
      await baixarExportacao(
        `/fichas-execucao/${ficha.id}/exportar`,
        `Ficha Tecnica de Execucao - ${poloNome(ficha.polo_id)} - ${ficha.periodo_referencia}.xlsx`
      );
    } catch {
      toast.error("Não foi possível exportar a ficha.");
    } finally {
      setExportando(null);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Fichas de Execução"
        subtitle="Ficha Técnica de Execução da Entidade (Portaria nº 102/2024), uma por polo e por período reportado."
      />
      <Card title="Criar nova ficha" className="animate-fade-in-up" style={staggerStyle(0)}>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Select
            label="Polo"
            value={form.polo_id}
            onChange={(e) => setForm({ ...form, polo_id: e.target.value })}
            required
          >
            <option value="">— Selecione —</option>
            {polos.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
          </Select>
          <Input
            label="Período de referência"
            placeholder="ex.: 1º Trimestre 2026"
            value={form.periodo_referencia}
            onChange={(e) => setForm({ ...form, periodo_referencia: e.target.value })}
            minLength={2}
            required
          />
          <Input
            label="Data do documento"
            type="date"
            value={form.data_documento}
            onChange={(e) => setForm({ ...form, data_documento: e.target.value })}
          />
          <div className="sm:col-span-3">
            <Button type="submit" disabled={salvando}>{salvando ? "Criando…" : "Criar ficha"}</Button>
          </div>
        </form>
      </Card>

      <Card title="Fichas" actions={<Badge variant="accent">{totalFichas}</Badge>} className="animate-fade-in-up" style={staggerStyle(1)}>
        {carregando ? (
          <Spinner label="Carregando fichas…" />
        ) : totalFichas === 0 ? (
          <EmptyState message="Nenhuma ficha de execução criada ainda." />
        ) : (
          <>
            {/* Celular: lista de cards. Telas sm+: tabela. */}
            <ul className="sm:hidden divide-y divide-gray-100">
              {fichas.map((f) => (
                <li key={f.id} className="py-3.5">
                  <div className="min-w-0">
                    <div className="font-medium text-gray-800 truncate">{poloNome(f.polo_id)}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{f.periodo_referencia}</div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {f.data_documento ? formatarData(f.data_documento) : "Sem data do documento"}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 mt-3">
                    <Link
                      to={`/fichas-execucao/${f.id}`}
                      title="Editar"
                      className="text-gray-400 hover:text-brand transition-colors -m-1.5 p-1.5"
                    >
                      <PencilIcon className="w-[18px] h-[18px]" />
                    </Link>
                    <Button variant="secondary" className="flex-1" onClick={() => exportar(f)} disabled={exportando === f.id}>
                      {exportando === f.id ? "Exportando…" : "Exportar .xlsx"}
                    </Button>
                  </div>
                </li>
              ))}
            </ul>

            <div className="hidden sm:block overflow-x-auto -mx-5 sm:-mx-8">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                    <th className="py-2.5 px-8">Polo</th>
                    <th className="px-3">Período</th>
                    <th className="px-3">Data do documento</th>
                    <th className="px-3 text-right pr-8">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {fichas.map((f) => (
                    <tr key={f.id} className="border-t border-gray-100 hover:bg-brand-light/60 transition-colors">
                      <td className="py-2.5 px-8 font-medium text-gray-800">{poloNome(f.polo_id)}</td>
                      <td className="px-3 text-gray-600">{f.periodo_referencia}</td>
                      <td className="px-3 text-gray-600">{f.data_documento ? formatarData(f.data_documento) : "—"}</td>
                      <td className="px-3 text-right pr-8">
                        <div className="flex items-center justify-end gap-3">
                          <Link to={`/fichas-execucao/${f.id}`} title="Editar" className="text-gray-400 hover:text-brand transition-colors">
                            <PencilIcon />
                          </Link>
                          <Button variant="secondary" onClick={() => exportar(f)} disabled={exportando === f.id}>
                            {exportando === f.id ? "Exportando…" : "Exportar .xlsx"}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        <Paginacao pagina={pagina} tamanhoPagina={TAMANHO_PAGINA} total={totalFichas} onChange={setPagina} />
      </Card>
    </div>
  );
}
