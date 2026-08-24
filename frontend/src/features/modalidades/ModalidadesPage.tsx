import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Modalidade } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export function ModalidadesPage() {
  const [modalidades, setModalidades] = useState<Modalidade[]>([]);
  const [form, setForm] = useState({ nome: "", descricao: "" });

  async function carregar() {
    const { data } = await api.get<Modalidade[]>("/modalidades");
    setModalidades(data);
  }
  useEffect(() => { carregar(); }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await api.post("/modalidades", { nome: form.nome, descricao: form.descricao || null });
    setForm({ nome: "", descricao: "" });
    carregar();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Modalidades</h1>
      <Card title="Cadastrar modalidade">
        <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
          <Input label="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
          <Input label="Descrição" value={form.descricao} onChange={(e) => setForm({ ...form, descricao: e.target.value })} />
          <div className="col-span-2"><Button type="submit">Cadastrar</Button></div>
        </form>
      </Card>
      <Card title={`Modalidades (${modalidades.length})`}>
        <ul className="divide-y">
          {modalidades.map((m) => (
            <li key={m.id} className="py-2">
              <span className="font-medium">{m.nome}</span>
              {m.descricao && <span className="text-gray-500 text-sm"> — {m.descricao}</span>}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
