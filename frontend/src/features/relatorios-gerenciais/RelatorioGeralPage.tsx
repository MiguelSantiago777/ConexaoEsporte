import { useEffect, useMemo, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import type { RelatorioGeral } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { formatarData } from "@/lib/format";
import { exportarPdf } from "@/lib/exportarPdf";

const CORES = ["#00417d", "#fcba27", "#0f5c33", "#8a6008", "#5b6b7a", "#0891b2", "#c2410c", "#7c3aed"];

function primeiroDiaDoMes(): string {
  const hoje = new Date();
  return new Date(hoje.getFullYear(), hoje.getMonth(), 1).toISOString().slice(0, 10);
}

function hoje(): string {
  return new Date().toISOString().slice(0, 10);
}

function KpiCard({ label, valor, sufixo }: { label: string; valor: number | string; sufixo?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200/80 p-4 shadow-sm">
      <div className="text-xs font-semibold uppercase tracking-wide text-gray-400">{label}</div>
      <div className="text-2xl font-bold text-brand-dark mt-1">
        {valor}
        {sufixo && <span className="text-base font-medium text-gray-400">{sufixo}</span>}
      </div>
    </div>
  );
}

/** Relatório consolidado entre TODOS os polos — exclusivo do MASTER. */
export function RelatorioGeralPage() {
  const toast = useToast();
  const [dataInicio, setDataInicio] = useState(primeiroDiaDoMes());
  const [dataFim, setDataFim] = useState(hoje());
  const [relatorio, setRelatorio] = useState<RelatorioGeral | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [exportando, setExportando] = useState(false);
  const conteudoRef = useRef<HTMLDivElement>(null);

  async function baixarPdf() {
    if (!conteudoRef.current) return;
    setExportando(true);
    try {
      await exportarPdf(conteudoRef.current, "relatorio-geral.pdf");
    } catch {
      toast.error("Não foi possível gerar o PDF. Tente novamente.");
    } finally {
      setExportando(false);
    }
  }

  async function gerar() {
    setCarregando(true);
    try {
      const { data } = await api.get<RelatorioGeral>("/relatorios/geral", {
        params: { data_inicio: dataInicio, data_fim: dataFim },
      });
      setRelatorio(data);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao gerar o relatório.");
      setRelatorio(null);
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    gerar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const dadosPizza = useMemo(
    () => relatorio?.beneficiarios_por_polo.map((s) => ({ name: s.label, value: s.valor })) ?? [],
    [relatorio]
  );

  return (
    <div className="space-y-6">
      <Card className="animate-fade-in-up" style={staggerStyle(0)}>
        <div className="flex flex-col sm:flex-row gap-4 sm:items-end flex-wrap">
          <div className="sm:w-44">
            <Input label="Período — de" type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} />
          </div>
          <div className="sm:w-44">
            <Input label="Período — até" type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} />
          </div>
          <Button onClick={gerar} disabled={carregando}>{carregando ? "Gerando…" : "Gerar relatório"}</Button>
          {relatorio && (
            <Button variant="secondary" onClick={baixarPdf} disabled={exportando}>
              {exportando ? "Gerando…" : "Baixar PDF"}
            </Button>
          )}
        </div>
      </Card>

      {carregando && <Spinner label="Gerando relatório…" />}

      {!carregando && !relatorio && (
        <Card><EmptyState message="Selecione um período para gerar o relatório." /></Card>
      )}

      {!carregando && relatorio && (
        <div ref={conteudoRef} className="space-y-6 bg-white">
          <div className="flex items-center gap-3 mb-2 p-2">
            <img src="/logo.png" alt="Conexão Esporte" className="w-10 h-10 object-contain" />
            <div>
              <div className="font-bold text-brand-dark">Relatório Geral — Todos os Polos</div>
              <div className="text-xs text-gray-500">Período: {formatarData(relatorio.data_inicio)} a {formatarData(relatorio.data_fim)}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 animate-fade-in-up" style={staggerStyle(1)}>
            <KpiCard label="Polos" valor={relatorio.kpis.total_polos} />
            <KpiCard label="Beneficiários ativos" valor={relatorio.kpis.total_beneficiarios_ativos} />
            <KpiCard label="Turmas ativas" valor={relatorio.kpis.total_turmas_ativas} />
            <KpiCard label="Frequência média geral" valor={relatorio.kpis.frequencia_media_pct} sufixo="%" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Beneficiários por polo" className="animate-fade-in-up" style={staggerStyle(2)}>
              {dadosPizza.length === 0 ? (
                <EmptyState message="Nenhum beneficiário ativo cadastrado." />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie data={dadosPizza} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={(d) => `${d.name} (${d.value})`} isAnimationActive={false}>
                      {dadosPizza.map((_, i) => <Cell key={i} fill={CORES[i % CORES.length]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </Card>

            <Card title="Ranking de polos por frequência" subtitle="% de presença no período selecionado" className="animate-fade-in-up" style={staggerStyle(3)}>
              {relatorio.ranking_polos.length === 0 ? (
                <EmptyState message="Nenhum polo cadastrado." />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={relatorio.ranking_polos.map((r) => ({ label: r.polo_nome, valor: r.frequencia_media_pct }))} margin={{ left: -20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(v: any) => `${v}%`} />
                    <Bar dataKey="valor" fill="#00417d" radius={[4, 4, 0, 0]} isAnimationActive={false} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>
          </div>

          <Card title="Evolução da frequência geral por semana" className="animate-fade-in-up" style={staggerStyle(4)}>
            {relatorio.frequencia_por_semana.length === 0 ? (
              <EmptyState message="Nenhuma chamada lançada no período." />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={relatorio.frequencia_por_semana} margin={{ left: -20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v: any) => `${v}%`} />
                  <Line type="monotone" dataKey="valor" stroke="#fcba27" strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </Card>

          <Card title="Todos os polos" className="animate-fade-in-up" style={staggerStyle(5)}>
            <div className="overflow-x-auto -mx-6">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                    <th className="py-2.5 px-6">Polo</th>
                    <th className="px-3">Beneficiários ativos</th>
                    <th className="px-3">Frequência média</th>
                  </tr>
                </thead>
                <tbody>
                  {relatorio.ranking_polos.map((r) => (
                    <tr key={r.polo_id} className="border-t border-gray-100">
                      <td className="py-2.5 px-6 font-medium text-gray-800">{r.polo_nome}</td>
                      <td className="px-3 text-gray-600">{r.beneficiarios_ativos}</td>
                      <td className="px-3">
                        <Badge variant={r.frequencia_media_pct >= 75 ? "accent" : "gray"}>{r.frequencia_media_pct}%</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
