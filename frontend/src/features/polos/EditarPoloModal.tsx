import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Polo, Usuario } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useToast } from "@/components/ui/toast/ToastContext";
import { maskCPF, maskTelefone } from "@/lib/masks";
import { EnderecoMapaField } from "./EnderecoMapaField";

interface Props {
  polo: Polo | null;
  onClose: () => void;
  onSalvo: () => void;
  /** Atualiza a lista da página por trás, sem fechar o modal — usado ao
   * criar o acesso do gestor, diferente de `onSalvo` (que fecha o modal). */
  onAtualizado?: () => void;
}

const GESTOR_FORM_VAZIO = { nome: "", email: "", telefone: "", cpf: "" };

const FORM_VAZIO = {
  nome: "",
  codigo: "",
  endereco: "",
  horario_funcionamento: "",
  status: "ATIVO" as "ATIVO" | "INATIVO",
  representante_legal_nome: "", representante_legal_cpf: "", representante_legal_rg: "",
  responsavel_nome: "", responsavel_email: "", responsavel_telefone: "",
};

export function EditarPoloModal({ polo, onClose, onSalvo, onAtualizado }: Props) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [form, setForm] = useState(FORM_VAZIO);
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);

  const [gestorId, setGestorId] = useState<string | null>(null);
  const [gestorForm, setGestorForm] = useState(GESTOR_FORM_VAZIO);

  const { data: usuarios = [] } = useQuery({
    queryKey: ["usuarios"],
    queryFn: () => api.get<Usuario[]>("/usuarios").then((r) => r.data),
    enabled: !!gestorId,
  });

  function set<K extends keyof typeof FORM_VAZIO>(campo: K, valor: (typeof FORM_VAZIO)[K]) {
    setForm((f) => ({ ...f, [campo]: valor }));
  }

  const [poloAnterior, setPoloAnterior] = useState(polo);

  const gestor = usuarios.find((u) => u.id === gestorId) ?? null;

  const criarGestorMutation = useMutation({
    mutationFn: async () => {
      const { data: novoGestor } = await api.post<Usuario>("/usuarios", {
        nome: gestorForm.nome,
        email: gestorForm.email,
        telefone: gestorForm.telefone || null,
        cpf: gestorForm.cpf || null,
        perfil: "GESTOR_POLO",
        polo_id: polo!.id,
      });
      await api.patch(`/polos/${polo!.id}`, { gestor_responsavel_id: novoGestor.id });
      return novoGestor;
    },
    onSuccess: (novoGestor) => {
      toast.success("Acesso criado — enviamos um email para o gestor definir a própria senha.");
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
      setGestorId(novoGestor.id);
      setGestorForm(GESTOR_FORM_VAZIO);
      onAtualizado?.();
    },
    onError: (err: unknown) => {
      toast.error(mensagemErroApi(err, "Erro ao criar acesso do gestor."));
    },
  });

  function handleCriarGestor() {
    if (!polo) return;
    if (!gestorForm.nome.trim() || !gestorForm.email.trim()) {
      toast.error("Informe nome e e-mail do gestor de polo.");
      return;
    }
    criarGestorMutation.mutate();
  }

  if (polo !== poloAnterior) {
    setPoloAnterior(polo);
    setGestorId(polo?.gestor_responsavel_id ?? null);
    setGestorForm(GESTOR_FORM_VAZIO);
    if (polo) {
      setForm({
        nome: polo.nome,
        codigo: polo.codigo ?? "",
        endereco: polo.endereco ?? "",
        horario_funcionamento: polo.horario_funcionamento ?? "",
        status: polo.status as "ATIVO" | "INATIVO",
        representante_legal_nome: polo.representante_legal_nome ?? "",
        representante_legal_cpf: polo.representante_legal_cpf ?? "",
        representante_legal_rg: polo.representante_legal_rg ?? "",
        responsavel_nome: polo.responsavel_nome ?? "", responsavel_email: polo.responsavel_email ?? "",
        responsavel_telefone: polo.responsavel_telefone ?? "",
      });
      setLatitude(polo.latitude);
      setLongitude(polo.longitude);
    }
  }

  const salvarMutation = useMutation({
    mutationFn: (dadosForm: typeof FORM_VAZIO) =>
      api.patch(`/polos/${polo!.id}`, {
        nome: dadosForm.nome,
        codigo: dadosForm.codigo.trim() || null,
        endereco: dadosForm.endereco || null,
        horario_funcionamento: dadosForm.horario_funcionamento || null,
        status: dadosForm.status,
        representante_legal_nome: dadosForm.representante_legal_nome || null,
        representante_legal_cpf: dadosForm.representante_legal_cpf || null,
        representante_legal_rg: dadosForm.representante_legal_rg || null,
        responsavel_nome: dadosForm.responsavel_nome || null, responsavel_email: dadosForm.responsavel_email || null,
        responsavel_telefone: dadosForm.responsavel_telefone || null,
        latitude, longitude,
      }),
    onSuccess: () => onSalvo(),
    onError: (err: unknown) => {
      toast.error(mensagemErroApi(err, "Erro ao salvar alterações."));
    },
  });

  if (!polo) return null;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!polo) return;
    salvarMutation.mutate(form);
  }

  return (
    <Modal open={!!polo} onClose={onClose} title={`Editar — ${polo.nome}`} maxWidth="max-w-3xl">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input label="Nome" value={form.nome} onChange={(e) => set("nome", e.target.value)} required />
          <Input
            label="Código"
            placeholder="ex.: ZN01"
            value={form.codigo}
            onChange={(e) => set("codigo", e.target.value.toUpperCase())}
            maxLength={20}
            hint="Identificador curto, usado no lugar do ID nas telas."
          />
          <Input label="Endereço" value={form.endereco} onChange={(e) => set("endereco", e.target.value)} />
          <Input
            label="Horário de funcionamento"
            placeholder="ex.: Seg a Sex, 08h às 18h"
            value={form.horario_funcionamento}
            onChange={(e) => set("horario_funcionamento", e.target.value)}
          />
          <EnderecoMapaField
            onEnderecoChange={(endereco) => set("endereco", endereco)}
            latitude={latitude}
            longitude={longitude}
            onChange={(lat, lon) => { setLatitude(lat); setLongitude(lon); }}
          />
          <Select label="Status" value={form.status} onChange={(e) => set("status", e.target.value as "ATIVO" | "INATIVO")}>
            <option value="ATIVO">ATIVO</option>
            <option value="INATIVO">INATIVO</option>
          </Select>
        </div>

        <div className="border-t border-gray-100 pt-4">
          <h3 className="text-sm font-semibold text-brand-dark mb-1">Representante legal</h3>
          <p className="text-xs text-gray-400 mb-3">
            Usado no Termo de Responsabilidade. CPF é opcional; mais de um polo pode ter o mesmo representante.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <Input
                label="Nome do representante" value={form.representante_legal_nome}
                onChange={(e) => set("representante_legal_nome", e.target.value)}
              />
            </div>
            <Input
              label="CPF (opcional)" value={form.representante_legal_cpf} inputMode="numeric"
              onChange={(e) => set("representante_legal_cpf", maskCPF(e.target.value))}
            />
            <Input
              label="RG" value={form.representante_legal_rg}
              onChange={(e) => set("representante_legal_rg", e.target.value)}
            />
          </div>
        </div>

        <div className="border-t border-gray-100 pt-4">
          <h3 className="text-sm font-semibold text-brand-dark mb-1">Contato do núcleo</h3>
          <p className="text-xs text-gray-400 mb-3">Usado na Identificação do Núcleo da Ficha de Execução.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Responsável" value={form.responsavel_nome} onChange={(e) => set("responsavel_nome", e.target.value)} />
            <Input label="Telefone" value={form.responsavel_telefone} onChange={(e) => set("responsavel_telefone", e.target.value)} />
            <div className="sm:col-span-2">
              <Input label="E-mail" value={form.responsavel_email} onChange={(e) => set("responsavel_email", e.target.value)} />
            </div>
          </div>
        </div>

        <div className="border-t border-gray-100 pt-4">
          <h3 className="text-sm font-semibold text-brand-dark mb-3">Acesso do Gestor de Polo</h3>
          {gestorId ? (
            <div className="text-sm text-gray-600 grid grid-cols-1 sm:grid-cols-2 gap-2">
              <p><span className="font-medium text-gray-800">Nome:</span> {gestor?.nome ?? "—"}</p>
              <p><span className="font-medium text-gray-800">E-mail:</span> {gestor?.email ?? "—"}</p>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-xs text-gray-400">
                Este polo ainda não tem um acesso de Gestor de Polo vinculado. O gestor recebe por email um
                link para definir a própria senha — ninguém mais precisa conhecê-la.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="sm:col-span-2">
                  <Input
                    label="Nome do gestor"
                    value={gestorForm.nome}
                    onChange={(e) => setGestorForm((f) => ({ ...f, nome: e.target.value }))}
                  />
                </div>
                <div className="sm:col-span-2">
                  <Input
                    label="E-mail"
                    type="email"
                    value={gestorForm.email}
                    onChange={(e) => setGestorForm((f) => ({ ...f, email: e.target.value }))}
                  />
                </div>
                <Input
                  label="Telefone" value={gestorForm.telefone} inputMode="tel"
                  onChange={(e) => setGestorForm((f) => ({ ...f, telefone: maskTelefone(e.target.value) }))}
                />
                <Input
                  label="CPF" value={gestorForm.cpf} inputMode="numeric"
                  onChange={(e) => setGestorForm((f) => ({ ...f, cpf: maskCPF(e.target.value) }))}
                />
              </div>
              <Button type="button" variant="secondary" onClick={handleCriarGestor} disabled={criarGestorMutation.isPending}>
                {criarGestorMutation.isPending ? "Criando…" : "Criar acesso do gestor"}
              </Button>
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-3">
          <Button type="submit" disabled={salvarMutation.isPending}>
            {salvarMutation.isPending ? "Salvando…" : "Salvar alterações"}
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
        </div>
      </form>
    </Modal>
  );
}
