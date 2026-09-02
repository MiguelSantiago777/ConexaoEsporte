import { useEffect, useMemo, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { RelatorioGeral } from "@/types";
import { Card } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Badge } from "@/components/ui/Badge";
import { DonutChart } from "@/components/ui/charts/DonutChart";
import { CATEGORICAL_PALETTE, COR_OUTROS } from "@/components/ui/charts/palette";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { formatarData } from "@/lib/format";
import { exportarPdf } from "@/lib/exportarPdf";
import { baixarExportacao } from "@/features/fichas-execucao/FichasExecucaoPage";

const MAX_FATIAS_POLO = 4;

function primeiroDiaDoMes(): string {
  const hoje = new Date();
  return new Date(hoje.getFullYear(), hoje.getMonth(), 1).toISOString().slice(0, 10);
}

function hoje(): string {
  return new Date().toISOString().slice(0, 10);
}

/** Relatório consolidado entre TODOS os polos — exclusivo do MASTER. */
export function RelatorioGeralPage() {
  const toast = useToast();
  const [dataInicio, setDataInicio] = useState(primeiroDiaDoMes());
  const [dataFim, setDataFim] = useState(hoje());
  const [relatorio, setRelatorio] = useState<RelatorioGeral | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [exportando, setExportando] = useState(false);
  const [exportandoXlsx, setExportandoXlsx] = useState(false);
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

  async function baixarXlsx() {
    setExportandoXlsx(true);
    try {
      await baixarExportacao(
        `/relatorios/geral/exportar?data_inicio=${dataInicio}&data_fim=${dataFim}`,
        "relatorio-geral.xlsx"
      );
    } catch {
      toast.error("Não foi possível gerar o Excel. Tente novamente.");
    } finally {
      setExportandoXlsx(false);
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
      toast.error(mensagemErroApi(err, "Erro ao gerar o relatório."));
      setRelatorio(null);
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    gerar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const porPolo = useMemo(() => {
    const ordenado = [...(relatorio?.beneficiarios_por_polo ?? [])].sort((a, b) => b.valor - a.valor);
    const principais = ordenado.slice(0, MAX_FATIAS_POLO);
    const resto = ordenado.slice(MAX_FATIAS_POLO).reduce((acc, i) => acc + i.valor, 0);
    const fatias = principais.map((item, i) => ({ label: item.label, value: item.valor, color: CATEGORICAL_PALETTE[i] }));
    if (resto > 0) fatias.push({ label: "Outros polos", value: resto, color: COR_OUTROS });
    return fatias;
  }, [relatorio]);

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
            <>
              <Button variant="secondary" onClick={baixarXlsx} disabled={exportandoXlsx}>
                {exportandoXlsx ? "Gerando…" : "Baixar Excel"}
              </Button>
              <Button variant="secondary" onClick={baixarPdf} disabled={exportando}>
                {exportando ? "Gerando…" : "Baixar PDF"}
              </Button>
            </>
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

          <div className="flex flex-wrap justify-center gap-5 animate-fade-in-up" style={staggerStyle(1)}>
            <StatTile compact label="Polos" value={relatorio.kpis.total_polos} />
            <StatTile compact label="Beneficiários ativos" value={relatorio.kpis.total_beneficiarios_ativos} />
            <StatTile compact label="Turmas ativas" value={relatorio.kpis.total_turmas_ativas} />
            <StatTile compact label="Frequência média geral" value={`${relatorio.kpis.frequencia_media_pct}%`} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Beneficiários por polo" className="animate-fade-in-up" style={staggerStyle(2)}>
              {porPolo.length === 0 ? (
                <EmptyState message="Nenhum beneficiário ativo cadastrado." />
              ) : (
                <div className="flex justify-center">
                  <DonutChart data={porPolo} />
                </div>
              )}
            </Card>

            <Card title="Ranking de polos por frequência" subtitle="% de presença no período selecionado" className="animate-fade-in-up" style={staggerStyle(3)}>
              {relatorio.ranking_polos.length === 0 ? (
                <EmptyState message="Nenhum polo cadastrado." />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={relatorio.ranking_polos.map((r) => ({ label: r.polo_nome, valor: r.frequencia_media_pct }))} margin={{ left: 0, right: 12, top: 4, bottom: 0 }}>
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
                <LineChart data={relatorio.frequencia_por_semana} margin={{ left: 0, right: 12, top: 4, bottom: 0 }}>
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
            {/* Celular: lista de cards. Telas sm+ (e a captura de PDF): tabela. */}
            <ul className="sm:hidden divide-y divide-gray-100">
              {relatorio.ranking_polos.map((r) => (
                <li key={r.polo_id} className="py-3 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="font-medium text-gray-800 truncate">{r.polo_nome}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{r.beneficiarios_ativos} beneficiários ativos</div>
                  </div>
                  <Badge variant={r.frequencia_media_pct >= 75 ? "accent" : "gray"}>{r.frequencia_media_pct}%</Badge>
                </li>
              ))}
            </ul>

            <div className="hidden sm:block overflow-x-auto -mx-5 sm:-mx-8">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                    <th className="py-2.5 px-8">Polo</th>
                    <th className="px-3">Beneficiários ativos</th>
                    <th className="px-3 pr-8">Frequência média</th>
                  </tr>
                </thead>
                <tbody>
                  {relatorio.ranking_polos.map((r) => (
                    <tr key={r.polo_id} className="border-t border-gray-100">
                      <td className="py-2.5 px-8 font-medium text-gray-800">{r.polo_nome}</td>
                      <td className="px-3 text-gray-600">{r.beneficiarios_ativos}</td>
                      <td className="px-3 pr-8">
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
