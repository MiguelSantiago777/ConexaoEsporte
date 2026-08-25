import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Polo } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useToast } from "@/components/ui/toast/ToastContext";

interface Props {
  polo: Polo | null;
  onClose: () => void;
  onSalvo: () => void;
}

export function EditarPoloModal({ polo, onClose, onSalvo }: Props) {
  const toast = useToast();
  const [form, setForm] = useState({
    nome: "",
    codigo: "",
    endereco: "",
    horario_funcionamento: "",
    status: "ATIVO" as "ATIVO" | "INATIVO",
  });
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    if (polo) {
      setForm({
        nome: polo.nome,
        codigo: polo.codigo ?? "",
        endereco: polo.endereco ?? "",
        horario_funcionamento: polo.horario_funcionamento ?? "",
        status: polo.status,
      });
    }
  }, [polo]);

  if (!polo) return null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!polo) return;
    setSalvando(true);
    try {
      await api.patch(`/polos/${polo.id}`, {
        nome: form.nome,
        codigo: form.codigo.trim() || null,
        endereco: form.endereco || null,
        horario_funcionamento: form.horario_funcionamento || null,
        status: form.status,
      });
      onSalvo();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao salvar alterações.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Modal open={!!polo} onClose={onClose} title={`Editar — ${polo.nome}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
        <Input
          label="Código"
          placeholder="ex.: ZN01"
          value={form.codigo}
          onChange={(e) => setForm({ ...form, codigo: e.target.value.toUpperCase() })}
          maxLength={20}
          hint="Identificador curto, usado no lugar do ID nas telas."
        />
        <Input label="Endereço" value={form.endereco} onChange={(e) => setForm({ ...form, endereco: e.target.value })} />
        <Input
          label="Horário de funcionamento"
          placeholder="ex.: Seg a Sex, 08h às 18h"
          value={form.horario_funcionamento}
          onChange={(e) => setForm({ ...form, horario_funcionamento: e.target.value })}
        />
        <Select label="Status" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value as "ATIVO" | "INATIVO" })}>
          <option value="ATIVO">ATIVO</option>
          <option value="INATIVO">INATIVO</option>
        </Select>
        <div className="flex gap-3">
          <Button type="submit" disabled={salvando}>
            {salvando ? "Salvando…" : "Salvar alterações"}
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
        </div>
      </form>
    </Modal>
  );
}
