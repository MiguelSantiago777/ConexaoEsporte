import { ChangeEvent, useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { ChamadaEvidencia, FichaChamada, StatusDia, Turma } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { PageHeader } from "@/components/ui/PageHeader";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { CameraIcon, CheckCircleIcon, AlertCircleIcon, CalendarOffIcon, CloseIcon } from "@/components/ui/icons";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { baixarExportacao } from "@/features/fichas-execucao/FichasExecucaoPage";
import { exportarPdf } from "@/lib/exportarPdf";
import { exportarXlsxMultiplasAbas } from "@/lib/exportarXlsx";
import { STATUS_ESTILO, diaCurto, fichaChamadaParaAbas } from "./statusChamada";
import { FichaChamadaImpressao } from "./FichaChamadaImpressao";

const MES_ATUAL = new Date().getMonth() + 1;
const ANO_ATUAL = new Date().getFullYear();

function EvidenciaThumb({ evidencia }: { evidencia: ChamadaEvidencia }) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelado = false;
    api.get(`/frequencias/evidencias/${evidencia.id}/arquivo`, { responseType: "blob" }).then((r) => {
      if (cancelado) return;
      objectUrl = window.URL.createObjectURL(r.data);
      setSrc(objectUrl);
    });
    return () => {
      cancelado = true;
      if (objectUrl) window.URL.revokeObjectURL(objectUrl);
    };
  }, [evidencia.id]);

  if (!src) {
    return <div className="w-20 h-20 rounded-lg bg-gray-100 animate-pulse shrink-0" />;
  }
  return (
    <a href={src} target="_blank" rel="noreferrer" title={evidencia.nome_arquivo}>
      <img src={src} alt={evidencia.nome_arquivo} className="w-20 h-20 rounded-lg object-cover border border-gray-200 shrink-0 hover:opacity-80 transition-opacity" />
    </a>
  );
}

/**
 * Chamada/frequência — funcionalidade principal do perfil PROFESSOR. Grade
 * mensal (beneficiário × cada data que a turma tem aula), com impeditivo de
 * aula (turma inteira) e falta justificada (por beneficiário) além da
 * presença/falta simples.
 */
export function FrequenciaPage() {
  const toast = useToast();
  const queryClient = useQueryClient();

  const { data: turmas = [] } = useQuery({
    queryKey: ["turmas"],
    queryFn: () => api.get<Turma[]>("/turmas").then((r) => r.data),
  });

  const [turmaId, setTurmaId] = useState("");
  const [mes, setMes] = useState(MES_ATUAL);
  const [ano, setAno] = useState(ANO_ATUAL);
  const [exportandoPdf, setExportandoPdf] = useState(false);
  const [exportandoXlsx, setExportandoXlsx] = useState(false);
  const fichaImpressaoRef = useRef<HTMLDivElement>(null);

  async function baixarPdfFichaChamada() {
    if (!fichaImpressaoRef.current) return;
    setExportandoPdf(true);
    try {
      await exportarPdf(fichaImpressaoRef.current, "ficha-de-chamada.pdf");
    } catch {
      toast.error("Não foi possível gerar o PDF. Tente novamente.");
    } finally {
      setExportandoPdf(false);
    }
  }

  const fichaQueryKey = ["frequencias", "ficha-chamada", turmaId, mes, ano];
  const { data: ficha, isLoading: carregandoFicha } = useQuery<FichaChamada>({
    queryKey: fichaQueryKey,
    queryFn: () =>
      api
        .get<FichaChamada>("/frequencias/ficha-chamada", { params: { turma_id: turmaId, mes, ano } })
        .then((r) => r.data),
    enabled: !!turmaId,
  });

  async function baixarXlsxFichaChamada() {
    if (!ficha) return;
    setExportandoXlsx(true);
    try {
      await exportarXlsxMultiplasAbas(fichaChamadaParaAbas(ficha), "ficha-de-chamada.xlsx");
    } catch {
      toast.error("Não foi possível gerar o Excel. Tente novamente.");
    } finally {
      setExportandoXlsx(false);
    }
  }

  const marcarMutation = useMutation({
    mutationFn: (payload: {
      beneficiarioId: string;
      data: string;
      presente: boolean;
      faltaJustificada?: boolean;
      justificativa?: string | null;
    }) =>
      api.post("/frequencias/chamada", {
        turma_id: turmaId,
        data: payload.data,
        presencas: [
          {
            beneficiario_id: payload.beneficiarioId,
            presente: payload.presente,
            falta_justificada: payload.faltaJustificada ?? false,
            justificativa: payload.justificativa ?? null,
          },
        ],
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: fichaQueryKey }),
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao atualizar a chamada.")),
  });

  const impeditivoMutation = useMutation({
    mutationFn: (payload: { data: string; justificativa: string }) =>
      api.post("/frequencias/impeditivos", { turma_id: turmaId, data: payload.data, justificativa: payload.justificativa }),
    onSuccess: () => {
      toast.success("Impeditivo de aula registrado.");
      queryClient.invalidateQueries({ queryKey: fichaQueryKey });
    },
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao registrar o impeditivo.")),
  });

  const removerImpeditivoMutation = useMutation({
    mutationFn: (impeditivoId: string) => api.delete(`/frequencias/impeditivos/${impeditivoId}`),
    onSuccess: () => {
      toast.success("Impeditivo removido.");
      queryClient.invalidateQueries({ queryKey: fichaQueryKey });
    },
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao remover o impeditivo.")),
  });

  function alternarPresenca(beneficiarioId: string, dataIso: string, statusAtual: StatusDia) {
    if (statusAtual === "IMPEDITIVO") return;
    marcarMutation.mutate({ beneficiarioId, data: dataIso, presente: statusAtual !== "PRESENTE" });
  }

  const [justificando, setJustificando] = useState<{ beneficiarioId: string; nome: string; data: string } | null>(null);
  const [textoJustificativa, setTextoJustificativa] = useState("");

  function abrirJustificar(beneficiarioId: string, nome: string, dataIso: string) {
    setJustificando({ beneficiarioId, nome, data: dataIso });
    setTextoJustificativa("");
  }

  function confirmarJustificativa() {
    if (!justificando || !textoJustificativa.trim()) return;
    marcarMutation.mutate(
      {
        beneficiarioId: justificando.beneficiarioId, data: justificando.data,
        presente: false, faltaJustificada: true, justificativa: textoJustificativa.trim(),
      },
      { onSuccess: () => setJustificando(null) }
    );
  }

  const [marcandoImpeditivoData, setMarcandoImpeditivoData] = useState<string | null>(null);
  const [textoImpeditivo, setTextoImpeditivo] = useState("Feriado, ponto facultativo ou data comemorativa");

  function confirmarImpeditivo() {
    if (!marcandoImpeditivoData || !textoImpeditivo.trim()) return;
    impeditivoMutation.mutate(
      { data: marcandoImpeditivoData, justificativa: textoImpeditivo.trim() },
      { onSuccess: () => setMarcandoImpeditivoData(null) }
    );
  }

  function impeditivoDeData(dataIso: string) {
    return ficha?.impeditivos.find((i) => i.data === dataIso) ?? null;
  }

  // --- Fotos da aula (por data específica — independente da grade do mês) ---
  const [dataEvidencia, setDataEvidencia] = useState(new Date().toISOString().slice(0, 10));
  const [enviandoFotos, setEnviandoFotos] = useState(false);
  const evidenciasQueryKey = ["frequencias", "evidencias", turmaId, dataEvidencia];
  const { data: evidencias = [] } = useQuery({
    queryKey: evidenciasQueryKey,
    queryFn: () =>
      api
        .get<ChamadaEvidencia[]>("/frequencias/evidencias", { params: { turma_id: turmaId, data: dataEvidencia } })
        .then((r) => r.data),
    enabled: !!turmaId && !!dataEvidencia,
  });

  async function enviarFotos(e: ChangeEvent<HTMLInputElement>) {
    const arquivos = e.target.files;
    if (!arquivos || arquivos.length === 0 || !turmaId) return;
    setEnviandoFotos(true);
    try {
      const formData = new FormData();
      formData.append("turma_id", turmaId);
      formData.append("data", dataEvidencia);
      Array.from(arquivos).forEach((arquivo) => formData.append("arquivos", arquivo));
      const resp = await api.post<ChamadaEvidencia[]>("/frequencias/evidencias", formData);
      queryClient.invalidateQueries({ queryKey: evidenciasQueryKey });
      toast.success(`${resp.data.length} foto(s) anexada(s) como comprovação da aula.`);
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao enviar as fotos."));
    } finally {
      setEnviandoFotos(false);
      e.target.value = "";
    }
  }

  // --- Exportar Lista de Presença (.xlsx oficial — independente da grade) ---
  const [mesExportacao, setMesExportacao] = useState(MES_ATUAL);
  const [anoExportacao, setAnoExportacao] = useState(ANO_ATUAL);
  const [exportando, setExportando] = useState(false);

  async function exportarListaPresenca() {
    if (!turmaId) return;
    setExportando(true);
    try {
      await baixarExportacao(
        `/turmas/${turmaId}/lista-presenca/exportar?mes=${mesExportacao}&ano=${anoExportacao}`,
        `Lista de Presenca - ${String(mesExportacao).padStart(2, "0")}-${anoExportacao}.xlsx`
      );
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao exportar a Lista de Presença."));
    } finally {
      setExportando(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="print:hidden">
        <PageHeader title="Frequência / Chamada" subtitle="Registro mensal de presença dos beneficiários, com impeditivo de aula e falta justificada." />
      </div>
      <Card title="Selecione turma, mês e ano" className="animate-fade-in-up print:hidden" style={staggerStyle(0)}>
        <div className="flex flex-col sm:flex-row gap-4 sm:items-end">
          <div className="flex-1">
            <Select label="Turma" value={turmaId} onChange={(e) => setTurmaId(e.target.value)}>
              <option value="">— Selecione —</option>
              {turmas.map((t) => <option key={t.id} value={t.id}>{t.horario_inicio}–{t.horario_fim} ({t.dias_semana.join(",")})</option>)}
            </Select>
          </div>
          <div className="sm:w-32">
            <Input label="Mês" type="number" min={1} max={12} value={mes} onChange={(e) => setMes(Number(e.target.value))} />
          </div>
          <div className="sm:w-32">
            <Input label="Ano" type="number" min={2000} max={2100} value={ano} onChange={(e) => setAno(Number(e.target.value))} />
          </div>
        </div>
      </Card>

      {turmaId && carregandoFicha && <Spinner label="Carregando ficha de chamada…" />}

      {turmaId && !carregandoFicha && ficha && (
        <Card
          title="Chamada do mês"
          subtitle={`${ficha.polo_nome} — ${ficha.modalidade_nome} — ${ficha.horario_inicio}–${ficha.horario_fim}${ficha.professor_nome ? ` — ${ficha.professor_nome}` : ""}`}
          actions={
            <div className="flex gap-2">
              <Button variant="secondary" onClick={baixarXlsxFichaChamada} disabled={exportandoXlsx}>
                {exportandoXlsx ? "Gerando…" : "Baixar Excel"}
              </Button>
              <Button variant="secondary" onClick={baixarPdfFichaChamada} disabled={exportandoPdf}>
                {exportandoPdf ? "Gerando…" : "Baixar PDF da ficha de chamada"}
              </Button>
            </div>
          }
          className="animate-fade-in-up"
          style={staggerStyle(1)}
        >
          {ficha.linhas.length === 0 ? (
            <EmptyState message="Nenhum beneficiário matriculado ativo nesta turma." />
          ) : ficha.datas.length === 0 ? (
            <EmptyState message="A turma não tem nenhuma aula prevista neste mês." />
          ) : (
            <>
              <p className="text-xs text-gray-400 mb-3">
                Clique numa célula para alternar presença/falta. Clique no cabeçalho de uma data para marcar ou
                remover um impeditivo de aula (feriado etc., vale para a turma inteira).
              </p>
              <div className="overflow-x-auto -mx-6">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                      <th className="py-2.5 px-6 sticky left-0 bg-brand-light">Beneficiário</th>
                      {ficha.datas.map((d) => {
                        const imp = impeditivoDeData(d);
                        return (
                          <th key={d} className="px-2 text-center">
                            <button
                              type="button"
                              title={imp ? `Impeditivo: ${imp.justificativa} — clique para remover` : "Marcar impeditivo de aula"}
                              onClick={() =>
                                imp
                                  ? removerImpeditivoMutation.mutate(imp.id)
                                  : (setMarcandoImpeditivoData(d), setTextoImpeditivo("Feriado, ponto facultativo ou data comemorativa"))
                              }
                              className={`px-1.5 py-1 rounded transition-colors ${imp ? "text-amber-600 bg-amber-50" : "hover:bg-gray-200"}`}
                            >
                              {diaCurto(d)}
                            </button>
                          </th>
                        );
                      })}
                      <th className="px-3 text-right pr-6">Freq.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ficha.linhas.map((linha) => (
                      <tr key={linha.beneficiario_id} className="border-t border-gray-100">
                        <td className="py-2 px-6 font-medium text-gray-800 sticky left-0 bg-white whitespace-nowrap">
                          {linha.nome}
                          {linha.idade !== null && <span className="text-gray-400 font-normal"> ({linha.idade})</span>}
                        </td>
                        {ficha.datas.map((d) => {
                          const status = linha.status_por_data[d];
                          const estilo = STATUS_ESTILO[status];
                          return (
                            <td key={d} className="px-2 text-center">
                              <div className="flex items-center justify-center gap-0.5">
                                <button
                                  type="button"
                                  title={estilo.titulo}
                                  onClick={() => alternarPresenca(linha.beneficiario_id, d, status)}
                                  disabled={status === "IMPEDITIVO"}
                                  className={`${estilo.className} disabled:cursor-default hover:opacity-70 transition-opacity`}
                                >
                                  {estilo.icon}
                                </button>
                                {(status === "FALTA" || status === "FALTA_JUSTIFICADA") && (
                                  <button
                                    type="button"
                                    title="Justificar falta"
                                    onClick={() => abrirJustificar(linha.beneficiario_id, linha.nome, d)}
                                    className="text-[10px] text-gray-400 hover:text-brand underline"
                                  >
                                    J
                                  </button>
                                )}
                              </div>
                            </td>
                          );
                        })}
                        <td className="px-3 text-right pr-6 font-medium text-gray-700">{linha.frequencia_pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {ficha.impeditivos.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">Impeditivos de aula do mês</h3>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {ficha.impeditivos.map((i) => (
                      <li key={i.id} className="flex items-center justify-between gap-3">
                        <span>{diaCurto(i.data)}/{ficha.mes.toString().padStart(2, "0")} — {i.justificativa}</span>
                        <button
                          type="button"
                          onClick={() => removerImpeditivoMutation.mutate(i.id)}
                          className="text-xs text-gray-400 hover:text-red-600"
                        >
                          remover
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="mt-6 pt-4 border-t border-gray-100 flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-500">
                <span className="flex items-center gap-1"><CheckCircleIcon className="w-4 h-4 text-accent-dark" /> Presença: {ficha.resumo.presenca}</span>
                <span className="flex items-center gap-1"><CloseIcon className="w-4 h-4 text-red-500" /> Falta: {ficha.resumo.falta}</span>
                <span className="flex items-center gap-1"><AlertCircleIcon className="w-4 h-4 text-blue-500" /> Falta justificada: {ficha.resumo.falta_justificada}</span>
                <span className="flex items-center gap-1"><CalendarOffIcon className="w-4 h-4 text-amber-500" /> Impeditivo: {ficha.resumo.impeditivo}</span>
                <span className="flex items-center gap-1 text-gray-300">— Sem marcação: {ficha.resumo.sem_marcacao}</span>
              </div>
            </>
          )}
        </Card>
      )}

      {turmaId && !carregandoFicha && ficha && ficha.linhas.length > 0 && ficha.datas.length > 0 && (
        <div ref={fichaImpressaoRef}>
          <FichaChamadaImpressao ficha={ficha} />
        </div>
      )}

      {turmaId && (
        <Card
          title="Fotos da aula"
          subtitle="Anexe uma ou mais fotos comprovando que a aula de uma data específica realmente aconteceu."
          className="animate-fade-in-up print:hidden"
          style={staggerStyle(2)}
        >
          <div className="sm:w-48 mb-4">
            <Input label="Data" type="date" value={dataEvidencia} onChange={(e) => setDataEvidencia(e.target.value)} />
          </div>
          <div className="flex flex-wrap gap-3 items-center">
            {evidencias.map((ev) => <EvidenciaThumb key={ev.id} evidencia={ev} />)}
            <label className="w-20 h-20 rounded-lg border-2 border-dashed border-gray-300 flex flex-col items-center justify-center gap-1 text-gray-400 cursor-pointer hover:border-brand hover:text-brand transition-colors shrink-0">
              <CameraIcon className="w-6 h-6" />
              <span className="text-[10px] font-medium">{enviandoFotos ? "Enviando…" : "Adicionar"}</span>
              <input type="file" accept="image/*" multiple className="hidden" disabled={enviandoFotos} onChange={enviarFotos} />
            </label>
          </div>
        </Card>
      )}

      {turmaId && (
        <Card title="Exportar Lista de Presença" subtitle="Gera o arquivo .xlsx do mês, no layout oficial, com a frequência já lançada." className="animate-fade-in-up print:hidden" style={staggerStyle(3)}>
          <div className="flex flex-col sm:flex-row gap-4 sm:items-end">
            <div className="sm:w-32">
              <Input label="Mês" type="number" min={1} max={12} value={mesExportacao} onChange={(e) => setMesExportacao(Number(e.target.value))} />
            </div>
            <div className="sm:w-32">
              <Input label="Ano" type="number" min={2000} max={2100} value={anoExportacao} onChange={(e) => setAnoExportacao(Number(e.target.value))} />
            </div>
            <Button variant="secondary" onClick={exportarListaPresenca} disabled={exportando}>
              {exportando ? "Exportando…" : "Exportar .xlsx"}
            </Button>
          </div>
        </Card>
      )}

      <Modal open={!!justificando} onClose={() => setJustificando(null)} title={justificando ? `Justificar falta — ${justificando.nome}` : ""}>
        {justificando && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500">Data: {diaCurto(justificando.data)}/{justificando.data.slice(5, 7)}/{justificando.data.slice(0, 4)}</p>
            <label className="block">
              <span className="block text-sm font-medium text-gray-700 mb-1">Justificativa</span>
              <textarea
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand/40 focus:border-brand outline-none transition"
                rows={3}
                value={textoJustificativa}
                onChange={(e) => setTextoJustificativa(e.target.value)}
                autoFocus
              />
            </label>
            <div className="flex gap-3">
              <Button onClick={confirmarJustificativa} disabled={!textoJustificativa.trim() || marcarMutation.isPending}>
                {marcarMutation.isPending ? "Salvando…" : "Confirmar"}
              </Button>
              <Button type="button" variant="secondary" onClick={() => setJustificando(null)}>Cancelar</Button>
            </div>
          </div>
        )}
      </Modal>

      <Modal open={!!marcandoImpeditivoData} onClose={() => setMarcandoImpeditivoData(null)} title="Marcar impeditivo de aula">
        {marcandoImpeditivoData && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500">
              Data: {diaCurto(marcandoImpeditivoData)}/{marcandoImpeditivoData.slice(5, 7)}/{marcandoImpeditivoData.slice(0, 4)} —
              vale para todos os beneficiários da turma nessa data.
            </p>
            <label className="block">
              <span className="block text-sm font-medium text-gray-700 mb-1">Justificativa</span>
              <textarea
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand/40 focus:border-brand outline-none transition"
                rows={3}
                value={textoImpeditivo}
                onChange={(e) => setTextoImpeditivo(e.target.value)}
                autoFocus
              />
            </label>
            <div className="flex gap-3">
              <Button onClick={confirmarImpeditivo} disabled={!textoImpeditivo.trim() || impeditivoMutation.isPending}>
                {impeditivoMutation.isPending ? "Salvando…" : "Confirmar"}
              </Button>
              <Button type="button" variant="secondary" onClick={() => setMarcandoImpeditivoData(null)}>Cancelar</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
