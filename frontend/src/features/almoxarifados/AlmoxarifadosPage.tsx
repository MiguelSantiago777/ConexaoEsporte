import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Almoxarifado, Usuario } from "@/types";
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
import { EditarAlmoxarifadoModal } from "./EditarAlmoxarifadoModal";
import { EditarCoordenadorModal } from "./EditarCoordenadorModal";

const FORM_COORDENADOR_INICIAL = { nome: "", email: "", senha: "", almoxarifado_id: "" };

export function AlmoxarifadosPage() {
  const { temPerfil } = useAuth();
  const ehMaster = temPerfil("MASTER");
  const toast = useToast();
  const queryClient = useQueryClient();
  const { data: almoxarifados = [], isLoading: carregando } = useQuery({
    queryKey: ["almoxarifados"],
    queryFn: () => api.get<Almoxarifado[]>("/almoxarifados").then((r) => r.data),
  });
  const [salvando, setSalvando] = useState(false);
  const [form, setForm] = useState({ nome: "", descricao: "" });
  const [almoxarifadoEditando, setAlmoxarifadoEditando] = useState<Almoxarifado | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
      await api.post("/almoxarifados", { nome: form.nome, descricao: form.descricao || null });
      setForm({ nome: "", descricao: "" });
      toast.success("Almoxarifado cadastrado com sucesso.");
      queryClient.invalidateQueries({ queryKey: ["almoxarifados"] });
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao cadastrar almoxarifado."));
    } finally {
      setSalvando(false);
    }
  }

  const removerMutation = useMutation({
    mutationFn: (a: Almoxarifado) => api.delete(`/almoxarifados/${a.id}`),
    onSuccess: () => {
      toast.success("Almoxarifado removido.");
      queryClient.invalidateQueries({ queryKey: ["almoxarifados"] });
    },
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao remover almoxarifado.")),
  });

  function removerAlmoxarifado(a: Almoxarifado) {
    if (!window.confirm(`Remover o almoxarifado "${a.nome}"?`)) return;
    removerMutation.mutate(a);
  }

  // --- Coordenadores de Almoxarifado (MASTER) — cada um só enxerga e opera
  // o próprio almoxarifado vinculado. ---
  const { data: coordenadores = [], isLoading: carregandoCoordenadores } = useQuery({
    queryKey: ["usuarios", "coordenadores-almoxarifado"],
    queryFn: () => api.get<Usuario[]>("/usuarios", { params: { perfil: "COORDENADOR_ALMOXARIFADO" } }).then((r) => r.data),
    enabled: ehMaster,
  });
  const [formCoordenador, setFormCoordenador] = useState(FORM_COORDENADOR_INICIAL);
  const [salvandoCoordenador, setSalvandoCoordenador] = useState(false);
  const [coordenadorEditando, setCoordenadorEditando] = useState<Usuario | null>(null);

  function nomeAlmoxarifado(id: string | null) {
    return almoxarifados.find((a) => a.id === id)?.nome ?? "—";
  }

  async function cadastrarCoordenador(e: FormEvent) {
    e.preventDefault();
    setSalvandoCoordenador(true);
    try {
      await api.post("/usuarios", {
        nome: formCoordenador.nome, email: formCoordenador.email, senha: formCoordenador.senha,
        perfil: "COORDENADOR_ALMOXARIFADO", almoxarifado_id: formCoordenador.almoxarifado_id,
      });
      setFormCoordenador(FORM_COORDENADOR_INICIAL);
      toast.success("Coordenador cadastrado com sucesso.");
      queryClient.invalidateQueries({ queryKey: ["usuarios", "coordenadores-almoxarifado"] });
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao cadastrar coordenador."));
    } finally {
      setSalvandoCoordenador(false);
    }
  }

  const desativarCoordenadorMutation = useMutation({
    mutationFn: (c: Usuario) => api.patch(`/usuarios/${c.id}`, { ativo: false }),
    onSuccess: () => {
      toast.success("Acesso do coordenador desativado.");
      queryClient.invalidateQueries({ queryKey: ["usuarios", "coordenadores-almoxarifado"] });
    },
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao desativar o coordenador.")),
  });

  function desativarCoordenador(c: Usuario) {
    if (!window.confirm(`Desativar o acesso de ${c.nome}? Ele deixa de conseguir fazer login no sistema.`)) return;
    desativarCoordenadorMutation.mutate(c);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Almoxarifados"
        subtitle="Locais físicos onde o estoque central fica guardado — o saldo de cada produto é controlado separadamente em cada um."
      />

      {ehMaster && (
        <Card title="Cadastrar almoxarifado" className="animate-fade-in-up" style={staggerStyle(0)}>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Nome" placeholder="ex.: Almoxarifado Central" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} required />
            <Input label="Descrição (opcional)" placeholder="ex.: Sede, Rua X, 123" value={form.descricao} onChange={(e) => setForm({ ...form, descricao: e.target.value })} />
            <div className="sm:col-span-2">
              <Button type="submit" disabled={salvando}>{salvando ? "Cadastrando…" : "Cadastrar"}</Button>
            </div>
          </form>
        </Card>
      )}

      <Card
        title="Almoxarifados"
        actions={<Badge variant="accent">{almoxarifados.length}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(1)}
      >
        {carregando ? (
          <Spinner label="Carregando almoxarifados…" />
        ) : almoxarifados.length === 0 ? (
          <EmptyState message="Nenhum almoxarifado cadastrado ainda." />
        ) : (
          <ul className="divide-y divide-gray-100">
            {almoxarifados.map((a) => (
              <li key={a.id} className="py-3 flex items-center justify-between gap-3">
                <div className="min-w-0 flex items-baseline gap-2 flex-wrap">
                  <span className="font-medium text-gray-800">{a.nome}</span>
                  {a.descricao && <span className="text-gray-500 text-sm truncate">— {a.descricao}</span>}
                  {!a.ativo && <Badge variant="gray">Inativo</Badge>}
                </div>
                {ehMaster && (
                  <div className="flex items-center gap-3 shrink-0">
                    <button type="button" title="Editar" onClick={() => setAlmoxarifadoEditando(a)} className="text-gray-400 hover:text-brand transition-colors">
                      <PencilIcon />
                    </button>
                    <button type="button" title="Remover" onClick={() => removerAlmoxarifado(a)} className="text-gray-400 hover:text-red-600 transition-colors">
                      <TrashIcon />
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>

      {ehMaster && (
        <Card
          title="Cadastrar coordenador de almoxarifado"
          subtitle="O coordenador só tem acesso ao almoxarifado vinculado — registra Entradas nele e acompanha o próprio saldo."
          className="animate-fade-in-up"
          style={staggerStyle(2)}
        >
          <form onSubmit={cadastrarCoordenador} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Nome" value={formCoordenador.nome} onChange={(e) => setFormCoordenador({ ...formCoordenador, nome: e.target.value })} required />
            <Input label="Email" type="email" value={formCoordenador.email} onChange={(e) => setFormCoordenador({ ...formCoordenador, email: e.target.value })} required />
            <Input label="Senha" type="password" minLength={8} hint="Mínimo de 8 caracteres." value={formCoordenador.senha} onChange={(e) => setFormCoordenador({ ...formCoordenador, senha: e.target.value })} required />
            <Select label="Almoxarifado" value={formCoordenador.almoxarifado_id} onChange={(e) => setFormCoordenador({ ...formCoordenador, almoxarifado_id: e.target.value })} required>
              <option value="">Selecione…</option>
              {almoxarifados.map((a) => <option key={a.id} value={a.id}>{a.nome}</option>)}
            </Select>
            <div className="sm:col-span-2">
              <Button type="submit" disabled={salvandoCoordenador}>{salvandoCoordenador ? "Cadastrando…" : "Cadastrar coordenador"}</Button>
            </div>
          </form>
        </Card>
      )}

      {ehMaster && (
        <Card
          title="Coordenadores de almoxarifado"
          actions={<Badge variant="accent">{coordenadores.length}</Badge>}
          className="animate-fade-in-up"
          style={staggerStyle(3)}
        >
          {carregandoCoordenadores ? (
            <Spinner label="Carregando coordenadores…" />
          ) : coordenadores.length === 0 ? (
            <EmptyState message="Nenhum coordenador cadastrado ainda." />
          ) : (
            <ul className="divide-y divide-gray-100">
              {coordenadores.map((c) => (
                <li key={c.id} className="py-3 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-gray-800 truncate">{c.nome}</span>
                      <Badge variant={c.ativo ? "accent" : "gray"}>{c.ativo ? "Ativo" : "Inativo"}</Badge>
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5 truncate">
                      {c.email} · {nomeAlmoxarifado(c.almoxarifado_id)}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <button type="button" title="Editar" onClick={() => setCoordenadorEditando(c)} className="text-gray-400 hover:text-brand transition-colors">
                      <PencilIcon />
                    </button>
                    <button type="button" title="Desativar" onClick={() => desativarCoordenador(c)} className="text-gray-400 hover:text-red-600 transition-colors">
                      <TrashIcon />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      <EditarAlmoxarifadoModal
        almoxarifado={almoxarifadoEditando}
        onClose={() => setAlmoxarifadoEditando(null)}
        onSalvo={() => {
          setAlmoxarifadoEditando(null);
          toast.success("Alterações salvas.");
          queryClient.invalidateQueries({ queryKey: ["almoxarifados"] });
        }}
      />

      <EditarCoordenadorModal
        coordenador={coordenadorEditando}
        almoxarifados={almoxarifados}
        onClose={() => setCoordenadorEditando(null)}
        onSalvo={() => {
          setCoordenadorEditando(null);
          toast.success("Alterações salvas.");
          queryClient.invalidateQueries({ queryKey: ["usuarios", "coordenadores-almoxarifado"] });
        }}
      />
    </div>
  );
}
