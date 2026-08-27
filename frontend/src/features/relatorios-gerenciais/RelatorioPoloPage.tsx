import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
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
import type { Polo, RelatorioPolo } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { PageHeader } from "@/components/ui/PageHeader";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";
import { useAuth } from "@/features/auth/AuthContext";
import { staggerStyle } from "@/lib/animation";
import { formatarData } from "@/lib/format";

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

export function RelatorioPoloPage() {
  const { usuario, temPerfil } = useAuth();
  const ehMaster = temPerfil("MASTER");
  const toast = useToast();

  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
    enabled: ehMaster,
  });
  const [poloId, setPoloId] = useState(usuario?.polo_id ?? "");
  const [dataInicio, setDataInicio] = useState(primeiroDiaDoMes());
  const [dataFim, setDataFim] = useState(hoje());
  const [relatorio, setRelatorio] = useState<RelatorioPolo | null>(null);
  const [carregando, setCarregando] = useState(false);

  useEffect(() => {
    if (!poloId && polos.length > 0) setPoloId(polos[0].id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [polos]);

  async function gerar() {
    if (!poloId) return;
    setCarregando(true);
    try {
      const { data } = await api.get<RelatorioPolo>(`/relatorios/polo/${poloId}`, {
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
    if (poloId) gerar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [poloId]);

  const dadosPizza = useMemo(
    () => relatorio?.beneficiarios_por_modalidade.map((s) => ({ name: s.label, value: s.valor })) ?? [],
    [relatorio]
  );

  return (
    <div className="space-y-6">
      <div className="print:hidden">
        <PageHeader title="Relatório do Polo" subtitle="Frequência, beneficiários por modalidade e desempenho por turma, com gráficos prontos para impressão." />
      </div>

      <Card className="print:hidden animate-fade-in-up" style={staggerStyle(0)}>
        <div className="flex flex-col sm:flex-row gap-4 sm:items-end flex-wrap">
          {ehMaster && (
            <div className="sm:w-64">
              <Select label="Polo" value={poloId} onChange={(e) => setPoloId(e.target.value)}>
                <option value="">— Selecione —</option>
                {polos.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
              </Select>
            </div>
          )}
          <div className="sm:w-44">
            <Input label="Período — de" type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} />
          </div>
          <div className="sm:w-44">
            <Input label="Período — até" type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} />
          </div>
          <Button onClick={gerar} disabled={!poloId || carregando}>{carregando ? "Gerando…" : "Gerar relatório"}</Button>
          {relatorio && (
            <Button variant="secondary" onClick={() => window.print()}>Imprimir / salvar PDF</Button>
          )}
        </div>
      </Card>

      {carregando && <Spinner label="Gerando relatório…" />}

      {!carregando && !relatorio && (
        <Card><EmptyState message="Selecione um polo e um período para gerar o relatório." /></Card>
      )}

      {!carregando && relatorio && (
        <div className="space-y-6">
          <div className="hidden print:flex items-center gap-3 mb-2">
            <img src="/logo.png" alt="Conexão Esporte" className="w-10 h-10 object-contain" />
            <div>
              <div className="font-bold text-brand-dark">Relatório do Polo — {relatorio.polo_nome}</div>
              <div className="text-xs text-gray-500">Período: {formatarData(relatorio.data_inicio)} a {formatarData(relatorio.data_fim)}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 animate-fade-in-up" style={staggerStyle(1)}>
            <KpiCard label="Beneficiários ativos" valor={relatorio.kpis.beneficiarios_ativos} />
            <KpiCard label="Turmas ativas" valor={relatorio.kpis.turmas_ativas} />
            <KpiCard label="Frequência média" valor={relatorio.kpis.frequencia_media_pct} sufixo="%" />
            <KpiCard label="Aulas registradas" valor={relatorio.kpis.aulas_registradas} />
            <KpiCard label="Fotos de evidência" valor={relatorio.kpis.fotos_evidencia} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Beneficiários por modalidade" className="animate-fade-in-up print:break-inside-avoid" style={staggerStyle(2)}>
              {dadosPizza.length === 0 ? (
                <EmptyState message="Sem beneficiários ativos matriculados no período." />
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

            <Card title="Frequência por turma" subtitle="% de presença no período selecionado" className="animate-fade-in-up print:break-inside-avoid" style={staggerStyle(3)}>
              {relatorio.frequencia_por_turma.length === 0 ? (
                <EmptyState message="Nenhuma chamada lançada no período." />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={relatorio.frequencia_por_turma} margin={{ left: -20 }}>
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

          <Card title="Evolução da frequência por semana" className="animate-fade-in-up print:break-inside-avoid" style={staggerStyle(4)}>
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
        </div>
      )}
    </div>
  );
}
