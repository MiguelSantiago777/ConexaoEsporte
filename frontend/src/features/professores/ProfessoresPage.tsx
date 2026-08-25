import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Polo, Usuario } from "@/types";
import { useAuth } from "@/features/auth/AuthContext";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";

const FORM_INICIAL = { nome: "", email: "", senha: "", polo_id: "" };

export function ProfessoresPage() {
  const { usuario } = useAuth();
  const toast = useToast();
  const ehMaster = usuario?.perfil === "MASTER";

  const [professores, setProfessores] = useState<Usuario[]>([]);
  const [polos, setPolos] = useState<Polo[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [form, setForm] = useState(FORM_INICIAL);
  const [salvando, setSalvando] = useState(false);

  async function carregar() {
    const { data } = await api.get<Usuario[]>("/usuarios");
    setProfessores(data.filter((u) => u.perfil === "PROFESSOR"));
  }

  useEffect(() => {
    Promise.all([carregar(), ehMaster ? api.get<Polo[]>("/polos").then(({ data }) => setPolos(data)) : null]).finally(
      () => setCarregando(false)
    );
  }, [ehMaster]);

  function nomePolo(poloId: string | null) {
    if (!poloId) return "—";
    if (!ehMaster) return usuario?.polo_nome ?? "—";
    return polos.find((p) => p.id === poloId)?.nome ?? "—";
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
      await api.post("/usuarios", {
        nome: form.nome,
        email: form.email,
        senha: form.senha,
        perfil: "PROFESSOR",
        polo_id: ehMaster ? form.polo_id || null : null,
      });
      setForm(FORM_INICIAL);
      toast.success("Professor cadastrado com sucesso.");
      carregar();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Erro ao cadastrar professor.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Professores"
        subtitle="Cadastre o acesso dos professores responsáveis pelas turmas do seu polo."
      />
      <Card title="Cadastrar professor" className="animate-fade-in-up" style={staggerStyle(0)}>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Nome"
            value={form.nome}
            onChange={(e) => setForm({ ...form, nome: e.target.value })}
            required
          />
          <Input
            label="Email"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
          <Input
            label="Senha"
            type="password"
            minLength={8}
            hint="Mínimo de 8 caracteres."
            value={form.senha}
            onChange={(e) => setForm({ ...form, senha: e.target.value })}
            required
          />
          {ehMaster ? (
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
          ) : (
            <Input label="Polo" value={usuario?.polo_nome ?? ""} disabled hint="Vinculado automaticamente ao seu polo." />
          )}
          <div className="sm:col-span-2">
            <Button type="submit" disabled={salvando}>
              {salvando ? "Cadastrando…" : "Cadastrar professor"}
            </Button>
          </div>
        </form>
      </Card>
      <Card
        title="Professores"
        actions={<Badge variant="accent">{professores.length}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(1)}
      >
        {carregando ? (
          <Spinner label="Carregando professores…" />
        ) : professores.length === 0 ? (
          <EmptyState message="Nenhum professor cadastrado ainda." />
        ) : (
          <div className="overflow-x-auto -mx-6">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                  <th className="py-2.5 px-6">Nome</th>
                  <th className="px-3">Email</th>
                  {ehMaster && <th className="px-3">Polo</th>}
                  <th className="px-3">Situação</th>
                </tr>
              </thead>
              <tbody>
                {professores.map((p) => (
                  <tr key={p.id} className="border-t border-gray-100 hover:bg-brand-light/60 transition-colors">
                    <td className="py-2.5 px-6 font-medium text-gray-800">{p.nome}</td>
                    <td className="px-3 text-gray-600">{p.email}</td>
                    {ehMaster && <td className="px-3 text-gray-600">{nomePolo(p.polo_id)}</td>}
                    <td className="px-3">
                      <Badge variant={p.ativo ? "accent" : "gray"}>{p.ativo ? "Ativo" : "Inativo"}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
