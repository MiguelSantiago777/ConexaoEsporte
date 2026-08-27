import { FormEvent, useState } from "react";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/components/ui/toast/ToastContext";
import { EnderecoMapaField } from "./EnderecoMapaField";

const FORM_VAZIO = {
  nome: "", codigo: "", endereco: "", horario_funcionamento: "",
  processo_sei: "", termo_fomento_numero: "", nome_entidade: "", cnpj: "",
  representante_legal_nome: "", representante_legal_cpf: "", objeto: "",
  vigencia_inicio: "", vigencia_fim: "", valor_pactuado: "", valor_executado: "",
  parlamentar: "", emenda: "",
  aditivo1_objeto: "", aditivo1_data: "",
  aditivo2_objeto: "", aditivo2_data: "",
  responsavel_nome: "", responsavel_email: "", responsavel_telefone: "",
  representante_legal_rg: "", representante_legal_endereco: "",
  representante_legal_bairro: "", representante_legal_cidade: "",
  gestor_nome: "", gestor_email: "", gestor_senha: "",
};

const TOTAL_ETAPAS = 6;
const TITULOS_ETAPA: Record<number, string> = {
  1: "Dados do polo",
  2: "Dados da parceria (Termo de Fomento)",
  3: "Termos aditivos",
  4: "Contato do núcleo",
  5: "Dados pessoais do representante legal (Termo de Responsabilidade)",
  6: "Acesso do Gestor de Polo",
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
    if (!form.gestor_nome.trim() || !form.gestor_email.trim() || !form.gestor_senha) {
      toast.error("Informe nome, e-mail e senha do gestor de polo para continuar.");
      return;
    }
    if (form.gestor_senha.length < 8) {
      toast.error("A senha do gestor deve ter pelo menos 8 caracteres.");
      return;
    }

    setSalvando(true);
    const termos_aditivos = [
      form.aditivo1_objeto || form.aditivo1_data
        ? { numero: "PRIMEIRO", objeto: form.aditivo1_objeto, data_assinatura: form.aditivo1_data || null }
        : null,
      form.aditivo2_objeto || form.aditivo2_data
        ? { numero: "SEGUNDO", objeto: form.aditivo2_objeto, data_assinatura: form.aditivo2_data || null }
        : null,
    ].filter(Boolean);

    let poloId: string;
    try {
      const { data } = await api.post("/polos", {
        nome: form.nome,
        codigo: form.codigo.trim() || null,
        endereco: form.endereco || null,
        horario_funcionamento: form.horario_funcionamento || null,
        processo_sei: form.processo_sei || null, termo_fomento_numero: form.termo_fomento_numero || null,
        nome_entidade: form.nome_entidade || null, cnpj: form.cnpj || null,
        representante_legal_nome: form.representante_legal_nome || null,
        representante_legal_cpf: form.representante_legal_cpf || null, objeto: form.objeto || null,
        vigencia_inicio: form.vigencia_inicio || null, vigencia_fim: form.vigencia_fim || null,
        valor_pactuado: form.valor_pactuado || null, valor_executado: form.valor_executado || null,
        parlamentar: form.parlamentar || null, emenda: form.emenda || null,
        termos_aditivos,
        responsavel_nome: form.responsavel_nome || null, responsavel_email: form.responsavel_email || null,
        responsavel_telefone: form.responsavel_telefone || null,
        representante_legal_rg: form.representante_legal_rg || null,
        representante_legal_endereco: form.representante_legal_endereco || null,
        representante_legal_bairro: form.representante_legal_bairro || null,
        representante_legal_cidade: form.representante_legal_cidade || null,
        latitude, longitude,
      });
      poloId = data.id;
    } catch (err: any) {
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
        senha: form.gestor_senha,
        perfil: "GESTOR_POLO",
        polo_id: poloId,
      });
      await api.patch(`/polos/${poloId}`, { gestor_responsavel_id: gestor.id });
      toast.success("Polo e acesso do gestor cadastrados com sucesso.");
    } catch (err: any) {
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
        )}

        {etapa === 3 && (
          <div className="space-y-4">
            <p className="text-xs text-gray-400">Até 2 — Primeiro e Segundo, como no modelo oficial. Pode deixar em branco e preencher depois.</p>
            <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-4 items-end">
              <Input label="Primeiro aditivo — objeto" value={form.aditivo1_objeto} onChange={(e) => set("aditivo1_objeto", e.target.value)} />
              <Input label="Data da assinatura" type="date" value={form.aditivo1_data} onChange={(e) => set("aditivo1_data", e.target.value)} />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-4 items-end">
              <Input label="Segundo aditivo — objeto" value={form.aditivo2_objeto} onChange={(e) => set("aditivo2_objeto", e.target.value)} />
              <Input label="Data da assinatura" type="date" value={form.aditivo2_data} onChange={(e) => set("aditivo2_data", e.target.value)} />
            </div>
          </div>
        )}

        {etapa === 4 && (
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

        {etapa === 5 && (
          <div className="space-y-4">
            <p className="text-xs text-gray-400">Dados pessoais do representante legal para o Termo de Responsabilidade — nome e CPF já preenchidos na etapa 2.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input label="RG" value={form.representante_legal_rg} onChange={(e) => set("representante_legal_rg", e.target.value)} />
              <div className="sm:col-span-2">
                <Input label="Endereço" value={form.representante_legal_endereco} onChange={(e) => set("representante_legal_endereco", e.target.value)} />
              </div>
              <Input label="Bairro" value={form.representante_legal_bairro} onChange={(e) => set("representante_legal_bairro", e.target.value)} />
              <Input label="Cidade" value={form.representante_legal_cidade} onChange={(e) => set("representante_legal_cidade", e.target.value)} />
            </div>
          </div>
        )}

        {etapa === 6 && (
          <div className="space-y-4">
            <p className="text-xs text-gray-400">
              Essas credenciais serão usadas pelo Gestor de Polo para acessar o sistema. Obrigatório.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <Input label="Nome do gestor" value={form.gestor_nome} onChange={(e) => set("gestor_nome", e.target.value)} required />
              </div>
              <div className="sm:col-span-2">
                <Input label="E-mail" type="email" value={form.gestor_email} onChange={(e) => set("gestor_email", e.target.value)} required />
              </div>
              <Input
                label="Senha"
                type="password"
                minLength={8}
                hint="Mínimo de 8 caracteres."
                value={form.gestor_senha}
                onChange={(e) => set("gestor_senha", e.target.value)}
                required
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
