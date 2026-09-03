import { FormEvent, useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Almoxarifado, Usuario } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useToast } from "@/components/ui/toast/ToastContext";

interface Props {
  coordenador: Usuario | null;
  almoxarifados: Almoxarifado[];
  onClose: () => void;
  onSalvo: () => void;
}

export function EditarCoordenadorModal({ coordenador, almoxarifados, onClose, onSalvo }: Props) {
  const toast = useToast();
  const [form, setForm] = useState({ nome: "", almoxarifado_id: "", ativo: true });

  useEffect(() => {
    if (coordenador) {
      setForm({
        nome: coordenador.nome,
        almoxarifado_id: coordenador.almoxarifado_id ?? "",
        ativo: coordenador.ativo,
      });
    }
  }, [coordenador]);

  const salvarMutation = useMutation({
    mutationFn: (payload: { id: string } & typeof form) =>
      api.patch(`/usuarios/${payload.id}`, {
        nome: payload.nome, almoxarifado_id: payload.almoxarifado_id || null, ativo: payload.ativo,
      }),
    onSuccess: () => onSalvo(),
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao salvar alterações.")),
  });

  if (!coordenador) return null;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!coordenador) return;
    salvarMutation.mutate({ id: coordenador.id, ...form });
  }

  return (
    <Modal open={!!coordenador} onClose={onClose} title={`Editar — ${coordenador.nome}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
        <Select label="Almoxarifado" value={form.almoxarifado_id} onChange={(e) => setForm({ ...form, almoxarifado_id: e.target.value })} required>
          <option value="">Selecione…</option>
          {almoxarifados.map((a) => <option key={a.id} value={a.id}>{a.nome}</option>)}
        </Select>
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            className="w-5 h-5 accent-[#fcba27] rounded"
            checked={form.ativo}
            onChange={(e) => setForm({ ...form, ativo: e.target.checked })}
          />
          <span className="text-sm text-gray-700">
            Ativo <span className="text-gray-400">— desmarque para desativar o acesso do coordenador</span>
          </span>
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
