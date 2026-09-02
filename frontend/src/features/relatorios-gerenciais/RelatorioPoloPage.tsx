import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
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
import type { Polo, RelatorioPolo } from "@/types";
import { Card } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { DonutChart } from "@/components/ui/charts/DonutChart";
import { CATEGORICAL_PALETTE, COR_OUTROS } from "@/components/ui/charts/palette";
import { useToast } from "@/components/ui/toast/ToastContext";
import { useAuth } from "@/features/auth/AuthContext";
import { staggerStyle } from "@/lib/animation";
import { formatarData } from "@/lib/format";
import { exportarPdf } from "@/lib/exportarPdf";
import { baixarExportacao } from "@/features/fichas-execucao/FichasExecucaoPage";

const MAX_FATIAS_MODALIDADE = 4;

function primeiroDiaDoMes(): string {
  const hoje = new Date();
  return new Date(hoje.getFullYear(), hoje.getMonth(), 1).toISOString().slice(0, 10);
}

function hoje(): string {
  return new Date().toISOString().slice(0, 10);
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
  const [exportando, setExportando] = useState(false);
  const [exportandoXlsx, setExportandoXlsx] = useState(false);
  const conteudoRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!poloId && polos.length > 0) setPoloId(polos[0].id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [polos]);

  async function baixarPdf() {
    if (!conteudoRef.current) return;
    setExportando(true);
    try {
      await exportarPdf(conteudoRef.current, "relatorio-do-polo.pdf");
    } catch {
      toast.error("Não foi possível gerar o PDF. Tente novamente.");
    } finally {
      setExportando(false);
    }
  }

  async function baixarXlsx() {
    if (!poloId) return;
    setExportandoXlsx(true);
    try {
      await baixarExportacao(
        `/relatorios/polo/${poloId}/exportar?data_inicio=${dataInicio}&data_fim=${dataFim}`,
        "relatorio-do-polo.xlsx"
      );
    } catch {
      toast.error("Não foi possível gerar o Excel. Tente novamente.");
    } finally {
      setExportandoXlsx(false);
    }
  }

  async function gerar() {
    if (!poloId) return;
    setCarregando(true);
    try {
      const { data } = await api.get<RelatorioPolo>(`/relatorios/polo/${poloId}`, {
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
    if (poloId) gerar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [poloId]);

  const porModalidade = useMemo(() => {
    const ordenado = [...(relatorio?.beneficiarios_por_modalidade ?? [])].sort((a, b) => b.valor - a.valor);
    const principais = ordenado.slice(0, MAX_FATIAS_MODALIDADE);
    const resto = ordenado.slice(MAX_FATIAS_MODALIDADE).reduce((acc, i) => acc + i.valor, 0);
    const fatias = principais.map((item, i) => ({ label: item.label, value: item.valor, color: CATEGORICAL_PALETTE[i] }));
    if (resto > 0) fatias.push({ label: "Outras modalidades", value: resto, color: COR_OUTROS });
    return fatias;
  }, [relatorio]);

  return (
    <div className="space-y-6">
      <Card className="animate-fade-in-up" style={staggerStyle(0)}>
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
        <Card><EmptyState message="Selecione um polo e um período para gerar o relatório." /></Card>
      )}

      {!carregando && relatorio && (
        <div ref={conteudoRef} className="space-y-6 bg-white">
          <div className="flex items-center gap-3 mb-2 p-2">
            <img src="/logo.png" alt="Conexão Esporte" className="w-10 h-10 object-contain" />
            <div>
              <div className="font-bold text-brand-dark">Relatório do Polo — {relatorio.polo_nome}</div>
              <div className="text-xs text-gray-500">Período: {formatarData(relatorio.data_inicio)} a {formatarData(relatorio.data_fim)}</div>
            </div>
          </div>

          <div className="flex flex-wrap justify-center gap-5 animate-fade-in-up" style={staggerStyle(1)}>
            <StatTile compact label="Beneficiários ativos" value={relatorio.kpis.beneficiarios_ativos} />
            <StatTile compact label="Turmas ativas" value={relatorio.kpis.turmas_ativas} />
            <StatTile compact label="Frequência média" value={`${relatorio.kpis.frequencia_media_pct}%`} />
            <StatTile compact label="Aulas registradas" value={relatorio.kpis.aulas_registradas} />
            <StatTile compact label="Fotos de evidência" value={relatorio.kpis.fotos_evidencia} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Beneficiários por modalidade" className="animate-fade-in-up" style={staggerStyle(2)}>
              {porModalidade.length === 0 ? (
                <EmptyState message="Sem beneficiários ativos matriculados no período." />
              ) : (
                <div className="flex justify-center">
                  <DonutChart data={porModalidade} />
                </div>
              )}
            </Card>

            <Card title="Frequência por turma" subtitle="% de presença no período selecionado" className="animate-fade-in-up" style={staggerStyle(3)}>
              {relatorio.frequencia_por_turma.length === 0 ? (
                <EmptyState message="Nenhuma chamada lançada no período." />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={relatorio.frequencia_por_turma} margin={{ left: 0, right: 12, top: 4, bottom: 0 }}>
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

          <Card title="Evolução da frequência por semana" className="animate-fade-in-up" style={staggerStyle(4)}>
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
        </div>
      )}
    </div>
  );
}
