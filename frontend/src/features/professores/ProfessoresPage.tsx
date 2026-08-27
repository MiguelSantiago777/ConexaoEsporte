import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Modalidade, Polo, Turma, Usuario } from "@/types";
import { useAuth } from "@/features/auth/AuthContext";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";
import { PencilIcon, TrashIcon } from "@/components/ui/icons";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { EditarProfessorModal } from "./EditarProfessorModal";

const FORM_INICIAL = {
  nome: "", email: "", senha: "", polo_id: "", modalidade_id: "", turma_id: "",
  telefone: "", carga_horaria_semanal: "",
};

export function ProfessoresPage() {
  const { usuario } = useAuth();
  const toast = useToast();
  const queryClient = useQueryClient();
  const ehMaster = usuario?.perfil === "MASTER";

  const { data: usuarios = [], isLoading: carregando } = useQuery({
    queryKey: ["usuarios"],
    queryFn: () => api.get<Usuario[]>("/usuarios").then((r) => r.data),
  });
  const professores = usuarios.filter((u) => u.perfil === "PROFESSOR");

  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
    enabled: ehMaster,
  });
  const { data: turmas = [] } = useQuery({
    queryKey: ["turmas"],
    queryFn: () => api.get<Turma[]>("/turmas").then((r) => r.data),
  });
  const { data: modalidades = [] } = useQuery({
    queryKey: ["modalidades"],
    queryFn: () => api.get<Modalidade[]>("/modalidades").then((r) => r.data),
  });

  const [form, setForm] = useState(FORM_INICIAL);
  const [salvando, setSalvando] = useState(false);
  const [professorEditando, setProfessorEditando] = useState<Usuario | null>(null);

  function nomePolo(poloId: string | null) {
    if (!poloId) return "—";
    if (!ehMaster) return usuario?.polo_nome ?? "—";
    return polos.find((p) => p.id === poloId)?.nome ?? "—";
  }

  const desativarMutation = useMutation({
    mutationFn: (p: Usuario) => api.patch(`/usuarios/${p.id}`, { ativo: false }),
    onSuccess: () => {
      toast.success("Acesso do professor desativado.");
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
    },
    onError: (err: any) => {
      toast.error(mensagemErroApi(err, "Erro ao desativar o professor."));
    },
  });

  function excluirProfessor(p: Usuario) {
    if (!window.confirm(`Desativar o acesso de ${p.nome}? Ele deixa de conseguir fazer login no sistema.`)) return;
    desativarMutation.mutate(p);
  }

  // Gestor de polo já opera dentro do próprio polo — não escolhe.
  const poloEfetivo = ehMaster ? form.polo_id : usuario?.polo_id ?? "";

  const turmasDoFormulario = useMemo(
    () => turmas.filter((t) => t.polo_id === poloEfetivo && t.modalidade_id === form.modalidade_id),
    [turmas, poloEfetivo, form.modalidade_id]
  );

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form.modalidade_id || !form.turma_id) {
      toast.error("Selecione a modalidade e a turma do professor.");
      return;
    }
    setSalvando(true);
    try {
      const { data: criado } = await api.post<Usuario>("/usuarios", {
        nome: form.nome,
        email: form.email,
        senha: form.senha,
        perfil: "PROFESSOR",
        polo_id: ehMaster ? form.polo_id || null : null,
        telefone: form.telefone || null,
        carga_horaria_semanal: form.carga_horaria_semanal || null,
      });
      try {
        await api.patch(`/turmas/${form.turma_id}`, { professor_id: criado.id });
        toast.success("Professor cadastrado e vinculado à turma com sucesso.");
      } catch (err: any) {
        toast.error(
          `Professor cadastrado, mas houve um problema ao vincular à turma: ${
            mensagemErroApi(err, "erro desconhecido")
          }. Você pode tentar novamente na tela de Turmas.`
        );
      }
      setForm(FORM_INICIAL);
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
      queryClient.invalidateQueries({ queryKey: ["turmas"] });
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao cadastrar professor."));
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
              onChange={(e) => setForm({ ...form, polo_id: e.target.value, modalidade_id: "", turma_id: "" })}
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
          <Select
            label="Modalidade"
            value={form.modalidade_id}
            onChange={(e) => setForm({ ...form, modalidade_id: e.target.value, turma_id: "" })}
            disabled={!poloEfetivo}
            required
          >
            <option value="">Selecione…</option>
            {modalidades.map((m) => (
              <option key={m.id} value={m.id}>
                {m.nome}
              </option>
            ))}
          </Select>
          <Select
            label="Turma"
            value={form.turma_id}
            onChange={(e) => setForm({ ...form, turma_id: e.target.value })}
            disabled={!form.modalidade_id}
            required
          >
            <option value="">Selecione…</option>
            {turmasDoFormulario.map((t) => (
              <option key={t.id} value={t.id}>
                {t.horario_inicio}–{t.horario_fim} ({t.dias_semana.join(", ")})
                {t.professor_id ? " — já tem professor" : ""}
              </option>
            ))}
          </Select>
          <p className="sm:col-span-2 text-xs text-gray-400">
            O professor será vinculado como responsável por essa turma — selecionar uma turma que já tem
            professor substitui o vínculo atual.
          </p>
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
                  <th className="px-3">Telefone</th>
                  <th className="px-3">Carga horária</th>
                  <th className="px-3">Situação</th>
                  <th className="px-3 text-right pr-6">Ações</th>
                </tr>
              </thead>
              <tbody>
                {professores.map((p) => (
                  <tr key={p.id} className="border-t border-gray-100 hover:bg-brand-light/60 transition-colors">
                    <td className="py-2.5 px-6 font-medium text-gray-800">{p.nome}</td>
                    <td className="px-3 text-gray-600">{p.email}</td>
                    {ehMaster && <td className="px-3 text-gray-600">{nomePolo(p.polo_id)}</td>}
                    <td className="px-3 text-gray-600">{p.telefone ?? "—"}</td>
                    <td className="px-3 text-gray-600">{p.carga_horaria_semanal ?? "—"}</td>
                    <td className="px-3">
                      <Badge variant={p.ativo ? "accent" : "gray"}>{p.ativo ? "Ativo" : "Inativo"}</Badge>
                    </td>
                    <td className="px-3 text-right pr-6">
                      <button
                        type="button"
                        title="Editar"
                        onClick={() => setProfessorEditando(p)}
                        className="text-gray-400 hover:text-brand transition-colors"
                      >
                        <PencilIcon />
                      </button>
                      {ehMaster && (
                        <button
                          type="button"
                          title="Desativar"
                          onClick={() => excluirProfessor(p)}
                          className="text-gray-400 hover:text-red-600 transition-colors ml-3"
                        >
                          <TrashIcon />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <EditarProfessorModal
        professor={professorEditando}
        onClose={() => setProfessorEditando(null)}
        onSalvo={() => {
          setProfessorEditando(null);
          toast.success("Alterações salvas.");
          queryClient.invalidateQueries({ queryKey: ["usuarios"] });
        }}
      />
    </div>
  );
}
