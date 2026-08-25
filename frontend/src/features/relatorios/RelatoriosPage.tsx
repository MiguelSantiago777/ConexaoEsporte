import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { RelatorioAula, Turma } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { PageHeader } from "@/components/ui/PageHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";

export function RelatoriosPage() {
  const toast = useToast();
  const [turmas, setTurmas] = useState<Turma[]>([]);
  const [relatorios, setRelatorios] = useState<RelatorioAula[]>([]);
  const [salvando, setSalvando] = useState(false);
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
    setSalvando(true);
    try {
      await api.post("/relatorios-aula", { ...form, observacoes: form.observacoes || null });
      setForm({ ...form, conteudo_trabalhado: "", observacoes: "" });
      toast.success("Relatório emitido com sucesso.");
      carregarRelatorios(form.turma_id);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao emitir relatório.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Relatórios de Aula" subtitle="Registro do conteúdo trabalhado em cada aula." />
      <Card title="Emitir relatório" className="animate-fade-in-up" style={staggerStyle(0)}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select label="Turma" value={form.turma_id}
              onChange={(e) => { setForm({ ...form, turma_id: e.target.value }); carregarRelatorios(e.target.value); }} required>
              <option value="">— Selecione —</option>
              {turmas.map((t) => <option key={t.id} value={t.id}>{t.horario_inicio}–{t.horario_fim}</option>)}
            </Select>
            <Input label="Data" type="date" value={form.data} onChange={(e) => setForm({ ...form, data: e.target.value })} required />
          </div>
          <label className="block">
            <span className="block text-sm font-medium text-gray-700 mb-1">Conteúdo trabalhado</span>
            <textarea className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand/40 focus:border-brand outline-none transition" rows={3}
              value={form.conteudo_trabalhado} onChange={(e) => setForm({ ...form, conteudo_trabalhado: e.target.value })} required />
          </label>
          <label className="block">
            <span className="block text-sm font-medium text-gray-700 mb-1">Observações</span>
            <textarea className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand/40 focus:border-brand outline-none transition" rows={2}
              value={form.observacoes} onChange={(e) => setForm({ ...form, observacoes: e.target.value })} />
          </label>
          <Button type="submit" disabled={salvando}>{salvando ? "Emitindo…" : "Emitir relatório"}</Button>
        </form>
      </Card>
      {form.turma_id && (
        <Card title="Relatórios da turma" className="animate-fade-in-up" style={staggerStyle(1)}>
          {relatorios.length === 0 ? (
            <EmptyState message="Nenhum relatório emitido para esta turma ainda." />
          ) : (
            <ul className="divide-y divide-gray-100">
              {relatorios.map((r) => (
                <li key={r.id} className="py-3">
                  <div className="text-xs text-gray-400">{r.data}</div>
                  <div className="font-medium text-gray-800">{r.conteudo_trabalhado}</div>
                  {r.observacoes && <div className="text-sm text-gray-600 mt-0.5">{r.observacoes}</div>}
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}
    </div>
  );
}
