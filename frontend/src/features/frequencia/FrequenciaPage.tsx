import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Beneficiario, Turma } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

/**
 * Chamada/frequência diária — funcionalidade principal do perfil PROFESSOR.
 */
export function FrequenciaPage() {
  const [turmas, setTurmas] = useState<Turma[]>([]);
  const [turmaId, setTurmaId] = useState("");
  const [data, setData] = useState(new Date().toISOString().slice(0, 10));
  const [beneficiarios, setBeneficiarios] = useState<Beneficiario[]>([]);
  const [presencas, setPresencas] = useState<Record<string, boolean>>({});
  const [salvo, setSalvo] = useState(false);

  useEffect(() => {
    api.get<Turma[]>("/turmas").then((r) => setTurmas(r.data));
  }, []);

  async function carregarBeneficiarios(id: string) {
    setTurmaId(id);
    setSalvo(false);
    if (!id) return;
    const { data: benef } = await api.get<Beneficiario[]>("/beneficiarios", { params: { turma_id: id } });
    setBeneficiarios(benef);
    setPresencas(Object.fromEntries(benef.map((b) => [b.id, true])));
  }

  async function salvarChamada() {
    await api.post("/frequencias/chamada", {
      turma_id: turmaId,
      data,
      presencas: beneficiarios.map((b) => ({ beneficiario_id: b.id, presente: presencas[b.id] ?? false })),
    });
    setSalvo(true);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Frequência / Chamada</h1>
      <Card title="Selecione turma e data">
        <div className="flex gap-4 items-end">
          <label className="block flex-1">
            <span className="block text-sm font-medium text-gray-700 mb-1">Turma</span>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-md" value={turmaId}
              onChange={(e) => carregarBeneficiarios(e.target.value)}>
              <option value="">— Selecione —</option>
              {turmas.map((t) => <option key={t.id} value={t.id}>{t.horario_inicio}–{t.horario_fim} ({t.dias_semana.join(",")})</option>)}
            </select>
          </label>
          <label className="block">
            <span className="block text-sm font-medium text-gray-700 mb-1">Data</span>
            <input type="date" className="px-3 py-2 border border-gray-300 rounded-md" value={data} onChange={(e) => setData(e.target.value)} />
          </label>
        </div>
      </Card>

      {beneficiarios.length > 0 && (
        <Card title={`Chamada — ${beneficiarios.length} beneficiários`}>
          {salvo && <div className="bg-green-50 text-green-700 text-sm p-2 rounded mb-4">Chamada salva com sucesso!</div>}
          <ul className="divide-y">
            {beneficiarios.map((b) => (
              <li key={b.id} className="py-3 flex items-center justify-between">
                <span className="font-medium">{b.nome_completo}</span>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="w-5 h-5 accent-brand"
                    checked={presencas[b.id] ?? false}
                    onChange={(e) => setPresencas({ ...presencas, [b.id]: e.target.checked })} />
                  <span className="text-sm">{presencas[b.id] ? "Presente" : "Ausente"}</span>
                </label>
              </li>
            ))}
          </ul>
          <div className="mt-4"><Button onClick={salvarChamada}>Salvar chamada</Button></div>
        </Card>
      )}
    </div>
  );
}
