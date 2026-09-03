import { FormEvent, useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { ModuloDisponivel, Papel } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useToast } from "@/components/ui/toast/ToastContext";

interface Props {
  papel: Papel | null;
  modulos: ModuloDisponivel[];
  onClose: () => void;
  onSalvo: () => void;
}

export function EditarPapelModal({ papel, modulos, onClose, onSalvo }: Props) {
  const toast = useToast();
  const [form, setForm] = useState({ nome: "", descricao: "", modulos: [] as string[], ativo: true });

  useEffect(() => {
    if (papel) {
      setForm({ nome: papel.nome, descricao: papel.descricao ?? "", modulos: papel.modulos, ativo: papel.ativo });
    }
  }, [papel]);

  function alternarModulo(chave: string) {
    setForm((f) => ({
      ...f,
      modulos: f.modulos.includes(chave) ? f.modulos.filter((m) => m !== chave) : [...f.modulos, chave],
    }));
  }

  const salvarMutation = useMutation({
    mutationFn: (payload: { id: string } & typeof form) =>
      api.patch(`/papeis/${payload.id}`, {
        nome: payload.nome,
        descricao: payload.descricao || null,
        modulos: payload.modulos,
        ativo: payload.ativo,
      }),
    onSuccess: () => onSalvo(),
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao salvar alterações.")),
  });

  if (!papel) return null;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!papel) return;
    salvarMutation.mutate({ id: papel.id, ...form });
  }

  return (
    <Modal open={!!papel} onClose={onClose} title={`Editar — ${papel.nome}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
        <Input label="Descrição" value={form.descricao} onChange={(e) => setForm({ ...form, descricao: e.target.value })} />
        <div>
          <span className="block text-sm font-medium text-gray-700 mb-2">Módulos liberados</span>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {modulos.map((m) => (
              <label key={m.chave} className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={form.modulos.includes(m.chave)}
                  onChange={() => alternarModulo(m.chave)}
                  className="rounded border-gray-300 text-brand focus:ring-brand"
                />
                {m.label}
              </label>
            ))}
          </div>
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={form.ativo}
            onChange={(e) => setForm({ ...form, ativo: e.target.checked })}
            className="rounded border-gray-300 text-brand focus:ring-brand"
          />
          Papel ativo
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
