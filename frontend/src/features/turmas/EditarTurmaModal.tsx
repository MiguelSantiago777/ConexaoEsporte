import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Modalidade, Turma } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useToast } from "@/components/ui/toast/ToastContext";

const DIAS = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"];

interface Props {
  turma: Turma | null;
  poloNome: string;
  modalidades: Modalidade[];
  onClose: () => void;
  onSalvo: () => void;
}

function formDaTurma(turma: Turma) {
  return {
    modalidade_id: turma.modalidade_id,
    horario_inicio: turma.horario_inicio,
    horario_fim: turma.horario_fim,
    dias_semana: turma.dias_semana,
    limite_vagas: turma.limite_vagas,
    coordenador_nome: turma.coordenador_nome ?? "",
    monitor_nome: turma.monitor_nome ?? "",
    periodicidade: turma.periodicidade ?? "",
  };
}

export function EditarTurmaModal({ turma, poloNome, modalidades, onClose, onSalvo }: Props) {
  const toast = useToast();
  const [form, setForm] = useState(() => (turma ? formDaTurma(turma) : null));
  const [turmaAnterior, setTurmaAnterior] = useState(turma);

  if (turma !== turmaAnterior) {
    setTurmaAnterior(turma);
    if (turma) setForm(formDaTurma(turma));
  }

  const salvarMutation = useMutation({
    mutationFn: (payload: { id: string; dados: ReturnType<typeof formDaTurma> }) =>
      api.patch(`/turmas/${payload.id}`, { ...payload.dados, limite_vagas: Number(payload.dados.limite_vagas) }),
    onSuccess: () => onSalvo(),
    onError: (err: unknown) => toast.error(mensagemErroApi(err, "Erro ao salvar alterações.")),
  });

  if (!turma || !form) return null;

  const trocouModalidade = form.modalidade_id !== turma.modalidade_id;
  const nomeModalidade = (id: string) => modalidades.find((m) => m.id === id)?.nome ?? "—";

  function toggleDia(dia: string) {
    setForm((f) =>
      f && {
        ...f,
        dias_semana: f.dias_semana.includes(dia) ? f.dias_semana.filter((d) => d !== dia) : [...f.dias_semana, dia],
      }
    );
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!turma || !form) return;
    if (form.dias_semana.length === 0) {
      toast.error("Selecione ao menos um dia da semana.");
      return;
    }
    salvarMutation.mutate({ id: turma.id, dados: form });
  }

  return (
    <Modal open={!!turma} onClose={onClose} title={`Editar turma — ${poloNome}`}>
      <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="sm:col-span-2">
          <Select
            label="Modalidade"
            value={form.modalidade_id}
            onChange={(e) => setForm({ ...form, modalidade_id: e.target.value })}
            required
          >
            {modalidades.map((m) => <option key={m.id} value={m.id}>{m.nome}</option>)}
          </Select>
          {trocouModalidade && (
            <p className="mt-2 rounded-lg border border-brand/15 bg-brand-light px-3 py-2 text-sm text-brand-dark">
              Os matriculados passam a constar em {nomeModalidade(form.modalidade_id)}. Se o polo ficar sem turma de{" "}
              {nomeModalidade(turma.modalidade_id)}, os interessados e a lista de espera do polo também são transferidos.
            </p>
          )}
        </div>
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
        <Input label="Periodicidade" placeholder="ex.: Semanal" value={form.periodicidade}
          onChange={(e) => setForm({ ...form, periodicidade: e.target.value })} />
        <Input label="Coordenador" value={form.coordenador_nome}
          onChange={(e) => setForm({ ...form, coordenador_nome: e.target.value })} />
        <Input label="Monitor" value={form.monitor_nome}
          onChange={(e) => setForm({ ...form, monitor_nome: e.target.value })} />
        <div className="sm:col-span-2 flex flex-wrap gap-3">
          <Button type="submit" disabled={salvarMutation.isPending}>
            {salvarMutation.isPending ? "Salvando…" : "Salvar alterações"}
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
        </div>
      </form>
    </Modal>
  );
}
