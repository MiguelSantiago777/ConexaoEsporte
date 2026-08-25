import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Modalidade } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";

export function ModalidadesPage() {
  const toast = useToast();
  const [modalidades, setModalidades] = useState<Modalidade[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [form, setForm] = useState({ nome: "", descricao: "" });

  async function carregar() {
    const { data } = await api.get<Modalidade[]>("/modalidades");
    setModalidades(data);
  }
  useEffect(() => {
    carregar().finally(() => setCarregando(false));
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
      await api.post("/modalidades", { nome: form.nome, descricao: form.descricao || null });
      setForm({ nome: "", descricao: "" });
      toast.success("Modalidade cadastrada com sucesso.");
      carregar();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao cadastrar modalidade.");
    } finally {
      setSalvando(false);
    }
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
              <li key={m.id} className="py-3 flex items-baseline gap-2">
                <span className="font-medium text-gray-800">{m.nome}</span>
                {m.descricao && <span className="text-gray-500 text-sm">— {m.descricao}</span>}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
