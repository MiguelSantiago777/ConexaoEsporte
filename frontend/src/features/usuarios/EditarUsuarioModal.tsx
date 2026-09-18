import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import { maskCPF, maskTelefone } from "@/lib/masks";
import type { Almoxarifado, Papel, Polo, Usuario } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useToast } from "@/components/ui/toast/ToastContext";

interface Props {
  usuario: Usuario | null;
  polos: Polo[];
  almoxarifados: Almoxarifado[];
  papeis: Papel[];
  onClose: () => void;
  onSalvo: () => void;
}

const FORM_VAZIO = { nome: "", telefone: "", cpf: "", ativo: true, polo_id: "", almoxarifado_id: "", papel_id: "" };

export function EditarUsuarioModal({ usuario, polos, almoxarifados, papeis, onClose, onSalvo }: Props) {
  const toast = useToast();
  const [form, setForm] = useState(FORM_VAZIO);
  const [usuarioAnterior, setUsuarioAnterior] = useState(usuario);

  if (usuario !== usuarioAnterior) {
    setUsuarioAnterior(usuario);
    if (usuario) {
      setForm({
        nome: usuario.nome,
        telefone: usuario.telefone ?? "",
        cpf: usuario.cpf ?? "",
        ativo: usuario.ativo,
        polo_id: usuario.polo_id ?? "",
        almoxarifado_id: usuario.almoxarifado_id ?? "",
        papel_id: usuario.papel_id ?? "",
      });
    }
  }

  const salvarMutation = useMutation({
    mutationFn: (payload: { id: string } & typeof form) =>
      api.patch(`/usuarios/${payload.id}`, {
        nome: payload.nome,
        telefone: payload.telefone || null,
        cpf: payload.cpf || null,
        ativo: payload.ativo,
        polo_id: usuario!.perfil === "GESTOR_POLO" || usuario!.perfil === "PROFESSOR" ? payload.polo_id || null : undefined,
        almoxarifado_id: usuario!.perfil === "COORDENADOR_ALMOXARIFADO" ? payload.almoxarifado_id || null : undefined,
        papel_id: usuario!.perfil === "PERSONALIZADO" ? payload.papel_id || null : undefined,
      }),
    onSuccess: () => onSalvo(),
    onError: (err: unknown) => toast.error(mensagemErroApi(err, "Erro ao salvar alterações.")),
  });

  if (!usuario) return null;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!usuario) return;
    salvarMutation.mutate({ id: usuario.id, ...form });
  }

  return (
    <Modal open={!!usuario} onClose={onClose} title={`Editar — ${usuario.nome}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
        <Input label="E-mail" value={usuario.email} disabled hint="O e-mail não pode ser alterado por aqui." />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Telefone" value={form.telefone} inputMode="tel"
            onChange={(e) => setForm({ ...form, telefone: maskTelefone(e.target.value) })}
          />
          <Input
            label="CPF" value={form.cpf} inputMode="numeric"
            onChange={(e) => setForm({ ...form, cpf: maskCPF(e.target.value) })}
          />
        </div>
        {(usuario.perfil === "GESTOR_POLO" || usuario.perfil === "PROFESSOR") && (
          <Select label="Polo" value={form.polo_id} onChange={(e) => setForm({ ...form, polo_id: e.target.value })} required>
            <option value="">Selecione…</option>
            {polos.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
          </Select>
        )}
        {usuario.perfil === "COORDENADOR_ALMOXARIFADO" && (
          <Select label="Almoxarifado" value={form.almoxarifado_id} onChange={(e) => setForm({ ...form, almoxarifado_id: e.target.value })} required>
            <option value="">Selecione…</option>
            {almoxarifados.map((a) => <option key={a.id} value={a.id}>{a.nome}</option>)}
          </Select>
        )}
        {usuario.perfil === "PERSONALIZADO" && (
          <Select label="Papel" value={form.papel_id} onChange={(e) => setForm({ ...form, papel_id: e.target.value })} required>
            <option value="">Selecione…</option>
            {papeis.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
          </Select>
        )}
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            className="w-5 h-5 accent-[#fcba27] rounded"
            checked={form.ativo}
            onChange={(e) => setForm({ ...form, ativo: e.target.checked })}
          />
          <span className="text-sm text-gray-700">
            Ativo <span className="text-gray-400">— desmarque para desativar o acesso</span>
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
