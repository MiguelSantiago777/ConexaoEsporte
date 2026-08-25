import { FormEvent, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { Beneficiario, Matricula, Modalidade, Polo, Turma } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";

interface Props {
  beneficiario: Beneficiario | null;
  turmas: Turma[];
  modalidades: Modalidade[];
  polos: Polo[];
  onClose: () => void;
  onAlterado: () => void;
}

export function MatriculasModal({ beneficiario, turmas, modalidades, polos, onClose, onAlterado }: Props) {
  const toast = useToast();
  const [matriculas, setMatriculas] = useState<Matricula[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [turmaId, setTurmaId] = useState("");
  const [matriculando, setMatriculando] = useState(false);

  useEffect(() => {
    if (!beneficiario) {
      setMatriculas([]);
      setTurmaId("");
      return;
    }
    setCarregando(true);
    api
      .get<Matricula[]>(`/beneficiarios/${beneficiario.id}/matriculas`)
      .then((r) => setMatriculas(r.data))
      .catch(() => toast.error("Não foi possível carregar as matrículas."))
      .finally(() => setCarregando(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [beneficiario]);

  function turmaLabel(turmaId: string) {
    const t = turmas.find((tu) => tu.id === turmaId);
    if (!t) return "Turma removida";
    const modalidade = modalidades.find((m) => m.id === t.modalidade_id)?.nome ?? "—";
    const polo = polos.find((p) => p.id === t.polo_id)?.nome ?? "—";
    return `${modalidade} · ${polo} · ${t.horario_inicio}–${t.horario_fim} (${t.dias_semana.join(", ")})`;
  }

  const matriculasAtivas = matriculas.filter((m) => m.ativo);

  const turmasDisponiveis = useMemo(() => {
    if (!beneficiario) return [];
    const idsJaMatriculado = new Set(matriculasAtivas.map((m) => m.turma_id));
    return turmas.filter((t) => t.polo_id === beneficiario.polo_id && !idsJaMatriculado.has(t.id));
  }, [turmas, beneficiario, matriculasAtivas]);

  if (!beneficiario) return null;

  async function matricular(e: FormEvent) {
    e.preventDefault();
    if (!beneficiario || !turmaId) return;
    setMatriculando(true);
    try {
      const { data } = await api.post<Matricula>(`/beneficiarios/${beneficiario.id}/matriculas`, {
        turma_id: turmaId,
      });
      setMatriculas((atual) => [...atual, data]);
      setTurmaId("");
      toast.success("Matrícula realizada com sucesso.");
      onAlterado();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao matricular o beneficiário.");
    } finally {
      setMatriculando(false);
    }
  }

  async function encerrar(matricula: Matricula) {
    if (!beneficiario) return;
    try {
      const { data } = await api.patch<Matricula>(
        `/beneficiarios/${beneficiario.id}/matriculas/${matricula.id}`,
        { ativo: false }
      );
      setMatriculas((atual) => atual.map((m) => (m.id === data.id ? data : m)));
      toast.success("Matrícula encerrada.");
      onAlterado();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao encerrar a matrícula.");
    }
  }

  return (
    <Modal open={!!beneficiario} onClose={onClose} title={`Matrículas — ${beneficiario.nome_completo}`}>
      <form onSubmit={matricular} className="flex items-end gap-3 mb-5">
        <div className="flex-1">
          <Select label="Matricular em nova turma" value={turmaId} onChange={(e) => setTurmaId(e.target.value)}>
            <option value="">— Selecione —</option>
            {turmasDisponiveis.map((t) => (
              <option key={t.id} value={t.id}>
                {turmaLabel(t.id)} — {t.vagas_ocupadas}/{t.limite_vagas} vagas
              </option>
            ))}
          </Select>
        </div>
        <Button type="submit" disabled={!turmaId || matriculando}>
          {matriculando ? "Matriculando…" : "Matricular"}
        </Button>
      </form>

      {carregando ? (
        <Spinner label="Carregando matrículas…" />
      ) : matriculasAtivas.length === 0 ? (
        <EmptyState message="Nenhuma matrícula ativa. O beneficiário pode estar em várias turmas ao mesmo tempo." />
      ) : (
        <ul className="divide-y divide-gray-100">
          {matriculasAtivas.map((m) => (
            <li key={m.id} className="py-3 flex items-center justify-between gap-3">
              <div className="min-w-0 flex items-center gap-2">
                <span className="text-sm text-gray-800 truncate">{turmaLabel(m.turma_id)}</span>
                <Badge variant="accent">Ativa</Badge>
              </div>
              <Button variant="secondary" type="button" onClick={() => encerrar(m)}>
                Encerrar
              </Button>
            </li>
          ))}
        </ul>
      )}
    </Modal>
  );
}
