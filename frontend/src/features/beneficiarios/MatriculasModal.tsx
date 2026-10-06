import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Beneficiario, InteressesModalidade, Matricula, Modalidade, Polo, Turma } from "@/types";
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
    onError: (err: unknown) => {
      toast.error(mensagemErroApi(err, "Erro ao matricular o beneficiário."));
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
    onError: (err: unknown) => {
      toast.error(mensagemErroApi(err, "Erro ao encerrar a matrícula."));
    },
  });

  const interessesQueryKey = ["beneficiarios", beneficiario?.id, "interesses"];
  const { data: interesses } = useQuery({
    queryKey: interessesQueryKey,
    queryFn: () =>
      api.get<InteressesModalidade>(`/beneficiarios/${beneficiario!.id}/interesses`).then((r) => r.data),
    enabled: !!beneficiario,
  });
  const idsInteresse = interesses?.modalidade_ids ?? [];

  const idsMatriculado = new Set(
    matriculasAtivas
      .map((m) => turmas.find((t) => t.id === m.turma_id)?.modalidade_id)
      .filter((id): id is string => !!id)
  );
  const aguardandoTurma = modalidades.filter((m) => idsInteresse.includes(m.id) && !idsMatriculado.has(m.id));

  const interessesMutation = useMutation({
    mutationFn: (modalidade_ids: string[]) =>
      api.put<InteressesModalidade>(`/beneficiarios/${beneficiario!.id}/interesses`, { modalidade_ids }),
    onSuccess: ({ data }) => {
      queryClient.setQueryData(interessesQueryKey, data);
      onAlterado();
    },
    onError: (err: unknown) => {
      toast.error(mensagemErroApi(err, "Erro ao salvar as modalidades de interesse."));
    },
  });

  function alternarInteresse(modalidadeId: string) {
    interessesMutation.mutate(
      idsInteresse.includes(modalidadeId)
        ? idsInteresse.filter((id) => id !== modalidadeId)
        : [...idsInteresse, modalidadeId]
    );
  }

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
    <Modal open={!!beneficiario} onClose={onClose} title={`Modalidades — ${beneficiario.nome_completo}`}>
      <section className="mb-6">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-brand-dark/70 mb-2">Situação</h3>
        {idsMatriculado.size === 0 && aguardandoTurma.length === 0 ? (
          <p className="text-sm text-gray-500">Sem matrícula nem modalidade de interesse registrada.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {modalidades
              .filter((m) => idsMatriculado.has(m.id))
              .map((m) => (
                <Badge key={m.id} variant="court">
                  {m.nome} · matriculado
                </Badge>
              ))}
            {aguardandoTurma.map((m) => (
              <Badge key={m.id} variant="accent">
                {m.nome} · interesse, aguardando turma
              </Badge>
            ))}
          </div>
        )}

        <h3 className="text-xs font-semibold uppercase tracking-wide text-brand-dark/70 mt-5 mb-2">
          Modalidades de interesse
        </h3>
        <div className="flex flex-wrap gap-2">
          {modalidades.map((m) => {
            const marcada = idsInteresse.includes(m.id);
            return (
              <button
                type="button"
                key={m.id}
                aria-pressed={marcada}
                onClick={() => alternarInteresse(m.id)}
                disabled={interessesMutation.isPending}
                className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors disabled:opacity-60 ${marcada ? "bg-brand text-white border-brand" : "bg-white border-gray-300 text-gray-600 hover:bg-gray-50"}`}
              >
                {m.nome}
              </button>
            );
          })}
        </div>
        <p className="text-xs text-gray-400 mt-2">
          Quando uma turma dessa modalidade for criada no polo, os interessados podem ser matriculados de uma vez.
        </p>
      </section>

      <form onSubmit={matricular} className="flex flex-col sm:flex-row sm:items-end gap-3 mb-5">
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
