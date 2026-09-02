import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Modalidade } from "@/types";
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
import { EditarModalidadeModal } from "./EditarModalidadeModal";

export function ModalidadesPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const { data: modalidades = [], isLoading: carregando } = useQuery({
    queryKey: ["modalidades"],
    queryFn: () => api.get<Modalidade[]>("/modalidades").then((r) => r.data),
  });
  const [salvando, setSalvando] = useState(false);
  const [form, setForm] = useState({ nome: "", descricao: "" });
  const [modalidadeEditando, setModalidadeEditando] = useState<Modalidade | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
      await api.post("/modalidades", { nome: form.nome, descricao: form.descricao || null });
      setForm({ nome: "", descricao: "" });
      toast.success("Modalidade cadastrada com sucesso.");
      queryClient.invalidateQueries({ queryKey: ["modalidades"] });
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao cadastrar modalidade."));
    } finally {
      setSalvando(false);
    }
  }

  const removerMutation = useMutation({
    mutationFn: (m: Modalidade) => api.delete(`/modalidades/${m.id}`),
    onSuccess: () => {
      toast.success("Modalidade removida.");
      queryClient.invalidateQueries({ queryKey: ["modalidades"] });
    },
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao remover modalidade.")),
  });

  function removerModalidade(m: Modalidade) {
    if (!window.confirm(`Remover a modalidade "${m.nome}"?`)) return;
    removerMutation.mutate(m);
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Modalidades" subtitle="Modalidades esportivas oferecidas pelos polos." />
      <Card title="Cadastrar modalidade" className="animate-fade-in-up" style={staggerStyle(0)}>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input label="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
          <Input label="Descrição" value={form.descricao} onChange={(e) => setForm({ ...form, descricao: e.target.value })} />
          <div className="sm:col-span-2">
            <Button type="submit" disabled={salvando}>{salvando ? "Cadastrando…" : "Cadastrar"}</Button>
          </div>
        </form>
      </Card>
      <Card
        title="Modalidades"
        actions={<Badge variant="accent">{modalidades.length}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(1)}
      >
        {carregando ? (
          <Spinner label="Carregando modalidades…" />
        ) : modalidades.length === 0 ? (
          <EmptyState message="Nenhuma modalidade cadastrada ainda." />
        ) : (
          <ul className="divide-y divide-gray-100">
            {modalidades.map((m) => (
              <li key={m.id} className="py-3 flex items-center justify-between gap-3">
                <div className="min-w-0 flex items-baseline gap-2">
                  <span className="font-medium text-gray-800">{m.nome}</span>
                  {m.descricao && <span className="text-gray-500 text-sm truncate">— {m.descricao}</span>}
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <button
                    type="button"
                    title="Editar"
                    onClick={() => setModalidadeEditando(m)}
                    className="text-gray-400 hover:text-brand transition-colors"
                  >
                    <PencilIcon />
                  </button>
                  <button
                    type="button"
                    title="Remover"
                    onClick={() => removerModalidade(m)}
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

      <EditarModalidadeModal
        modalidade={modalidadeEditando}
        onClose={() => setModalidadeEditando(null)}
        onSalvo={() => {
          setModalidadeEditando(null);
          toast.success("Alterações salvas.");
          queryClient.invalidateQueries({ queryKey: ["modalidades"] });
        }}
      />
    </div>
  );
}
