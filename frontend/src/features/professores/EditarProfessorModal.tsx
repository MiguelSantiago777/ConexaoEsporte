import { FormEvent, useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Polo, Usuario } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Tabs } from "@/components/ui/Tabs";
import { useToast } from "@/components/ui/toast/ToastContext";
import { UsuarioAnexosTab } from "./UsuarioAnexosTab";

interface Props {
  professor: Usuario | null;
  polos: Polo[];
  ehMaster: boolean;
  onClose: () => void;
  onSalvo: () => void;
}

const ABAS = [
  { id: "dados", label: "Dados" },
  { id: "foto", label: "Foto" },
  { id: "documentos", label: "Documentos" },
  { id: "contrato", label: "Contrato" },
];

export function EditarProfessorModal({ professor, polos, ehMaster, onClose, onSalvo }: Props) {
  const toast = useToast();
  const [aba, setAba] = useState("dados");
  const [form, setForm] = useState({ nome: "", telefone: "", carga_horaria_semanal: "", polo_id: "", ativo: true });

  useEffect(() => {
    if (professor) {
      setForm({
        nome: professor.nome,
        telefone: professor.telefone ?? "",
        carga_horaria_semanal: professor.carga_horaria_semanal ?? "",
        polo_id: professor.polo_id ?? "",
        ativo: professor.ativo,
      });
      setAba("dados");
    }
  }, [professor]);

  const salvarMutation = useMutation({
    mutationFn: (payload: {
      id: string;
      nome: string;
      telefone: string;
      carga_horaria_semanal: string;
      polo_id: string;
      ativo: boolean;
    }) =>
      api.patch(`/usuarios/${payload.id}`, {
        nome: payload.nome,
        telefone: payload.telefone || null,
        carga_horaria_semanal: payload.carga_horaria_semanal || null,
        // Gestor de polo não pode alterar polo/situação do professor — envia
        // só o que já vinha preenchido, sem o risco de "resetar" o campo
        // (ver PATCH /usuarios/{id}, que rejeita esses campos vindos do gestor).
        ...(ehMaster ? { polo_id: payload.polo_id || null, ativo: payload.ativo } : {}),
      }),
    onSuccess: () => onSalvo(),
    onError: (err: any) => {
      toast.error(mensagemErroApi(err, "Erro ao salvar alterações."));
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
      <Tabs abas={ABAS} ativa={aba} onChange={setAba}>
        {aba === "dados" && (
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
            {ehMaster && (
              <>
                <Select
                  label="Polo"
                  value={form.polo_id}
                  onChange={(e) => setForm({ ...form, polo_id: e.target.value })}
                  required
                >
                  <option value="">Selecione…</option>
                  {polos.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nome}
                    </option>
                  ))}
                </Select>
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    className="w-5 h-5 accent-[#fcba27] rounded"
                    checked={form.ativo}
                    onChange={(e) => setForm({ ...form, ativo: e.target.checked })}
                  />
                  <span className="text-sm text-gray-700">
                    Ativo <span className="text-gray-400">— desmarque para desativar o acesso do professor</span>
                  </span>
                </label>
              </>
            )}
            <div className="flex flex-wrap gap-3">
              <Button type="submit" disabled={salvarMutation.isPending}>
                {salvarMutation.isPending ? "Salvando…" : "Salvar alterações"}
              </Button>
              <Button type="button" variant="secondary" onClick={onClose}>
                Cancelar
              </Button>
            </div>
          </form>
        )}
        {aba === "foto" && <UsuarioAnexosTab usuarioId={professor.id} tipo="FOTO" label="Foto" />}
        {aba === "documentos" && <UsuarioAnexosTab usuarioId={professor.id} tipo="DOCUMENTO" label="Documento" />}
        {aba === "contrato" && <UsuarioAnexosTab usuarioId={professor.id} tipo="CONTRATO" label="Contrato" />}
      </Tabs>
    </Modal>
  );
}
