import { ChangeEvent, useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Beneficiario, ChamadaEvidencia, Turma } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { PageHeader } from "@/components/ui/PageHeader";
import { CameraIcon } from "@/components/ui/icons";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { baixarExportacao } from "@/features/fichas-execucao/FichasExecucaoPage";

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
 * Chamada/frequência diária — funcionalidade principal do perfil PROFESSOR.
 */
export function FrequenciaPage() {
  const toast = useToast();
  const queryClient = useQueryClient();

  const { data: turmas = [] } = useQuery({
    queryKey: ["turmas"],
    queryFn: () => api.get<Turma[]>("/turmas").then((r) => r.data),
  });

  const [turmaId, setTurmaId] = useState("");
  const [data, setData] = useState(new Date().toISOString().slice(0, 10));
  const [presencas, setPresencas] = useState<Record<string, boolean>>({});
  const [salvando, setSalvando] = useState(false);
  const [mesExportacao, setMesExportacao] = useState(MES_ATUAL);
  const [anoExportacao, setAnoExportacao] = useState(ANO_ATUAL);
  const [exportando, setExportando] = useState(false);
  const [enviandoFotos, setEnviandoFotos] = useState(false);

  const beneficiariosQuery = useQuery({
    queryKey: ["beneficiarios", "por-turma", turmaId],
    queryFn: () => api.get<Beneficiario[]>("/beneficiarios", { params: { turma_id: turmaId } }).then((r) => r.data),
    enabled: !!turmaId,
  });
  const beneficiarios = beneficiariosQuery.data ?? [];

  // Reinicializa a chamada (todos presentes) só quando os beneficiários da
  // turma recém-selecionada terminam de carregar pela primeira vez — não a
  // cada refetch em segundo plano dos mesmos beneficiários, que apagaria
  // marcações que o usuário já tenha feito na tela.
  const presencasInicializadasPara = useRef<string | null>(null);
  useEffect(() => {
    if (turmaId && beneficiariosQuery.data && presencasInicializadasPara.current !== turmaId) {
      setPresencas(Object.fromEntries(beneficiariosQuery.data.map((b) => [b.id, true])));
      presencasInicializadasPara.current = turmaId;
    }
  }, [turmaId, beneficiariosQuery.data]);

  const evidenciasQueryKey = ["frequencias", "evidencias", turmaId, data];
  const { data: evidencias = [] } = useQuery({
    queryKey: evidenciasQueryKey,
    queryFn: () =>
      api
        .get<ChamadaEvidencia[]>("/frequencias/evidencias", { params: { turma_id: turmaId, data } })
        .then((r) => r.data),
    enabled: !!turmaId && !!data,
  });

  async function salvarChamada() {
    setSalvando(true);
    try {
      await api.post("/frequencias/chamada", {
        turma_id: turmaId,
        data,
        presencas: beneficiarios.map((b) => ({ beneficiario_id: b.id, presente: presencas[b.id] ?? false })),
      });
      toast.success("Chamada salva com sucesso.");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao salvar a chamada.");
    } finally {
      setSalvando(false);
    }
  }

  async function enviarFotos(e: ChangeEvent<HTMLInputElement>) {
    const arquivos = e.target.files;
    if (!arquivos || arquivos.length === 0 || !turmaId) return;
    setEnviandoFotos(true);
    try {
      const formData = new FormData();
      formData.append("turma_id", turmaId);
      formData.append("data", data);
      Array.from(arquivos).forEach((arquivo) => formData.append("arquivos", arquivo));
      const resp = await api.post<ChamadaEvidencia[]>("/frequencias/evidencias", formData);
      queryClient.invalidateQueries({ queryKey: evidenciasQueryKey });
      toast.success(`${resp.data.length} foto(s) anexada(s) como comprovação da aula.`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao enviar as fotos.");
    } finally {
      setEnviandoFotos(false);
      e.target.value = "";
    }
  }

  async function exportarListaPresenca() {
    if (!turmaId) return;
    setExportando(true);
    try {
      await baixarExportacao(
        `/turmas/${turmaId}/lista-presenca/exportar?mes=${mesExportacao}&ano=${anoExportacao}`,
        `Lista de Presenca - ${String(mesExportacao).padStart(2, "0")}-${anoExportacao}.xlsx`
      );
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao exportar a Lista de Presença.");
    } finally {
      setExportando(false);
    }
  }

  const presentes = beneficiarios.filter((b) => presencas[b.id]).length;

  return (
    <div className="space-y-6">
      <PageHeader title="Frequência / Chamada" subtitle="Registro diário de presença dos beneficiários." />
      <Card title="Selecione turma e data" className="animate-fade-in-up" style={staggerStyle(0)}>
        <div className="flex flex-col sm:flex-row gap-4 sm:items-end">
          <div className="flex-1">
            <Select label="Turma" value={turmaId} onChange={(e) => setTurmaId(e.target.value)}>
              <option value="">— Selecione —</option>
              {turmas.map((t) => <option key={t.id} value={t.id}>{t.horario_inicio}–{t.horario_fim} ({t.dias_semana.join(",")})</option>)}
            </Select>
          </div>
          <div className="sm:w-48">
            <Input label="Data" type="date" value={data} onChange={(e) => setData(e.target.value)} />
          </div>
        </div>
      </Card>

      {turmaId && (
        <Card
          title="Fotos da aula"
          subtitle="Anexe uma ou mais fotos comprovando que a aula desta data realmente aconteceu."
          className="animate-fade-in-up"
          style={staggerStyle(1)}
        >
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
        <Card title="Exportar Lista de Presença" subtitle="Gera o arquivo .xlsx do mês, no layout oficial, com a frequência já lançada." className="animate-fade-in-up" style={staggerStyle(2)}>
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

      {beneficiarios.length > 0 && (
        <Card
          title="Chamada"
          subtitle={`${presentes} de ${beneficiarios.length} presentes`}
          className="animate-fade-in-up"
          style={staggerStyle(3)}
        >
          <ul className="divide-y divide-gray-100">
            {beneficiarios.map((b) => (
              <li key={b.id} className="py-3 flex items-center justify-between">
                <span className="font-medium text-gray-800">{b.nome_completo}</span>
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input type="checkbox" className="w-5 h-5 accent-[#fcba27] rounded"
                    checked={presencas[b.id] ?? false}
                    onChange={(e) => setPresencas({ ...presencas, [b.id]: e.target.checked })} />
                  <span className={`text-sm font-medium ${presencas[b.id] ? "text-accent-dark" : "text-gray-400"}`}>
                    {presencas[b.id] ? "Presente" : "Ausente"}
                  </span>
                </label>
              </li>
            ))}
          </ul>
          <div className="mt-4">
            <Button onClick={salvarChamada} disabled={salvando}>{salvando ? "Salvando…" : "Salvar chamada"}</Button>
          </div>
        </Card>
      )}
    </div>
  );
}
