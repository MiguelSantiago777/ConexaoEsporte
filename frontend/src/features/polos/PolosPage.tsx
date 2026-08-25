import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Polo } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";
import { PencilIcon, TrashIcon } from "@/components/ui/icons";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { EditarPoloModal } from "./EditarPoloModal";

export function PolosPage() {
  const toast = useToast();
  const [polos, setPolos] = useState<Polo[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [form, setForm] = useState({ nome: "", codigo: "", endereco: "", horario_funcionamento: "" });
  const [salvando, setSalvando] = useState(false);
  const [poloEditando, setPoloEditando] = useState<Polo | null>(null);

  async function carregar() {
    const { data } = await api.get<Polo[]>("/polos");
    setPolos(data);
  }
  useEffect(() => {
    carregar().finally(() => setCarregando(false));
  }, []);

  async function excluirPolo(p: Polo) {
    if (!window.confirm(`Desativar o polo "${p.nome}"? Ele deixa de aparecer como opção em novos cadastros.`)) return;
    try {
      await api.patch(`/polos/${p.id}`, { status: "INATIVO" });
      toast.success("Polo desativado.");
      carregar();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao desativar polo.");
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
      await api.post("/polos", {
        nome: form.nome,
        codigo: form.codigo.trim() || null,
        endereco: form.endereco || null,
        horario_funcionamento: form.horario_funcionamento || null,
      });
      setForm({ nome: "", codigo: "", endereco: "", horario_funcionamento: "" });
      toast.success("Polo cadastrado com sucesso.");
      carregar();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao cadastrar polo.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Polos" subtitle="Unidades onde os projetos esportivos são executados." />
      <Card title="Cadastrar polo" className="animate-fade-in-up" style={staggerStyle(0)}>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="sm:col-span-2">
            <Input label="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
          </div>
          <Input
            label="Código"
            placeholder="ex.: ZN01"
            value={form.codigo}
            onChange={(e) => setForm({ ...form, codigo: e.target.value.toUpperCase() })}
            maxLength={20}
            hint="Identificador curto, usado no lugar do ID nas telas."
          />
          <div className="sm:col-span-3">
            <Input label="Endereço" value={form.endereco} onChange={(e) => setForm({ ...form, endereco: e.target.value })} />
          </div>
          <div className="sm:col-span-3">
            <Input
              label="Horário de funcionamento"
              placeholder="ex.: Seg a Sex, 08h às 18h"
              value={form.horario_funcionamento}
              onChange={(e) => setForm({ ...form, horario_funcionamento: e.target.value })}
            />
          </div>
          <div className="sm:col-span-3">
            <Button type="submit" disabled={salvando}>{salvando ? "Cadastrando…" : "Cadastrar polo"}</Button>
          </div>
        </form>
      </Card>
      <Card
        title="Polos"
        actions={<Badge variant="accent">{polos.length}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(1)}
      >
        {carregando ? (
          <Spinner label="Carregando polos…" />
        ) : polos.length === 0 ? (
          <EmptyState message="Nenhum polo cadastrado ainda." />
        ) : (
          <div className="overflow-x-auto -mx-6">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                  <th className="py-2.5 px-6">Código</th>
                  <th className="px-3">Nome</th>
                  <th className="px-3">Endereço</th>
                  <th className="px-3">Horário de funcionamento</th>
                  <th className="px-3">Status</th>
                  <th className="px-3 text-right pr-6">Ações</th>
                </tr>
              </thead>
              <tbody>
                {polos.map((p) => (
                  <tr key={p.id} className="border-t border-gray-100 hover:bg-brand-light/60 transition-colors">
                    <td className="py-2.5 px-6 font-medium text-gray-800">{p.codigo ?? "—"}</td>
                    <td className="px-3 text-gray-600">{p.nome}</td>
                    <td className="px-3 text-gray-600">{p.endereco ?? "—"}</td>
                    <td className="px-3 text-gray-600">{p.horario_funcionamento ?? "—"}</td>
                    <td className="px-3">
                      <Badge variant={p.status === "ATIVO" ? "accent" : "gray"}>{p.status}</Badge>
                    </td>
                    <td className="px-3 text-right pr-6">
                      <div className="flex items-center justify-end gap-3">
                        <button
                          type="button"
                          title="Editar"
                          onClick={() => setPoloEditando(p)}
                          className="text-gray-400 hover:text-brand transition-colors"
                        >
                          <PencilIcon />
                        </button>
                        {p.status === "ATIVO" && (
                          <button
                            type="button"
                            title="Desativar"
                            onClick={() => excluirPolo(p)}
                            className="text-gray-400 hover:text-red-600 transition-colors"
                          >
                            <TrashIcon />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <EditarPoloModal
        polo={poloEditando}
        onClose={() => setPoloEditando(null)}
        onSalvo={() => {
          setPoloEditando(null);
          toast.success("Alterações salvas.");
          carregar();
        }}
      />
    </div>
  );
}
