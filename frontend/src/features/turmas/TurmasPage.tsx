import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Modalidade, Polo, Turma, Usuario } from "@/types";
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
import { baixarExportacao } from "@/features/fichas-execucao/FichasExecucaoPage";

const DIAS = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"];
const MES_ATUAL = new Date().getMonth() + 1;
const ANO_ATUAL = new Date().getFullYear();

export function TurmasPage() {
  const { usuario } = useAuth();
  const toast = useToast();
  const queryClient = useQueryClient();

  const { data: turmas = [], isLoading: carregando } = useQuery({
    queryKey: ["turmas"],
    queryFn: () => api.get<Turma[]>("/turmas").then((r) => r.data),
  });
  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
  });
  const { data: modalidades = [] } = useQuery({
    queryKey: ["modalidades"],
    queryFn: () => api.get<Modalidade[]>("/modalidades").then((r) => r.data),
  });
  const { data: usuarios = [] } = useQuery({
    queryKey: ["usuarios"],
    queryFn: () => api.get<Usuario[]>("/usuarios").then((r) => r.data),
  });
  const professores = usuarios.filter((x) => x.perfil === "PROFESSOR");

  const [salvando, setSalvando] = useState(false);
  const [exportando, setExportando] = useState(false);
  const [form, setForm] = useState({
    polo_id: "", modalidade_id: "", horario_inicio: "", horario_fim: "",
    dias_semana: [] as string[], limite_vagas: 20,
    coordenador_nome: "", monitor_nome: "", periodicidade: "",
  });
  const [exportForm, setExportForm] = useState({ turma_id: "", mes: MES_ATUAL, ano: ANO_ATUAL });

  // Gestor de polo já vem com o polo pré-selecionado.
  useEffect(() => {
    if (usuario?.polo_id) {
      setForm((f) => (f.polo_id ? f : { ...f, polo_id: usuario.polo_id! }));
    }
  }, [usuario]);

  const atribuirProfessorMutation = useMutation({
    mutationFn: ({ turmaId, professorId }: { turmaId: string; professorId: string }) =>
      api.patch(`/turmas/${turmaId}`, { professor_id: professorId || null }),
    onSuccess: () => {
      toast.success("Professor atualizado.");
      queryClient.invalidateQueries({ queryKey: ["turmas"] });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Erro ao atualizar o professor da turma.");
    },
  });

  function atribuirProfessor(turmaId: string, professorId: string) {
    atribuirProfessorMutation.mutate({ turmaId, professorId });
  }

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
      await api.post("/turmas", {
        ...form,
        limite_vagas: Number(form.limite_vagas),
        coordenador_nome: form.coordenador_nome || null,
        monitor_nome: form.monitor_nome || null,
        periodicidade: form.periodicidade || null,
      });
      setForm({
        polo_id: usuario?.polo_id ?? "", modalidade_id: "", horario_inicio: "", horario_fim: "",
        dias_semana: [], limite_vagas: 20, coordenador_nome: "", monitor_nome: "", periodicidade: "",
      });
      toast.success("Turma cadastrada com sucesso.");
      queryClient.invalidateQueries({ queryKey: ["turmas"] });
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao cadastrar turma.");
    } finally {
      setSalvando(false);
    }
  }

  async function exportarListaPresenca(e: FormEvent) {
    e.preventDefault();
    if (!exportForm.turma_id) return;
    setExportando(true);
    try {
      await baixarExportacao(
        `/turmas/${exportForm.turma_id}/lista-presenca/exportar?mes=${exportForm.mes}&ano=${exportForm.ano}`,
        `Lista de Presenca - ${String(exportForm.mes).padStart(2, "0")}-${exportForm.ano}.xlsx`
      );
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao exportar a Lista de Presença.");
    } finally {
      setExportando(false);
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
          <Input label="Coordenador" placeholder="Nome do coordenador do núcleo" value={form.coordenador_nome}
            onChange={(e) => setForm({ ...form, coordenador_nome: e.target.value })} />
          <Input label="Monitor" placeholder="Nome do monitor/instrutor" value={form.monitor_nome}
            onChange={(e) => setForm({ ...form, monitor_nome: e.target.value })} />
          <Input label="Periodicidade" placeholder="ex.: Semanal" value={form.periodicidade}
            onChange={(e) => setForm({ ...form, periodicidade: e.target.value })} />
          <div className="sm:col-span-2">
            <Button type="submit" disabled={salvando}>{salvando ? "Cadastrando…" : "Cadastrar turma"}</Button>
          </div>
        </form>
      </Card>
      <Card title="Exportar Lista de Presença" subtitle="Gera o arquivo .xlsx do mês no layout oficial, a partir da frequência já lançada." className="animate-fade-in-up" style={staggerStyle(1)}>
        <form onSubmit={exportarListaPresenca} className="grid grid-cols-1 sm:grid-cols-4 gap-4 items-end">
          <div className="sm:col-span-2">
            <Select label="Turma" value={exportForm.turma_id} onChange={(e) => setExportForm({ ...exportForm, turma_id: e.target.value })} required>
              <option value="">— Selecione —</option>
              {turmas.map((t) => (
                <option key={t.id} value={t.id}>{poloNome(t.polo_id)} — {modalidadeNome(t.modalidade_id)} ({t.horario_inicio}–{t.horario_fim})</option>
              ))}
            </Select>
          </div>
          <Input label="Mês" type="number" min={1} max={12} value={exportForm.mes}
            onChange={(e) => setExportForm({ ...exportForm, mes: Number(e.target.value) })} required />
          <Input label="Ano" type="number" min={2000} max={2100} value={exportForm.ano}
            onChange={(e) => setExportForm({ ...exportForm, ano: Number(e.target.value) })} required />
          <div className="sm:col-span-4">
            <Button type="submit" variant="secondary" disabled={exportando}>{exportando ? "Exportando…" : "Exportar .xlsx"}</Button>
          </div>
        </form>
      </Card>
      <Card
        title="Turmas"
        actions={<Badge variant="accent">{turmas.length}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(2)}
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
                    <td className="px-3">
                      <select
                        className="text-sm border border-gray-200 rounded-lg px-2 py-1 bg-white hover:border-gray-400 focus:ring-2 focus:ring-brand/40 focus:border-brand outline-none disabled:opacity-50"
                        value={t.professor_id ?? ""}
                        disabled={
                          atribuirProfessorMutation.isPending && atribuirProfessorMutation.variables?.turmaId === t.id
                        }
                        onChange={(e) => atribuirProfessor(t.id, e.target.value)}
                      >
                        <option value="">— Sem professor —</option>
                        {professores
                          .filter((p) => p.polo_id === t.polo_id)
                          .map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.nome}
                            </option>
                          ))}
                      </select>
                    </td>
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
