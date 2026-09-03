import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { ModuloDisponivel, Papel } from "@/types";
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
import { EditarPapelModal } from "./EditarPapelModal";

export function PapeisPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const { data: papeis = [], isLoading: carregando } = useQuery({
    queryKey: ["papeis"],
    queryFn: () => api.get<Papel[]>("/papeis").then((r) => r.data),
  });
  const { data: modulos = [] } = useQuery({
    queryKey: ["papeis", "modulos"],
    queryFn: () => api.get<ModuloDisponivel[]>("/papeis/modulos").then((r) => r.data),
  });
  const [salvando, setSalvando] = useState(false);
  const [form, setForm] = useState({ nome: "", descricao: "", modulos: [] as string[] });
  const [papelEditando, setPapelEditando] = useState<Papel | null>(null);

  function alternarModulo(chave: string) {
    setForm((f) => ({
      ...f,
      modulos: f.modulos.includes(chave) ? f.modulos.filter((m) => m !== chave) : [...f.modulos, chave],
    }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
      await api.post("/papeis", { nome: form.nome, descricao: form.descricao || null, modulos: form.modulos });
      setForm({ nome: "", descricao: "", modulos: [] });
      toast.success("Papel cadastrado com sucesso.");
      queryClient.invalidateQueries({ queryKey: ["papeis"] });
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao cadastrar papel."));
    } finally {
      setSalvando(false);
    }
  }

  const removerMutation = useMutation({
    mutationFn: (p: Papel) => api.delete(`/papeis/${p.id}`),
    onSuccess: () => {
      toast.success("Papel removido.");
      queryClient.invalidateQueries({ queryKey: ["papeis"] });
    },
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao remover papel.")),
  });

  function removerPapel(p: Papel) {
    if (!window.confirm(`Remover o papel "${p.nome}"?`)) return;
    removerMutation.mutate(p);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Central de Acessos"
        subtitle="Crie níveis de acesso personalizados escolhendo os módulos do sistema, para depois vincular usuários com perfil Personalizado a eles."
      />
      <Card title="Cadastrar papel" className="animate-fade-in-up" style={staggerStyle(0)}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
            <Input label="Descrição" value={form.descricao} onChange={(e) => setForm({ ...form, descricao: e.target.value })} />
          </div>
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
          <Button type="submit" disabled={salvando}>{salvando ? "Cadastrando…" : "Cadastrar"}</Button>
        </form>
      </Card>
      <Card
        title="Papéis"
        actions={<Badge variant="accent">{papeis.length}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(1)}
      >
        {carregando ? (
          <Spinner label="Carregando papéis…" />
        ) : papeis.length === 0 ? (
          <EmptyState message="Nenhum papel cadastrado ainda." />
        ) : (
          <ul className="divide-y divide-gray-100">
            {papeis.map((p) => (
              <li key={p.id} className="py-3 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-baseline gap-2 flex-wrap">
                    <span className="font-medium text-gray-800">{p.nome}</span>
                    {p.descricao && <span className="text-gray-500 text-sm truncate">— {p.descricao}</span>}
                    <Badge variant={p.ativo ? "accent" : "gray"}>{p.ativo ? "Ativo" : "Inativo"}</Badge>
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {p.modulos.length === 0 ? (
                      <span className="text-xs text-gray-400">Nenhum módulo liberado</span>
                    ) : (
                      p.modulos.map((chave) => (
                        <Badge key={chave} variant="brand">{modulos.find((m) => m.chave === chave)?.label ?? chave}</Badge>
                      ))
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <button
                    type="button"
                    title="Editar"
                    onClick={() => setPapelEditando(p)}
                    className="text-gray-400 hover:text-brand transition-colors"
                  >
                    <PencilIcon />
                  </button>
                  <button
                    type="button"
                    title="Remover"
                    onClick={() => removerPapel(p)}
                    className="text-gray-400 hover:text-red-600 transition-colors"
                  >
                    <TrashIcon />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <EditarPapelModal
        papel={papelEditando}
        modulos={modulos}
        onClose={() => setPapelEditando(null)}
        onSalvo={() => {
          setPapelEditando(null);
          toast.success("Alterações salvas.");
          queryClient.invalidateQueries({ queryKey: ["papeis"] });
        }}
      />
    </div>
  );
}
