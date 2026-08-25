import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Modalidade, Polo, Turma } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { useAuth } from "@/features/auth/AuthContext";

const DIAS = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"];

export function TurmasPage() {
  const { usuario } = useAuth();
  const toast = useToast();
  const [turmas, setTurmas] = useState<Turma[]>([]);
  const [polos, setPolos] = useState<Polo[]>([]);
  const [modalidades, setModalidades] = useState<Modalidade[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [form, setForm] = useState({
    polo_id: "", modalidade_id: "", horario_inicio: "", horario_fim: "",
    dias_semana: [] as string[], limite_vagas: 20,
  });

  async function carregar() {
    const [t, p, m] = await Promise.all([
      api.get<Turma[]>("/turmas"),
      api.get<Polo[]>("/polos"),
      api.get<Modalidade[]>("/modalidades"),
    ]);
    setTurmas(t.data);
    setPolos(p.data);
    setModalidades(m.data);
    // Gestor de polo já vem com o polo pré-selecionado
    if (usuario?.polo_id && !form.polo_id) {
      setForm((f) => ({ ...f, polo_id: usuario.polo_id! }));
    }
  }
  useEffect(() => {
    carregar().finally(() => setCarregando(false));
  }, []);

  function toggleDia(dia: string) {
    setForm((f) => ({
      ...f,
      dias_semana: f.dias_semana.includes(dia)
        ? f.dias_semana.filter((d) => d !== dia)
        : [...f.dias_semana, dia],
    }));
  }

  function poloNome(id: string) {
    return polos.find((p) => p.id === id)?.nome ?? "—";
  }
  function modalidadeNome(id: string) {
    return modalidades.find((m) => m.id === id)?.nome ?? "—";
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
      await api.post("/turmas", { ...form, limite_vagas: Number(form.limite_vagas) });
      setForm({ polo_id: usuario?.polo_id ?? "", modalidade_id: "", horario_inicio: "", horario_fim: "", dias_semana: [], limite_vagas: 20 });
      toast.success("Turma cadastrada com sucesso.");
      carregar();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao cadastrar turma.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Turmas" subtitle="Turmas de cada modalidade oferecidas por polo." />
      <Card title="Cadastrar turma" className="animate-fade-in-up" style={staggerStyle(0)}>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="Polo"
            value={form.polo_id}
            onChange={(e) => setForm({ ...form, polo_id: e.target.value })}
            disabled={usuario?.perfil === "GESTOR_POLO"}
            required
          >
            <option value="">— Selecione —</option>
            {polos.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
          </Select>
          <Select
            label="Modalidade"
            value={form.modalidade_id}
            onChange={(e) => setForm({ ...form, modalidade_id: e.target.value })}
            required
          >
            <option value="">— Selecione —</option>
            {modalidades.map((m) => <option key={m.id} value={m.id}>{m.nome}</option>)}
          </Select>
          <Input label="Horário início" type="time" value={form.horario_inicio}
            onChange={(e) => setForm({ ...form, horario_inicio: e.target.value })} required />
          <Input label="Horário fim" type="time" value={form.horario_fim}
            onChange={(e) => setForm({ ...form, horario_fim: e.target.value })} required />
          <div className="sm:col-span-2">
            <span className="block text-sm font-medium text-gray-700 mb-1">Dias da semana</span>
            <div className="flex flex-wrap gap-2">
              {DIAS.map((d) => (
                <button type="button" key={d} onClick={() => toggleDia(d)}
                  className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors ${form.dias_semana.includes(d) ? "bg-accent text-brand-dark border-accent" : "bg-white border-gray-300 text-gray-600 hover:bg-gray-50"}`}>
                  {d}
                </button>
              ))}
            </div>
          </div>
          <Input label="Limite de vagas" type="number" min={1} value={form.limite_vagas}
            onChange={(e) => setForm({ ...form, limite_vagas: Number(e.target.value) })} required />
          <div className="sm:col-span-2">
            <Button type="submit" disabled={salvando}>{salvando ? "Cadastrando…" : "Cadastrar turma"}</Button>
          </div>
        </form>
      </Card>
      <Card
        title="Turmas"
        actions={<Badge variant="accent">{turmas.length}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(1)}
      >
        {carregando ? (
          <Spinner label="Carregando turmas…" />
        ) : turmas.length === 0 ? (
          <EmptyState message="Nenhuma turma cadastrada ainda." />
        ) : (
          <div className="overflow-x-auto -mx-6">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                  <th className="py-2.5 px-6">Polo</th>
                  <th className="px-3">Modalidade</th>
                  <th className="px-3">Horário</th>
                  <th className="px-3">Dias</th>
                  <th className="px-3">Vagas</th>
                  <th className="px-3">Professor</th>
                </tr>
              </thead>
              <tbody>
                {turmas.map((t) => (
                  <tr key={t.id} className="border-t border-gray-100 hover:bg-brand-light/60 transition-colors">
                    <td className="py-2.5 px-6 font-medium text-gray-800">{poloNome(t.polo_id)}</td>
                    <td className="px-3 text-gray-600">{modalidadeNome(t.modalidade_id)}</td>
                    <td className="px-3 text-gray-600">{t.horario_inicio}–{t.horario_fim}</td>
                    <td className="px-3 text-gray-600">{t.dias_semana.join(", ")}</td>
                    <td className="px-3"><Badge variant="accent">{t.vagas_ocupadas}/{t.limite_vagas}</Badge></td>
                    <td className="px-3">{t.professor_id ? t.professor_id.slice(0, 8) : <span className="text-gray-400">sem professor</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
