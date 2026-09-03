import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { RelatorioEstoque } from "@/types";
import { Card } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { formatarData } from "@/lib/format";
import { exportarPdf } from "@/lib/exportarPdf";
import { exportarXlsxMultiplasAbas } from "@/lib/exportarXlsx";

function primeiroDiaDoMes(): string {
  const hoje = new Date();
  return new Date(hoje.getFullYear(), hoje.getMonth(), 1).toISOString().slice(0, 10);
}

function hoje(): string {
  return new Date().toISOString().slice(0, 10);
}

/** Relatório de Estoque: saldos por produto e o detalhe de Entradas/Saídas
 * do período selecionado — a Saída aparece automaticamente quando nasce de
 * uma Entrega de Materiais. */
export function RelatorioEstoquePage() {
  const toast = useToast();
  const [dataInicio, setDataInicio] = useState(primeiroDiaDoMes());
  const [dataFim, setDataFim] = useState(hoje());
  const [relatorio, setRelatorio] = useState<RelatorioEstoque | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [exportando, setExportando] = useState(false);
  const [exportandoXlsx, setExportandoXlsx] = useState(false);
  const conteudoRef = useRef<HTMLDivElement>(null);

  async function gerar() {
    setCarregando(true);
    try {
      const { data } = await api.get<RelatorioEstoque>("/movimentos-estoque/relatorio", {
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

  function nomeProduto(produtoId: string) {
    return relatorio?.saldos.find((s) => s.produto_id === produtoId)?.produto_nome ?? "—";
  }

  async function baixarPdf() {
    if (!conteudoRef.current) return;
    setExportando(true);
    try {
      await exportarPdf(conteudoRef.current, "relatorio-de-estoque.pdf");
    } catch {
      toast.error("Não foi possível gerar o PDF. Tente novamente.");
    } finally {
      setExportando(false);
    }
  }

  async function baixarXlsx() {
    if (!relatorio) return;
    setExportandoXlsx(true);
    try {
      await exportarXlsxMultiplasAbas(
        [
          {
            nome: "Saldos por produto",
            linhas: relatorio.saldos.map((s) => ({
              Produto: s.produto_nome,
              Unidade: s.unidade_medida,
              "Entradas no período": s.total_entradas,
              "Saídas no período": s.total_saidas,
              "Saldo atual": s.saldo_atual,
            })),
          },
          {
            nome: "Movimentações",
            linhas: relatorio.movimentos.map((m) => ({
              Tipo: m.tipo === "ENTRADA" ? "Entrada" : "Saída",
              Produto: nomeProduto(m.produto_id),
              Quantidade: m.quantidade,
              Data: formatarData(m.data),
              Origem: m.entrega_material_id ? "Entrega de Materiais" : "Lançamento manual",
            })),
          },
        ],
        "relatorio-de-estoque.xlsx"
      );
    } catch {
      toast.error("Não foi possível gerar o Excel. Tente novamente.");
    } finally {
      setExportandoXlsx(false);
    }
  }

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
              <div className="font-bold text-brand-dark">Relatório de Estoque</div>
              <div className="text-xs text-gray-500">Período: {formatarData(relatorio.data_inicio)} a {formatarData(relatorio.data_fim)}</div>
            </div>
          </div>

          <div className="flex flex-wrap justify-center gap-5 animate-fade-in-up" style={staggerStyle(1)}>
            <StatTile compact label="Produtos com movimento" value={relatorio.total_produtos} />
            <StatTile compact label="Entradas no período" value={relatorio.total_entradas_periodo} />
            <StatTile compact label="Saídas no período" value={relatorio.total_saidas_periodo} />
          </div>

          <Card title="Saldos por produto" actions={<Badge variant="accent">{relatorio.saldos.length}</Badge>} className="animate-fade-in-up" style={staggerStyle(2)}>
            {relatorio.saldos.length === 0 ? (
              <EmptyState message="Nenhum produto com movimentação no período." />
            ) : (
              <>
                <ul className="sm:hidden divide-y divide-gray-100">
                  {relatorio.saldos.map((s) => (
                    <li key={s.produto_id} className="py-3">
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-medium text-gray-800 truncate">{s.produto_nome}</span>
                        <Badge variant="brand">{s.saldo_atual} {s.unidade_medida}</Badge>
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5">Entradas: {s.total_entradas} · Saídas: {s.total_saidas}</div>
                    </li>
                  ))}
                </ul>
                <div className="hidden sm:block overflow-x-auto -mx-5 sm:-mx-8">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                        <th className="py-2.5 px-8">Produto</th>
                        <th className="px-3">Unidade</th>
                        <th className="px-3">Entradas</th>
                        <th className="px-3">Saídas</th>
                        <th className="px-3 pr-8">Saldo atual</th>
                      </tr>
                    </thead>
                    <tbody>
                      {relatorio.saldos.map((s) => (
                        <tr key={s.produto_id} className="border-t border-gray-100">
                          <td className="py-2.5 px-8 font-medium text-gray-800">{s.produto_nome}</td>
                          <td className="px-3 text-gray-600">{s.unidade_medida}</td>
                          <td className="px-3 text-gray-600">{s.total_entradas}</td>
                          <td className="px-3 text-gray-600">{s.total_saidas}</td>
                          <td className="px-3 pr-8"><Badge variant="brand">{s.saldo_atual}</Badge></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </Card>

          <Card title="Movimentações do período" actions={<Badge variant="accent">{relatorio.movimentos.length}</Badge>} className="animate-fade-in-up" style={staggerStyle(3)}>
            {relatorio.movimentos.length === 0 ? (
              <EmptyState message="Nenhuma movimentação no período selecionado." />
            ) : (
              <>
                <ul className="sm:hidden divide-y divide-gray-100">
                  {relatorio.movimentos.map((m) => (
                    <li key={m.id} className="py-3">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant={m.tipo === "ENTRADA" ? "accent" : "gray"}>{m.tipo === "ENTRADA" ? "Entrada" : "Saída"}</Badge>
                        <span className="font-medium text-gray-800">{nomeProduto(m.produto_id)}</span>
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {m.quantidade} un. · {formatarData(m.data)}
                        {m.entrega_material_id ? " · via Entrega de Materiais" : ""}
                      </div>
                    </li>
                  ))}
                </ul>
                <div className="hidden sm:block overflow-x-auto -mx-5 sm:-mx-8">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                        <th className="py-2.5 px-8">Tipo</th>
                        <th className="px-3">Produto</th>
                        <th className="px-3">Quantidade</th>
                        <th className="px-3">Data</th>
                        <th className="px-3 pr-8">Origem</th>
                      </tr>
                    </thead>
                    <tbody>
                      {relatorio.movimentos.map((m) => (
                        <tr key={m.id} className="border-t border-gray-100">
                          <td className="py-2.5 px-8"><Badge variant={m.tipo === "ENTRADA" ? "accent" : "gray"}>{m.tipo === "ENTRADA" ? "Entrada" : "Saída"}</Badge></td>
                          <td className="px-3 text-gray-600">{nomeProduto(m.produto_id)}</td>
                          <td className="px-3 text-gray-600">{m.quantidade}</td>
                          <td className="px-3 text-gray-600">{formatarData(m.data)}</td>
                          <td className="px-3 pr-8 text-gray-500 text-xs">{m.entrega_material_id ? "Entrega de Materiais" : "Lançamento manual"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
