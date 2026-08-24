import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { RelatorioAula, Turma } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export function RelatoriosPage() {
  const [turmas, setTurmas] = useState<Turma[]>([]);
  const [relatorios, setRelatorios] = useState<RelatorioAula[]>([]);
  const [form, setForm] = useState({
    turma_id: "", data: new Date().toISOString().slice(0, 10),
    conteudo_trabalhado: "", observacoes: "",
  });

  useEffect(() => {
    api.get<Turma[]>("/turmas").then((r) => setTurmas(r.data));
  }, []);

  async function carregarRelatorios(turmaId: string) {
    if (!turmaId) return setRelatorios([]);
    const { data } = await api.get<RelatorioAula[]>(`/relatorios-aula/turma/${turmaId}`);
    setRelatorios(data);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await api.post("/relatorios-aula", { ...form, observacoes: form.observacoes || null });
    setForm({ ...form, conteudo_trabalhado: "", observacoes: "" });
    carregarRelatorios(form.turma_id);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Relatórios de Aula</h1>
      <Card title="Emitir relatório">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <label className="block">
              <span className="block text-sm font-medium text-gray-700 mb-1">Turma</span>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md" value={form.turma_id}
                onChange={(e) => { setForm({ ...form, turma_id: e.target.value }); carregarRelatorios(e.target.value); }} required>
                <option value="">— Selecione —</option>
                {turmas.map((t) => <option key={t.id} value={t.id}>{t.horario_inicio}–{t.horario_fim}</option>)}
              </select>
            </label>
            <Input label="Data" type="date" value={form.data} onChange={(e) => setForm({ ...form, data: e.target.value })} required />
          </div>
          <label className="block">
            <span className="block text-sm font-medium text-gray-700 mb-1">Conteúdo trabalhado</span>
            <textarea className="w-full px-3 py-2 border border-gray-300 rounded-md" rows={3}
              value={form.conteudo_trabalhado} onChange={(e) => setForm({ ...form, conteudo_trabalhado: e.target.value })} required />
          </label>
          <label className="block">
            <span className="block text-sm font-medium text-gray-700 mb-1">Observações</span>
            <textarea className="w-full px-3 py-2 border border-gray-300 rounded-md" rows={2}
              value={form.observacoes} onChange={(e) => setForm({ ...form, observacoes: e.target.value })} />
          </label>
          <Button type="submit">Emitir relatório</Button>
        </form>
      </Card>
      {relatorios.length > 0 && (
        <Card title="Relatórios da turma">
          <ul className="divide-y">
            {relatorios.map((r) => (
              <li key={r.id} className="py-3">
                <div className="text-sm text-gray-500">{r.data}</div>
                <div className="font-medium">{r.conteudo_trabalhado}</div>
                {r.observacoes && <div className="text-sm text-gray-600">{r.observacoes}</div>}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
