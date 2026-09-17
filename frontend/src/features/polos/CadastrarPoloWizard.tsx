import { FormEvent, useState } from "react";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/components/ui/toast/ToastContext";
import { maskCPF, maskTelefone } from "@/lib/masks";
import { EnderecoMapaField } from "./EnderecoMapaField";

const FORM_VAZIO = {
  nome: "", codigo: "", endereco: "", horario_funcionamento: "",
  representante_legal_nome: "", representante_legal_cpf: "", representante_legal_rg: "",
  responsavel_nome: "", responsavel_email: "", responsavel_telefone: "",
  gestor_nome: "", gestor_email: "", gestor_telefone: "", gestor_cpf: "",
};

const TOTAL_ETAPAS = 4;
const TITULOS_ETAPA: Record<number, string> = {
  1: "Dados do polo",
  2: "Representante legal",
  3: "Contato do núcleo",
  4: "Acesso do Gestor de Polo",
};

export function CadastrarPoloWizard({ onCadastrado, style }: { onCadastrado: () => void; style?: React.CSSProperties }) {
  const toast = useToast();
  const [etapa, setEtapa] = useState(1);
  const [form, setForm] = useState(FORM_VAZIO);
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [salvando, setSalvando] = useState(false);

  function set<K extends keyof typeof FORM_VAZIO>(campo: K, valor: string) {
    setForm((f) => ({ ...f, [campo]: valor }));
  }

  function continuar() {
    if (etapa === 1 && !form.nome.trim()) {
      toast.error("Informe o nome do polo para continuar.");
      return;
    }
    setEtapa((e) => Math.min(e + 1, TOTAL_ETAPAS));
  }

  function voltar() {
    setEtapa((e) => Math.max(e - 1, 1));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form.gestor_nome.trim() || !form.gestor_email.trim()) {
      toast.error("Informe nome e e-mail do gestor de polo para continuar.");
      return;
    }

    setSalvando(true);

    let poloId: string;
    try {
      const { data } = await api.post("/polos", {
        nome: form.nome,
        codigo: form.codigo.trim() || null,
        endereco: form.endereco || null,
        horario_funcionamento: form.horario_funcionamento || null,
        representante_legal_nome: form.representante_legal_nome || null,
        representante_legal_cpf: form.representante_legal_cpf || null,
        representante_legal_rg: form.representante_legal_rg || null,
        responsavel_nome: form.responsavel_nome || null, responsavel_email: form.responsavel_email || null,
        responsavel_telefone: form.responsavel_telefone || null,
        latitude, longitude,
      });
      poloId = data.id;
    } catch (err: unknown) {
      toast.error(mensagemErroApi(err, "Erro ao cadastrar polo."));
      setSalvando(false);
      return;
    }

    // O polo já existe a partir daqui — uma falha na criação do gestor não é
    // mais uma falha total: o polo é real e deve aparecer na lista mesmo assim.
    try {
      const { data: gestor } = await api.post("/usuarios", {
        nome: form.gestor_nome,
        email: form.gestor_email,
        telefone: form.gestor_telefone || null,
        cpf: form.gestor_cpf || null,
        perfil: "GESTOR_POLO",
        polo_id: poloId,
      });
      await api.patch(`/polos/${poloId}`, { gestor_responsavel_id: gestor.id });
      toast.success("Polo cadastrado. Enviamos um email para o gestor definir a própria senha.");
    } catch (err: unknown) {
      toast.error(
        `Polo cadastrado, mas houve um problema ao criar o acesso do gestor: ${
          mensagemErroApi(err, "erro desconhecido")
        }. Você pode tentar novamente em "Editar Polo".`
      );
    }

    setForm(FORM_VAZIO);
    setLatitude(null);
    setLongitude(null);
    setEtapa(1);
    onCadastrado();
    setSalvando(false);
  }

  return (
    <Card
      title="Cadastrar polo"
      subtitle={TITULOS_ETAPA[etapa]}
      actions={<Badge variant="brand">Etapa {etapa} de {TOTAL_ETAPAS}</Badge>}
      className="animate-fade-in-up"
      style={style}
    >
      <form onSubmit={handleSubmit}>
        {etapa === 1 && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-2">
              <Input label="Nome" value={form.nome} onChange={(e) => set("nome", e.target.value)} required />
            </div>
            <Input
              label="Código"
              placeholder="ex.: ZN01"
              value={form.codigo}
              onChange={(e) => set("codigo", e.target.value.toUpperCase())}
              maxLength={20}
              hint="Identificador curto, usado no lugar do ID nas telas."
            />
            <div className="sm:col-span-3">
              <Input label="Endereço" value={form.endereco} onChange={(e) => set("endereco", e.target.value)} />
            </div>
            <div className="sm:col-span-3">
              <Input
                label="Horário de funcionamento"
                placeholder="ex.: Seg a Sex, 08h às 18h"
                value={form.horario_funcionamento}
                onChange={(e) => set("horario_funcionamento", e.target.value)}
              />
            </div>
            <div className="sm:col-span-3">
              <EnderecoMapaField
                onEnderecoChange={(endereco) => set("endereco", endereco)}
                latitude={latitude}
                longitude={longitude}
                onChange={(lat, lon) => { setLatitude(lat); setLongitude(lon); }}
              />
            </div>
          </div>
        )}

        {etapa === 2 && (
          <div className="space-y-4">
            <p className="text-xs text-gray-400">Usado no Termo de Responsabilidade. CPF é opcional.</p>
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
        )}

        {etapa === 3 && (
          <div className="space-y-4">
            <p className="text-xs text-gray-400">Usado na Identificação do Núcleo da Ficha de Execução.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input label="Responsável" value={form.responsavel_nome} onChange={(e) => set("responsavel_nome", e.target.value)} />
              <Input label="Telefone" value={form.responsavel_telefone} onChange={(e) => set("responsavel_telefone", e.target.value)} />
              <div className="sm:col-span-2">
                <Input label="E-mail" value={form.responsavel_email} onChange={(e) => set("responsavel_email", e.target.value)} />
              </div>
            </div>
          </div>
        )}

        {etapa === 4 && (
          <div className="space-y-4">
            <p className="text-xs text-gray-400">
              O gestor recebe por email um link para definir a própria senha — ninguém mais precisa conhecê-la.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <Input label="Nome do gestor" value={form.gestor_nome} onChange={(e) => set("gestor_nome", e.target.value)} required />
              </div>
              <div className="sm:col-span-2">
                <Input label="E-mail" type="email" value={form.gestor_email} onChange={(e) => set("gestor_email", e.target.value)} required />
              </div>
              <Input
                label="Telefone" value={form.gestor_telefone} inputMode="tel"
                onChange={(e) => set("gestor_telefone", maskTelefone(e.target.value))}
              />
              <Input
                label="CPF" value={form.gestor_cpf} inputMode="numeric"
                onChange={(e) => set("gestor_cpf", maskCPF(e.target.value))}
              />
            </div>
          </div>
        )}

        <div className="flex gap-3 mt-6">
          {etapa > 1 && (
            <Button type="button" variant="secondary" onClick={voltar}>Voltar</Button>
          )}
          {etapa < TOTAL_ETAPAS ? (
            <Button key="continuar" type="button" onClick={continuar}>Continuar</Button>
          ) : (
            <Button key="submit" type="submit" disabled={salvando}>{salvando ? "Cadastrando…" : "Cadastrar polo"}</Button>
          )}
        </div>
      </form>
    </Card>
  );
}
