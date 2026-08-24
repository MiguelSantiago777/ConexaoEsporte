import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Polo } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export function PolosPage() {
  const [polos, setPolos] = useState<Polo[]>([]);
  const [form, setForm] = useState({ nome: "", endereco: "" });
  const [erro, setErro] = useState<string | null>(null);

  async function carregar() {
    const { data } = await api.get<Polo[]>("/polos");
    setPolos(data);
  }
  useEffect(() => { carregar(); }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    try {
      await api.post("/polos", { nome: form.nome, endereco: form.endereco || null });
      setForm({ nome: "", endereco: "" });
      carregar();
    } catch (err: any) {
      setErro(err?.response?.data?.detail ?? "Erro ao cadastrar polo.");
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Polos</h1>
      <Card title="Cadastrar polo">
        {erro && <div className="bg-red-50 text-red-700 text-sm p-2 rounded mb-4">{erro}</div>}
        <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
          <Input label="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
          <Input label="Endereço" value={form.endereco} onChange={(e) => setForm({ ...form, endereco: e.target.value })} />
          <div className="col-span-2"><Button type="submit">Cadastrar polo</Button></div>
        </form>
      </Card>
      <Card title={`Polos (${polos.length})`}>
        <table className="w-full text-sm">
          <thead><tr className="text-left text-gray-500 border-b"><th className="py-2">Nome</th><th>Endereço</th><th>Status</th></tr></thead>
          <tbody>
            {polos.map((p) => (
              <tr key={p.id} className="border-b last:border-0">
                <td className="py-2 font-medium">{p.nome}</td><td>{p.endereco ?? "—"}</td>
                <td><span className="px-2 py-0.5 rounded text-xs bg-brand-light text-brand-dark">{p.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
