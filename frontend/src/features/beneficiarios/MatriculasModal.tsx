import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
  const queryClient = useQueryClient();
  const [turmaId, setTurmaId] = useState("");

  const matriculasQueryKey = ["beneficiarios", beneficiario?.id, "matriculas"];
  const { data: matriculas = [], isLoading: carregando, isError } = useQuery({
    queryKey: matriculasQueryKey,
    queryFn: () => api.get<Matricula[]>(`/beneficiarios/${beneficiario!.id}/matriculas`).then((r) => r.data),
    enabled: !!beneficiario,
  });

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

  const matricularMutation = useMutation({
    mutationFn: (turma_id: string) =>
      api.post<Matricula>(`/beneficiarios/${beneficiario!.id}/matriculas`, { turma_id }),
    onSuccess: () => {
      setTurmaId("");
      toast.success("Matrícula realizada com sucesso.");
      queryClient.invalidateQueries({ queryKey: matriculasQueryKey });
      onAlterado();
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Erro ao matricular o beneficiário.");
    },
  });

  const encerrarMutation = useMutation({
    mutationFn: (matricula: Matricula) =>
      api.patch<Matricula>(`/beneficiarios/${beneficiario!.id}/matriculas/${matricula.id}`, { ativo: false }),
    onSuccess: () => {
      toast.success("Matrícula encerrada.");
      queryClient.invalidateQueries({ queryKey: matriculasQueryKey });
      onAlterado();
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Erro ao encerrar a matrícula.");
    },
  });

  if (!beneficiario) return null;

  function matricular(e: FormEvent) {
    e.preventDefault();
    if (!turmaId) return;
    matricularMutation.mutate(turmaId);
  }

  function encerrar(matricula: Matricula) {
    encerrarMutation.mutate(matricula);
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
        <Button type="submit" disabled={!turmaId || matricularMutation.isPending}>
          {matricularMutation.isPending ? "Matriculando…" : "Matricular"}
        </Button>
      </form>

      {carregando ? (
        <Spinner label="Carregando matrículas…" />
      ) : isError ? (
        <EmptyState message="Não foi possível carregar as matrículas." />
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
