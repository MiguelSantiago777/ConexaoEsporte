import { FormEvent, useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Modalidade } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useToast } from "@/components/ui/toast/ToastContext";

interface Props {
  modalidade: Modalidade | null;
  onClose: () => void;
  onSalvo: () => void;
}

export function EditarModalidadeModal({ modalidade, onClose, onSalvo }: Props) {
  const toast = useToast();
  const [form, setForm] = useState({ nome: "", descricao: "" });

  useEffect(() => {
    if (modalidade) {
      setForm({ nome: modalidade.nome, descricao: modalidade.descricao ?? "" });
    }
  }, [modalidade]);

  const salvarMutation = useMutation({
    mutationFn: (payload: { id: string; nome: string; descricao: string }) =>
      api.patch(`/modalidades/${payload.id}`, { nome: payload.nome, descricao: payload.descricao || null }),
    onSuccess: () => onSalvo(),
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao salvar alterações.")),
  });

  if (!modalidade) return null;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!modalidade) return;
    salvarMutation.mutate({ id: modalidade.id, ...form });
  }

  return (
    <Modal open={!!modalidade} onClose={onClose} title={`Editar — ${modalidade.nome}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
        <Input
          label="Descrição"
          value={form.descricao}
          onChange={(e) => setForm({ ...form, descricao: e.target.value })}
        />
        <div className="flex flex-wrap gap-3">
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
