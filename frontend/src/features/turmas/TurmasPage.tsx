import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Modalidade, Polo, Turma } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/features/auth/AuthContext";

const DIAS = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"];

export function TurmasPage() {
  const { usuario } = useAuth();
  const [turmas, setTurmas] = useState<Turma[]>([]);
  const [polos, setPolos] = useState<Polo[]>([]);
  const [modalidades, setModalidades] = useState<Modalidade[]>([]);
  const [erro, setErro] = useState<string | null>(null);
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
  useEffect(() => { carregar(); }, []);

  function toggleDia(dia: string) {
    setForm((f) => ({
      ...f,
      dias_semana: f.dias_semana.includes(dia)
        ? f.dias_semana.filter((d) => d !== dia)
        : [...f.dias_semana, dia],
    }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    try {
      await api.post("/turmas", { ...form, limite_vagas: Number(form.limite_vagas) });
      setForm({ polo_id: usuario?.polo_id ?? "", modalidade_id: "", horario_inicio: "", horario_fim: "", dias_semana: [], limite_vagas: 20 });
      carregar();
    } catch (err: any) {
      setErro(err?.response?.data?.detail ?? "Erro ao cadastrar turma.");
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Turmas</h1>
      <Card title="Cadastrar turma">
        {erro && <div className="bg-red-50 text-red-700 text-sm p-2 rounded mb-4">{erro}</div>}
        <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
          <label className="block">
            <span className="block text-sm font-medium text-gray-700 mb-1">Polo</span>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-md" value={form.polo_id}
              onChange={(e) => setForm({ ...form, polo_id: e.target.value })}
              disabled={usuario?.perfil === "GESTOR_POLO"} required>
              <option value="">— Selecione —</option>
              {polos.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
            </select>
          </label>
          <label className="block">
            <span className="block text-sm font-medium text-gray-700 mb-1">Modalidade</span>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-md" value={form.modalidade_id}
              onChange={(e) => setForm({ ...form, modalidade_id: e.target.value })} required>
              <option value="">— Selecione —</option>
              {modalidades.map((m) => <option key={m.id} value={m.id}>{m.nome}</option>)}
            </select>
          </label>
          <Input label="Horário início" type="time" value={form.horario_inicio}
            onChange={(e) => setForm({ ...form, horario_inicio: e.target.value })} required />
          <Input label="Horário fim" type="time" value={form.horario_fim}
            onChange={(e) => setForm({ ...form, horario_fim: e.target.value })} required />
          <div className="col-span-2">
            <span className="block text-sm font-medium text-gray-700 mb-1">Dias da semana</span>
            <div className="flex gap-2">
              {DIAS.map((d) => (
                <button type="button" key={d} onClick={() => toggleDia(d)}
                  className={`px-3 py-1 rounded text-sm border ${form.dias_semana.includes(d) ? "bg-brand text-white border-brand" : "bg-white border-gray-300"}`}>
                  {d}
                </button>
              ))}
            </div>
          </div>
          <Input label="Limite de vagas" type="number" min={1} value={form.limite_vagas}
            onChange={(e) => setForm({ ...form, limite_vagas: Number(e.target.value) })} required />
          <div className="col-span-2"><Button type="submit">Cadastrar turma</Button></div>
        </form>
      </Card>
      <Card title={`Turmas (${turmas.length})`}>
        <table className="w-full text-sm">
          <thead><tr className="text-left text-gray-500 border-b">
            <th className="py-2">Horário</th><th>Dias</th><th>Vagas</th><th>Professor</th></tr></thead>
          <tbody>
            {turmas.map((t) => (
              <tr key={t.id} className="border-b last:border-0">
                <td className="py-2">{t.horario_inicio}–{t.horario_fim}</td>
                <td>{t.dias_semana.join(", ")}</td>
                <td>{t.vagas_ocupadas}/{t.limite_vagas}</td>
                <td>{t.professor_id ? t.professor_id.slice(0, 8) : <span className="text-gray-400">sem professor</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
