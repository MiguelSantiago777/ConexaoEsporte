import { useQuery } from "@tanstack/react-query";
import { buscarPortalTransparencia, urlDownloadDocumentoPublico } from "./transparenciaService";
import { StatTile } from "@/components/ui/StatTile";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { PaperclipIcon } from "@/components/ui/icons";
import { formatarData, formatarMoeda } from "@/lib/format";

/** Página pública (sem autenticação) do Portal Transparência — execução
 * física, financeira e documentos do Termo de Fomento, para consulta do
 * órgão fiscalizador e de qualquer visitante. Segue o mesmo painel navy
 * com o brasão de linhas do login/inscrição pública (ver DESIGN.md), mas
 * numa largura de conteúdo densa, própria de uma página de dados. */
export function PortalTransparenciaPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["portal-transparencia"],
    queryFn: buscarPortalTransparencia,
  });

  return (
    <div className="min-h-screen">
      <header className="bg-brand-dark relative overflow-hidden">
        <img
          src="/brasao-linhas.png" alt="" aria-hidden="true"
          className="absolute inset-0 w-full h-full object-contain opacity-[0.06] scale-150 pointer-events-none select-none"
        />
        <div className="relative z-10 max-w-5xl mx-auto px-6 py-12 sm:py-16 text-center">
          <img src="/logo.png" alt="Conexão Esporte" className="w-16 h-16 object-contain mx-auto mb-3" />
          <h1 className="font-display text-3xl sm:text-4xl font-bold text-white">Portal da Transparência</h1>
          <p className="text-sm sm:text-base text-white/70 mt-2 max-w-xl mx-auto">
            {data?.institucional.nome_projeto ?? "Conexão Esporte"} — prestação de contas pública da execução
            física e financeira do Termo de Fomento.
          </p>
          {data?.institucional.numero_convenio && (
            <p className="text-xs text-white/50 mt-4 font-mono tabular-nums">
              Convênio nº {data.institucional.numero_convenio}
              {data.institucional.data_inicio_projeto && data.institucional.data_fim_projeto && (
                <>
                  {" "}· Vigência {formatarData(data.institucional.data_inicio_projeto)} a{" "}
                  {formatarData(data.institucional.data_fim_projeto)}
                </>
              )}
            </p>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-10">
        {isLoading && (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        )}
        {isError && (
          <p className="text-center text-sm text-danger py-16">
            Não foi possível carregar os dados do portal. Tente novamente em instantes.
          </p>
        )}

        {data && (
          <>
            <section>
              <h2 className="font-display text-xl font-bold text-brand-dark mb-4">Execução física</h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <StatTile label="Polos" value={data.execucao_fisica.total_polos} staggerIndex={0} />
                <StatTile label="Modalidades" value={data.execucao_fisica.total_modalidades} staggerIndex={1} />
                <StatTile label="Turmas ativas" value={data.execucao_fisica.total_turmas_ativas} staggerIndex={2} />
                <StatTile
                  label="Beneficiários atendidos" value={data.execucao_fisica.total_beneficiarios_ativos}
                  staggerIndex={3}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mt-4">
                <StatTile
                  label="Frequência média (90 dias)" value={`${data.execucao_fisica.frequencia_media_pct}%`}
                  staggerIndex={4}
                />
              </div>
            </section>

            <section>
              <h2 className="font-display text-xl font-bold text-brand-dark mb-4">Execução financeira</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-5">
                <StatTile label="Total repassado" value={formatarMoeda(data.financeiro.total_repassado)} staggerIndex={0} />
                <StatTile label="Total executado" value={formatarMoeda(data.financeiro.total_executado)} staggerIndex={1} />
                <StatTile label="Saldo" value={formatarMoeda(data.financeiro.saldo)} staggerIndex={2} />
              </div>
              {data.financeiro.por_categoria.length > 0 ? (
                <Card title="Por categoria">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-xs uppercase tracking-wide text-slate-500 border-b border-slate-200">
                          <th className="py-2 pr-4">Categoria</th>
                          <th className="py-2 pr-4 text-right">Repassado</th>
                          <th className="py-2 text-right">Executado</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.financeiro.por_categoria.map((c) => (
                          <tr key={c.categoria} className="border-b border-slate-100 last:border-0">
                            <td className="py-2 pr-4 text-ink">{c.categoria}</td>
                            <td className="py-2 pr-4 text-right font-mono tabular-nums text-ink">
                              {formatarMoeda(c.repassado)}
                            </td>
                            <td className="py-2 text-right font-mono tabular-nums text-ink">
                              {formatarMoeda(c.executado)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              ) : (
                <EmptyState message="Nenhum lançamento financeiro registrado até o momento." />
              )}
            </section>

            <section>
              <h2 className="font-display text-xl font-bold text-brand-dark mb-4">Documentos do convênio</h2>
              {data.documentos.length > 0 ? (
                <Card>
                  <ul className="divide-y divide-slate-100">
                    {data.documentos.map((doc) => (
                      <li key={doc.id} className="flex items-center justify-between gap-4 py-3">
                        <div className="flex items-center gap-3 min-w-0">
                          <PaperclipIcon className="w-4 h-4 text-slate-400 shrink-0" />
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-ink truncate">{doc.titulo}</p>
                            <p className="text-xs text-slate-500">
                              {doc.polo_nome} · {formatarData(doc.criado_em?.slice(0, 10))}
                            </p>
                          </div>
                        </div>
                        <a
                          href={urlDownloadDocumentoPublico(doc.id)} target="_blank" rel="noreferrer"
                          className="text-sm font-medium text-brand hover:text-brand-dark shrink-0"
                        >
                          Baixar
                        </a>
                      </li>
                    ))}
                  </ul>
                </Card>
              ) : (
                <EmptyState message="Nenhum documento público disponível até o momento." />
              )}
            </section>

            <footer className="text-center text-xs text-slate-400 pt-4">
              Atualizado em {new Date(data.atualizado_em).toLocaleString("pt-BR")}
            </footer>
          </>
        )}
      </main>
    </div>
  );
}
