import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Polo, Usuario } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useToast } from "@/components/ui/toast/ToastContext";
import { EnderecoMapaField } from "./EnderecoMapaField";

interface Props {
  polo: Polo | null;
  onClose: () => void;
  onSalvo: () => void;
  /** Atualiza a lista da página por trás, sem fechar o modal — usado ao
   * criar o acesso do gestor, diferente de `onSalvo` (que fecha o modal). */
  onAtualizado?: () => void;
}

const GESTOR_FORM_VAZIO = { nome: "", email: "", senha: "" };

const FORM_VAZIO = {
  nome: "",
  codigo: "",
  endereco: "",
  horario_funcionamento: "",
  status: "ATIVO" as "ATIVO" | "INATIVO",
  processo_sei: "", termo_fomento_numero: "", nome_entidade: "", cnpj: "",
  representante_legal_nome: "", representante_legal_cpf: "", objeto: "",
  vigencia_inicio: "", vigencia_fim: "", valor_pactuado: "", valor_executado: "",
  parlamentar: "", emenda: "",
  aditivo1_objeto: "", aditivo1_data: "",
  aditivo2_objeto: "", aditivo2_data: "",
  responsavel_nome: "", responsavel_email: "", responsavel_telefone: "",
  representante_legal_rg: "", representante_legal_endereco: "",
  representante_legal_bairro: "", representante_legal_cidade: "",
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

  useEffect(() => {
    setGestorId(polo?.gestor_responsavel_id ?? null);
    setGestorForm(GESTOR_FORM_VAZIO);
  }, [polo]);

  const gestor = usuarios.find((u) => u.id === gestorId) ?? null;

  const criarGestorMutation = useMutation({
    mutationFn: async () => {
      const { data: novoGestor } = await api.post<Usuario>("/usuarios", {
        nome: gestorForm.nome,
        email: gestorForm.email,
        senha: gestorForm.senha,
        perfil: "GESTOR_POLO",
        polo_id: polo!.id,
      });
      await api.patch(`/polos/${polo!.id}`, { gestor_responsavel_id: novoGestor.id });
      return novoGestor;
    },
    onSuccess: (novoGestor) => {
      toast.success("Acesso do gestor criado com sucesso.");
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
      setGestorId(novoGestor.id);
      setGestorForm(GESTOR_FORM_VAZIO);
      onAtualizado?.();
    },
    onError: (err: any) => {
      toast.error(mensagemErroApi(err, "Erro ao criar acesso do gestor."));
    },
  });

  function handleCriarGestor() {
    if (!polo) return;
    if (!gestorForm.nome.trim() || !gestorForm.email.trim() || !gestorForm.senha) {
      toast.error("Informe nome, e-mail e senha do gestor de polo.");
      return;
    }
    if (gestorForm.senha.length < 8) {
      toast.error("A senha do gestor deve ter pelo menos 8 caracteres.");
      return;
    }
    criarGestorMutation.mutate();
  }

  useEffect(() => {
    if (polo) {
      const p1 = polo.termos_aditivos.find((a) => a.numero === "PRIMEIRO");
      const p2 = polo.termos_aditivos.find((a) => a.numero === "SEGUNDO");
      setForm({
        nome: polo.nome,
        codigo: polo.codigo ?? "",
        endereco: polo.endereco ?? "",
        horario_funcionamento: polo.horario_funcionamento ?? "",
        status: polo.status as "ATIVO" | "INATIVO",
        processo_sei: polo.processo_sei ?? "", termo_fomento_numero: polo.termo_fomento_numero ?? "",
        nome_entidade: polo.nome_entidade ?? "", cnpj: polo.cnpj ?? "",
        representante_legal_nome: polo.representante_legal_nome ?? "",
        representante_legal_cpf: polo.representante_legal_cpf ?? "", objeto: polo.objeto ?? "",
        vigencia_inicio: polo.vigencia_inicio ?? "", vigencia_fim: polo.vigencia_fim ?? "",
        valor_pactuado: polo.valor_pactuado ?? "", valor_executado: polo.valor_executado ?? "",
        parlamentar: polo.parlamentar ?? "", emenda: polo.emenda ?? "",
        aditivo1_objeto: p1?.objeto ?? "", aditivo1_data: p1?.data_assinatura ?? "",
        aditivo2_objeto: p2?.objeto ?? "", aditivo2_data: p2?.data_assinatura ?? "",
        responsavel_nome: polo.responsavel_nome ?? "", responsavel_email: polo.responsavel_email ?? "",
        responsavel_telefone: polo.responsavel_telefone ?? "",
        representante_legal_rg: polo.representante_legal_rg ?? "",
        representante_legal_endereco: polo.representante_legal_endereco ?? "",
        representante_legal_bairro: polo.representante_legal_bairro ?? "",
        representante_legal_cidade: polo.representante_legal_cidade ?? "",
      });
      setLatitude(polo.latitude);
      setLongitude(polo.longitude);
    }
  }, [polo]);

  const salvarMutation = useMutation({
    mutationFn: (dadosForm: typeof FORM_VAZIO) => {
      const termos_aditivos = [
        dadosForm.aditivo1_objeto || dadosForm.aditivo1_data
          ? { numero: "PRIMEIRO", objeto: dadosForm.aditivo1_objeto, data_assinatura: dadosForm.aditivo1_data || null }
          : null,
        dadosForm.aditivo2_objeto || dadosForm.aditivo2_data
          ? { numero: "SEGUNDO", objeto: dadosForm.aditivo2_objeto, data_assinatura: dadosForm.aditivo2_data || null }
          : null,
      ].filter(Boolean);
      return api.patch(`/polos/${polo!.id}`, {
        nome: dadosForm.nome,
        codigo: dadosForm.codigo.trim() || null,
        endereco: dadosForm.endereco || null,
        horario_funcionamento: dadosForm.horario_funcionamento || null,
        status: dadosForm.status,
        processo_sei: dadosForm.processo_sei || null, termo_fomento_numero: dadosForm.termo_fomento_numero || null,
        nome_entidade: dadosForm.nome_entidade || null, cnpj: dadosForm.cnpj || null,
        representante_legal_nome: dadosForm.representante_legal_nome || null,
        representante_legal_cpf: dadosForm.representante_legal_cpf || null, objeto: dadosForm.objeto || null,
        vigencia_inicio: dadosForm.vigencia_inicio || null, vigencia_fim: dadosForm.vigencia_fim || null,
        valor_pactuado: dadosForm.valor_pactuado || null, valor_executado: dadosForm.valor_executado || null,
        parlamentar: dadosForm.parlamentar || null, emenda: dadosForm.emenda || null,
        termos_aditivos,
        responsavel_nome: dadosForm.responsavel_nome || null, responsavel_email: dadosForm.responsavel_email || null,
        responsavel_telefone: dadosForm.responsavel_telefone || null,
        representante_legal_rg: dadosForm.representante_legal_rg || null,
        representante_legal_endereco: dadosForm.representante_legal_endereco || null,
        representante_legal_bairro: dadosForm.representante_legal_bairro || null,
        representante_legal_cidade: dadosForm.representante_legal_cidade || null,
        latitude, longitude,
      });
    },
    onSuccess: () => onSalvo(),
    onError: (err: any) => {
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
          <h3 className="text-sm font-semibold text-brand-dark mb-3">
            Dados da parceria (Termo de Fomento)
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Processo SEI" value={form.processo_sei} onChange={(e) => set("processo_sei", e.target.value)} />
            <Input label="Termo de Fomento" value={form.termo_fomento_numero} onChange={(e) => set("termo_fomento_numero", e.target.value)} />
            <div className="sm:col-span-2">
              <Input label="Entidade parceira" value={form.nome_entidade} onChange={(e) => set("nome_entidade", e.target.value)} />
            </div>
            <Input label="CNPJ" value={form.cnpj} onChange={(e) => set("cnpj", e.target.value)} />
            <Input label="Representante legal" value={form.representante_legal_nome} onChange={(e) => set("representante_legal_nome", e.target.value)} />
            <Input label="CPF do representante" value={form.representante_legal_cpf} onChange={(e) => set("representante_legal_cpf", e.target.value)} />
            <div className="sm:col-span-2">
              <Input label="Objeto" value={form.objeto} onChange={(e) => set("objeto", e.target.value)} />
            </div>
            <Input label="Vigência — início" type="date" value={form.vigencia_inicio} onChange={(e) => set("vigencia_inicio", e.target.value)} />
            <Input label="Vigência — fim" type="date" value={form.vigencia_fim} onChange={(e) => set("vigencia_fim", e.target.value)} />
            <Input label="Valor pactuado" placeholder="R$ 0,00" value={form.valor_pactuado} onChange={(e) => set("valor_pactuado", e.target.value)} />
            <Input label="Valor executado" placeholder="R$ 0,00" value={form.valor_executado} onChange={(e) => set("valor_executado", e.target.value)} />
            <Input label="Parlamentar" value={form.parlamentar} onChange={(e) => set("parlamentar", e.target.value)} />
            <Input label="Emenda" value={form.emenda} onChange={(e) => set("emenda", e.target.value)} />
          </div>
        </div>

        <div className="border-t border-gray-100 pt-4">
          <h3 className="text-sm font-semibold text-brand-dark mb-1">Termos aditivos</h3>
          <p className="text-xs text-gray-400 mb-3">Até 2 — Primeiro e Segundo, como no modelo oficial.</p>
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-4 items-end">
              <Input label="Primeiro aditivo — objeto" value={form.aditivo1_objeto} onChange={(e) => set("aditivo1_objeto", e.target.value)} />
              <Input label="Data da assinatura" type="date" value={form.aditivo1_data} onChange={(e) => set("aditivo1_data", e.target.value)} />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-4 items-end">
              <Input label="Segundo aditivo — objeto" value={form.aditivo2_objeto} onChange={(e) => set("aditivo2_objeto", e.target.value)} />
              <Input label="Data da assinatura" type="date" value={form.aditivo2_data} onChange={(e) => set("aditivo2_data", e.target.value)} />
            </div>
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
          <h3 className="text-sm font-semibold text-brand-dark mb-1">Dados pessoais do representante legal</h3>
          <p className="text-xs text-gray-400 mb-3">Usado no Termo de Responsabilidade — nome e CPF já estão na seção "Dados da parceria" acima.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="RG" value={form.representante_legal_rg} onChange={(e) => set("representante_legal_rg", e.target.value)} />
            <div className="sm:col-span-2">
              <Input label="Endereço" value={form.representante_legal_endereco} onChange={(e) => set("representante_legal_endereco", e.target.value)} />
            </div>
            <Input label="Bairro" value={form.representante_legal_bairro} onChange={(e) => set("representante_legal_bairro", e.target.value)} />
            <Input label="Cidade" value={form.representante_legal_cidade} onChange={(e) => set("representante_legal_cidade", e.target.value)} />
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
              <p className="text-xs text-gray-400">Este polo ainda não tem um acesso de Gestor de Polo vinculado.</p>
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
                  label="Senha"
                  type="password"
                  minLength={8}
                  hint="Mínimo de 8 caracteres."
                  value={gestorForm.senha}
                  onChange={(e) => setGestorForm((f) => ({ ...f, senha: e.target.value }))}
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
