import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import { maskCPF, maskTelefone } from "@/lib/masks";
import type { Almoxarifado, Pagina, Papel, Perfil, Polo, Usuario } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";
import { Paginacao } from "@/components/ui/Paginacao";
import { PencilIcon, TrashIcon } from "@/components/ui/icons";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { EditarUsuarioModal } from "./EditarUsuarioModal";

const TAMANHO_PAGINA = 20;

const PERFIS: { value: Perfil; label: string }[] = [
  { value: "MASTER", label: "Master" },
  { value: "GESTOR_POLO", label: "Gestor de Polo" },
  { value: "PROFESSOR", label: "Professor" },
  { value: "PERSONALIZADO", label: "Personalizado" },
];

const FORM_VAZIO = {
  nome: "", email: "", telefone: "", cpf: "",
  perfil: "PROFESSOR" as Perfil, polo_id: "", almoxarifado_id: "", papel_id: "",
};

export function UsuariosPage() {
  const toast = useToast();
  const queryClient = useQueryClient();

  const [filtroPerfil, setFiltroPerfil] = useState<Perfil | "">("");
  const [pagina, setPagina] = useState(1);

  const { data: paginaUsuarios, isLoading: carregando } = useQuery({
    queryKey: ["usuarios", "pagina", pagina, filtroPerfil],
    queryFn: () =>
      api
        .get<Pagina<Usuario>>("/usuarios", { params: { pagina, tamanho_pagina: TAMANHO_PAGINA, perfil: filtroPerfil || undefined } })
        .then((r) => r.data),
  });
  const usuarios = paginaUsuarios?.itens ?? [];
  const totalUsuarios = paginaUsuarios?.total ?? 0;

  const { data: polos = [] } = useQuery({
    queryKey: ["polos", "todos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
  });
  const { data: almoxarifados = [] } = useQuery({
    queryKey: ["almoxarifados"],
    queryFn: () => api.get<Almoxarifado[]>("/almoxarifados").then((r) => r.data),
  });
  const { data: papeis = [] } = useQuery({
    queryKey: ["papeis", "todos"],
    queryFn: () => api.get<Papel[]>("/papeis").then((r) => r.data),
  });

  function nomeVinculo(u: Usuario): string {
    if (u.perfil === "GESTOR_POLO" || u.perfil === "PROFESSOR") {
      return polos.find((p) => p.id === u.polo_id)?.nome ?? "—";
    }
    if (u.perfil === "COORDENADOR_ALMOXARIFADO") {
      return almoxarifados.find((a) => a.id === u.almoxarifado_id)?.nome ?? "—";
    }
    if (u.perfil === "PERSONALIZADO") {
      return papeis.find((p) => p.id === u.papel_id)?.nome ?? "—";
    }
    return "—";
  }

  const [form, setForm] = useState(FORM_VAZIO);
  const [salvando, setSalvando] = useState(false);
  const [usuarioEditando, setUsuarioEditando] = useState<Usuario | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
      await api.post("/usuarios", {
        nome: form.nome,
        email: form.email,
        telefone: form.telefone || null,
        cpf: form.cpf || null,
        perfil: form.perfil,
        polo_id: form.perfil === "GESTOR_POLO" || form.perfil === "PROFESSOR" ? form.polo_id || null : null,
        almoxarifado_id: form.perfil === "COORDENADOR_ALMOXARIFADO" ? form.almoxarifado_id || null : null,
        papel_id: form.perfil === "PERSONALIZADO" ? form.papel_id || null : null,
      });
      setForm(FORM_VAZIO);
      toast.success("Usuário cadastrado. Ele entra com a senha temporária padrão e é obrigado a trocá-la no primeiro acesso.");
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
    } catch (err: unknown) {
      toast.error(mensagemErroApi(err, "Erro ao cadastrar usuário."));
    } finally {
      setSalvando(false);
    }
  }

  const excluirMutation = useMutation({
    mutationFn: (u: Usuario) => api.delete(`/usuarios/${u.id}`),
    onSuccess: () => {
      toast.success("Usuário excluído.");
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
    },
    onError: (err: unknown) => toast.error(mensagemErroApi(err, "Erro ao excluir usuário.")),
  });

  function excluirUsuario(u: Usuario) {
    if (
      !window.confirm(
        `Excluir o acesso de "${u.nome}" definitivamente? Essa ação não pode ser desfeita. Se preferir só suspender o acesso, edite o usuário e desmarque Ativo.`
      )
    ) {
      return;
    }
    excluirMutation.mutate(u);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Usuários"
        subtitle="Todas as contas de acesso ao sistema, de qualquer perfil. Usuário novo entra com a senha temporária padrão e é obrigado a trocá-la no primeiro acesso."
      />

      <Card title="Cadastrar usuário" className="animate-fade-in-up" style={staggerStyle(0)}>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input label="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
          <Input label="E-mail" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          <Input
            label="Telefone" value={form.telefone} inputMode="tel"
            onChange={(e) => setForm({ ...form, telefone: maskTelefone(e.target.value) })}
          />
          <Input
            label="CPF" value={form.cpf} inputMode="numeric"
            onChange={(e) => setForm({ ...form, cpf: maskCPF(e.target.value) })}
          />
          <Select
            label="Perfil" value={form.perfil}
            onChange={(e) => setForm({ ...form, perfil: e.target.value as Perfil, polo_id: "", almoxarifado_id: "", papel_id: "" })}
          >
            {PERFIS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
          </Select>
          {(form.perfil === "GESTOR_POLO" || form.perfil === "PROFESSOR") && (
            <Select label="Polo" value={form.polo_id} onChange={(e) => setForm({ ...form, polo_id: e.target.value })} required>
              <option value="">Selecione…</option>
              {polos.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
            </Select>
          )}
          {form.perfil === "COORDENADOR_ALMOXARIFADO" && (
            <Select label="Estoque" value={form.almoxarifado_id} onChange={(e) => setForm({ ...form, almoxarifado_id: e.target.value })} required>
              <option value="">Selecione…</option>
              {almoxarifados.map((a) => <option key={a.id} value={a.id}>{a.nome}</option>)}
            </Select>
          )}
          {form.perfil === "PERSONALIZADO" && (
            <Select label="Papel" value={form.papel_id} onChange={(e) => setForm({ ...form, papel_id: e.target.value })} required>
              <option value="">Selecione…</option>
              {papeis.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
            </Select>
          )}
          <div className="sm:col-span-2">
            <Button type="submit" disabled={salvando}>{salvando ? "Cadastrando…" : "Cadastrar usuário"}</Button>
          </div>
        </form>
      </Card>

      <Card
        title="Usuários"
        actions={<Badge variant="accent">{totalUsuarios}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(1)}
      >
        <div className="mb-4 sm:max-w-xs">
          <Select
            label="Filtrar por perfil" value={filtroPerfil}
            onChange={(e) => { setFiltroPerfil(e.target.value as Perfil | ""); setPagina(1); }}
          >
            <option value="">Todos os perfis</option>
            {PERFIS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
          </Select>
        </div>
        {carregando ? (
          <Spinner label="Carregando usuários…" />
        ) : totalUsuarios === 0 ? (
          <EmptyState message="Nenhum usuário encontrado." />
        ) : (
          <>
            {/* Celular: lista de cards. Telas sm+: tabela. */}
            <ul className="sm:hidden divide-y divide-gray-100">
              {usuarios.map((u) => (
                <li key={u.id} className="py-3.5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="font-medium text-gray-800 truncate">{u.nome}</div>
                      <div className="text-xs text-gray-500 mt-0.5 truncate">{u.email} · {nomeVinculo(u)}</div>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <Badge variant="brand">{PERFIS.find((p) => p.value === u.perfil)?.label ?? u.perfil}</Badge>
                      <Badge variant={u.ativo ? "accent" : "gray"}>{u.ativo ? "Ativo" : "Inativo"}</Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-5 mt-3 flex-wrap">
                    <button
                      type="button"
                      title="Editar"
                      onClick={() => setUsuarioEditando(u)}
                      className="text-gray-400 hover:text-brand transition-colors -m-1.5 p-1.5"
                    >
                      <PencilIcon className="w-[18px] h-[18px]" />
                    </button>
                    <button
                      type="button"
                      title="Excluir"
                      onClick={() => excluirUsuario(u)}
                      className="text-gray-400 hover:text-red-600 transition-colors -m-1.5 p-1.5"
                    >
                      <TrashIcon className="w-[18px] h-[18px]" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>

            <div className="hidden sm:block overflow-x-auto -mx-5 sm:-mx-8">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                    <th className="py-2.5 px-8">Nome</th>
                    <th className="px-3">E-mail</th>
                    <th className="px-3">Perfil</th>
                    <th className="px-3">Vínculo</th>
                    <th className="px-3">Status</th>
                    <th className="px-3 text-right pr-8">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {usuarios.map((u) => (
                    <tr key={u.id} className="border-t border-gray-100 hover:bg-brand-light/60 transition-colors">
                      <td className="py-2.5 px-8 font-medium text-gray-800">{u.nome}</td>
                      <td className="px-3 text-gray-600">{u.email}</td>
                      <td className="px-3">
                        <Badge variant="brand">{PERFIS.find((p) => p.value === u.perfil)?.label ?? u.perfil}</Badge>
                      </td>
                      <td className="px-3 text-gray-600">{nomeVinculo(u)}</td>
                      <td className="px-3">
                        <Badge variant={u.ativo ? "accent" : "gray"}>{u.ativo ? "Ativo" : "Inativo"}</Badge>
                      </td>
                      <td className="px-3 text-right pr-8">
                        <div className="flex items-center justify-end gap-3">
                          <button
                            type="button"
                            title="Editar"
                            onClick={() => setUsuarioEditando(u)}
                            className="text-gray-400 hover:text-brand transition-colors"
                          >
                            <PencilIcon />
                          </button>
                          <button
                            type="button"
                            title="Excluir"
                            onClick={() => excluirUsuario(u)}
                            className="text-gray-400 hover:text-red-600 transition-colors"
                          >
                            <TrashIcon />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        <Paginacao pagina={pagina} tamanhoPagina={TAMANHO_PAGINA} total={totalUsuarios} onChange={setPagina} />
      </Card>

      <EditarUsuarioModal
        usuario={usuarioEditando}
        polos={polos}
        almoxarifados={almoxarifados}
        papeis={papeis}
        onClose={() => setUsuarioEditando(null)}
        onSalvo={() => {
          setUsuarioEditando(null);
          toast.success("Alterações salvas.");
          queryClient.invalidateQueries({ queryKey: ["usuarios"] });
        }}
      />
    </div>
  );
}
