import { FormEvent, useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Produto } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useToast } from "@/components/ui/toast/ToastContext";

interface Props {
  produto: Produto | null;
  onClose: () => void;
  onSalvo: () => void;
}

export function EditarProdutoModal({ produto, onClose, onSalvo }: Props) {
  const toast = useToast();
  const [form, setForm] = useState({ nome: "", unidade_medida: "", descricao: "", ativo: true });

  useEffect(() => {
    if (produto) {
      setForm({
        nome: produto.nome, unidade_medida: produto.unidade_medida,
        descricao: produto.descricao ?? "", ativo: produto.ativo,
      });
    }
  }, [produto]);

  const salvarMutation = useMutation({
    mutationFn: (payload: { id: string } & typeof form) =>
      api.patch(`/produtos/${payload.id}`, {
        nome: payload.nome, unidade_medida: payload.unidade_medida,
        descricao: payload.descricao || null, ativo: payload.ativo,
      }),
    onSuccess: () => onSalvo(),
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao salvar alterações.")),
  });

  if (!produto) return null;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!produto) return;
    salvarMutation.mutate({ id: produto.id, ...form });
  }

  return (
    <Modal open={!!produto} onClose={onClose} title={`Editar — ${produto.nome}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
        <Input label="Unidade de medida" value={form.unidade_medida} onChange={(e) => setForm({ ...form, unidade_medida: e.target.value })} required />
        <Input label="Descrição" value={form.descricao} onChange={(e) => setForm({ ...form, descricao: e.target.value })} />
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={form.ativo} onChange={(e) => setForm({ ...form, ativo: e.target.checked })} className="rounded border-gray-300 text-brand focus:ring-brand" />
          Produto ativo
        </label>
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
