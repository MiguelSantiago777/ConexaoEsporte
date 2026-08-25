import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Beneficiario, Turma } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { PageHeader } from "@/components/ui/PageHeader";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";

/**
 * Chamada/frequência diária — funcionalidade principal do perfil PROFESSOR.
 */
export function FrequenciaPage() {
  const toast = useToast();
  const [turmas, setTurmas] = useState<Turma[]>([]);
  const [turmaId, setTurmaId] = useState("");
  const [data, setData] = useState(new Date().toISOString().slice(0, 10));
  const [beneficiarios, setBeneficiarios] = useState<Beneficiario[]>([]);
  const [presencas, setPresencas] = useState<Record<string, boolean>>({});
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    api.get<Turma[]>("/turmas").then((r) => setTurmas(r.data));
  }, []);

  async function carregarBeneficiarios(id: string) {
    setTurmaId(id);
    if (!id) return;
    const { data: benef } = await api.get<Beneficiario[]>("/beneficiarios", { params: { turma_id: id } });
    setBeneficiarios(benef);
    setPresencas(Object.fromEntries(benef.map((b) => [b.id, true])));
  }

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

  const presentes = beneficiarios.filter((b) => presencas[b.id]).length;

  return (
    <div className="space-y-6">
      <PageHeader title="Frequência / Chamada" subtitle="Registro diário de presença dos beneficiários." />
      <Card title="Selecione turma e data" className="animate-fade-in-up" style={staggerStyle(0)}>
        <div className="flex flex-col sm:flex-row gap-4 sm:items-end">
          <div className="flex-1">
            <Select label="Turma" value={turmaId} onChange={(e) => carregarBeneficiarios(e.target.value)}>
              <option value="">— Selecione —</option>
              {turmas.map((t) => <option key={t.id} value={t.id}>{t.horario_inicio}–{t.horario_fim} ({t.dias_semana.join(",")})</option>)}
            </Select>
          </div>
          <div className="sm:w-48">
            <Input label="Data" type="date" value={data} onChange={(e) => setData(e.target.value)} />
          </div>
        </div>
      </Card>

      {beneficiarios.length > 0 && (
        <Card
          title="Chamada"
          subtitle={`${presentes} de ${beneficiarios.length} presentes`}
          className="animate-fade-in-up"
          style={staggerStyle(1)}
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
