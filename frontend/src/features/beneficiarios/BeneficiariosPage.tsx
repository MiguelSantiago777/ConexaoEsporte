import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Beneficiario, Turma } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

/**
 * Página de cadastro e listagem de BENEFICIÁRIOS.
 * Nomenclatura oficial e obrigatória — nunca "aluno".
 */
export function BeneficiariosPage() {
  const [beneficiarios, setBeneficiarios] = useState<Beneficiario[]>([]);
  const [turmas, setTurmas] = useState<Turma[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [form, setForm] = useState({
    nome_completo: "",
    data_nascimento: "",
    documento: "",
    responsavel_legal_nome: "",
    responsavel_legal_contato: "",
    turma_id: "",
    observacoes_medicas: "",
  });

  async function carregar() {
    const [b, t] = await Promise.all([
      api.get<Beneficiario[]>("/beneficiarios"),
      api.get<Turma[]>("/turmas"),
    ]);
    setBeneficiarios(b.data);
    setTurmas(t.data);
  }

  useEffect(() => {
    carregar();
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    try {
      await api.post("/beneficiarios", {
        ...form,
        turma_id: form.turma_id || null,
        responsavel_legal_nome: form.responsavel_legal_nome || null,
        responsavel_legal_contato: form.responsavel_legal_contato || null,
        observacoes_medicas: form.observacoes_medicas || null,
      });
      setForm({
        nome_completo: "", data_nascimento: "", documento: "",
        responsavel_legal_nome: "", responsavel_legal_contato: "",
        turma_id: "", observacoes_medicas: "",
      });
      carregar();
    } catch (err: any) {
      setErro(err?.response?.data?.detail ?? "Erro ao cadastrar beneficiário.");
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Beneficiários</h1>

      <Card title="Cadastrar beneficiário">
        {erro && <div className="bg-red-50 text-red-700 text-sm p-2 rounded mb-4">{erro}</div>}
        <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
          <Input
            label="Nome completo"
            value={form.nome_completo}
            onChange={(e) => setForm({ ...form, nome_completo: e.target.value })}
            required
          />
          <Input
            label="Documento (CPF)"
            value={form.documento}
            onChange={(e) => setForm({ ...form, documento: e.target.value })}
            required
          />
          <Input
            label="Data de nascimento"
            type="date"
            value={form.data_nascimento}
            onChange={(e) => setForm({ ...form, data_nascimento: e.target.value })}
            required
          />
          <label className="block">
            <span className="block text-sm font-medium text-gray-700 mb-1">Turma</span>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              value={form.turma_id}
              onChange={(e) => setForm({ ...form, turma_id: e.target.value })}
            >
              <option value="">— Sem turma —</option>
              {turmas.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.horario_inicio}-{t.horario_fim} ({t.vagas_ocupadas}/{t.limite_vagas})
                </option>
              ))}
            </select>
          </label>
          <Input
            label="Responsável legal (nome)"
            value={form.responsavel_legal_nome}
            onChange={(e) => setForm({ ...form, responsavel_legal_nome: e.target.value })}
          />
          <Input
            label="Responsável legal (contato)"
            value={form.responsavel_legal_contato}
            onChange={(e) => setForm({ ...form, responsavel_legal_contato: e.target.value })}
          />
          <div className="col-span-2">
            <Input
              label="Observações médicas"
              value={form.observacoes_medicas}
              onChange={(e) => setForm({ ...form, observacoes_medicas: e.target.value })}
            />
          </div>
          <div className="col-span-2">
            <Button type="submit">Cadastrar beneficiário</Button>
          </div>
        </form>
      </Card>

      <Card title={`Beneficiários cadastrados (${beneficiarios.length})`}>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b">
              <th className="py-2">Nome</th>
              <th>Documento</th>
              <th>Nascimento</th>
              <th>Responsável</th>
            </tr>
          </thead>
          <tbody>
            {beneficiarios.map((b) => (
              <tr key={b.id} className="border-b last:border-0">
                <td className="py-2 font-medium">{b.nome_completo}</td>
                <td>{b.documento}</td>
                <td>{b.data_nascimento}</td>
                <td>{b.responsavel_legal_nome ?? "—"}</td>
              </tr>
            ))}
            {beneficiarios.length === 0 && (
              <tr>
                <td colSpan={4} className="py-4 text-center text-gray-400">
                  Nenhum beneficiário cadastrado ainda.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
