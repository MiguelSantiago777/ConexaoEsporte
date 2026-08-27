import { FormEvent, useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Usuario } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useToast } from "@/components/ui/toast/ToastContext";

interface Props {
  professor: Usuario | null;
  onClose: () => void;
  onSalvo: () => void;
}

export function EditarProfessorModal({ professor, onClose, onSalvo }: Props) {
  const toast = useToast();
  const [form, setForm] = useState({ nome: "", telefone: "", carga_horaria_semanal: "" });

  useEffect(() => {
    if (professor) {
      setForm({
        nome: professor.nome,
        telefone: professor.telefone ?? "",
        carga_horaria_semanal: professor.carga_horaria_semanal ?? "",
      });
    }
  }, [professor]);

  const salvarMutation = useMutation({
    mutationFn: (payload: { id: string; nome: string; telefone: string; carga_horaria_semanal: string }) =>
      api.patch(`/usuarios/${payload.id}`, {
        nome: payload.nome,
        telefone: payload.telefone || null,
        carga_horaria_semanal: payload.carga_horaria_semanal || null,
      }),
    onSuccess: () => onSalvo(),
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Erro ao salvar alterações.");
    },
  });

  if (!professor) return null;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!professor) return;
    salvarMutation.mutate({ id: professor.id, ...form });
  }

  return (
    <Modal open={!!professor} onClose={onClose} title={`Editar — ${professor.nome}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
        <Input
          label="Telefone"
          value={form.telefone}
          onChange={(e) => setForm({ ...form, telefone: e.target.value })}
        />
        <Input
          label="Carga horária semanal"
          placeholder="ex.: 20h"
          hint="Usado na Planilha de Núcleos — RH e Beneficiário."
          value={form.carga_horaria_semanal}
          onChange={(e) => setForm({ ...form, carga_horaria_semanal: e.target.value })}
        />
        <div className="flex gap-3">
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
