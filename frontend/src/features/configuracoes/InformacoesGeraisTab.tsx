import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { ConfiguracaoGeral } from "@/types";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/toast/ToastContext";

const FORM_INICIAL = {
  nome_projeto: "", numero_convenio: "", data_inicio_projeto: "", data_fim_projeto: "",
  processo_sei: "", termo_fomento_numero: "", nome_entidade: "", cnpj: "",
  objeto: "", vigencia_inicio: "", vigencia_fim: "", valor_pactuado: "", valor_executado: "",
  parlamentar: "", emenda: "",
  aditivo1_objeto: "", aditivo1_data: "",
  aditivo2_objeto: "", aditivo2_data: "",
};

export function InformacoesGeraisTab() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [form, setForm] = useState(FORM_INICIAL);

  const { data: config, isLoading } = useQuery({
    queryKey: ["configuracao-geral"],
    queryFn: () => api.get<ConfiguracaoGeral | null>("/configuracao-geral").then((r) => r.data),
  });

  const [configAnterior, setConfigAnterior] = useState(config);
  if (config !== configAnterior) {
    setConfigAnterior(config);
    if (config) {
      const p1 = config.termos_aditivos.find((a) => a.numero === "PRIMEIRO");
      const p2 = config.termos_aditivos.find((a) => a.numero === "SEGUNDO");
      setForm({
        nome_projeto: config.nome_projeto ?? "",
        numero_convenio: config.numero_convenio ?? "",
        data_inicio_projeto: config.data_inicio_projeto ?? "",
        data_fim_projeto: config.data_fim_projeto ?? "",
        processo_sei: config.processo_sei ?? "", termo_fomento_numero: config.termo_fomento_numero ?? "",
        nome_entidade: config.nome_entidade ?? "", cnpj: config.cnpj ?? "",
        objeto: config.objeto ?? "",
        vigencia_inicio: config.vigencia_inicio ?? "", vigencia_fim: config.vigencia_fim ?? "",
        valor_pactuado: config.valor_pactuado ?? "", valor_executado: config.valor_executado ?? "",
        parlamentar: config.parlamentar ?? "", emenda: config.emenda ?? "",
        aditivo1_objeto: p1?.objeto ?? "", aditivo1_data: p1?.data_assinatura ?? "",
        aditivo2_objeto: p2?.objeto ?? "", aditivo2_data: p2?.data_assinatura ?? "",
      });
    }
  }

  const salvarMutation = useMutation({
    mutationFn: (dadosForm: typeof FORM_INICIAL) => {
      const termos_aditivos = [
        dadosForm.aditivo1_objeto || dadosForm.aditivo1_data
          ? { numero: "PRIMEIRO", objeto: dadosForm.aditivo1_objeto, data_assinatura: dadosForm.aditivo1_data || null }
          : null,
        dadosForm.aditivo2_objeto || dadosForm.aditivo2_data
          ? { numero: "SEGUNDO", objeto: dadosForm.aditivo2_objeto, data_assinatura: dadosForm.aditivo2_data || null }
          : null,
      ].filter(Boolean);
      return api.patch("/configuracao-geral", {
        nome_projeto: dadosForm.nome_projeto || null,
        numero_convenio: dadosForm.numero_convenio || null,
        data_inicio_projeto: dadosForm.data_inicio_projeto || null,
        data_fim_projeto: dadosForm.data_fim_projeto || null,
        processo_sei: dadosForm.processo_sei || null, termo_fomento_numero: dadosForm.termo_fomento_numero || null,
        nome_entidade: dadosForm.nome_entidade || null, cnpj: dadosForm.cnpj || null,
        objeto: dadosForm.objeto || null,
        vigencia_inicio: dadosForm.vigencia_inicio || null, vigencia_fim: dadosForm.vigencia_fim || null,
        valor_pactuado: dadosForm.valor_pactuado || null, valor_executado: dadosForm.valor_executado || null,
        parlamentar: dadosForm.parlamentar || null, emenda: dadosForm.emenda || null,
        termos_aditivos,
      });
    },
    onSuccess: () => {
      toast.success("Informações gerais salvas — já valem para os próximos relatórios exportados.");
      queryClient.invalidateQueries({ queryKey: ["configuracao-geral"] });
    },
    onError: (err: unknown) => toast.error(mensagemErroApi(err, "Erro ao salvar as informações gerais.")),
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    salvarMutation.mutate(form);
  }

  function set<K extends keyof typeof FORM_INICIAL>(campo: K, valor: string) {
    setForm((f) => ({ ...f, [campo]: valor }));
  }

  if (isLoading) return <Spinner label="Carregando…" />;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <p className="text-sm text-gray-500">
        Esses dados aparecem no rodapé de todos os relatórios exportados pelo sistema. Podem ser alterados a
        qualquer momento.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Input label="Nome do projeto" value={form.nome_projeto} onChange={(e) => set("nome_projeto", e.target.value)} />
        <Input label="Número do convênio" value={form.numero_convenio} onChange={(e) => set("numero_convenio", e.target.value)} />
        <Input
          label="Data de início do projeto" type="date" value={form.data_inicio_projeto}
          onChange={(e) => set("data_inicio_projeto", e.target.value)}
        />
        <Input
          label="Data final do projeto" type="date" value={form.data_fim_projeto}
          onChange={(e) => set("data_fim_projeto", e.target.value)}
        />
      </div>

      <div className="border-t border-gray-100 pt-4">
        <h3 className="text-sm font-semibold text-brand-dark mb-1">Termo de Fomento</h3>
        <p className="text-xs text-gray-400 mb-3">
          Dados da entidade parceira — únicos pro projeto inteiro, não mudam de polo pra polo. Usados na
          Ficha de Execução, na Planilha de Núcleos e na Lista de Presença. O representante legal fica no
          cadastro de cada Polo (Polos &gt; Editar), já que polos diferentes podem ter representantes diferentes.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input label="Processo SEI" value={form.processo_sei} onChange={(e) => set("processo_sei", e.target.value)} />
          <Input label="Termo de Fomento" value={form.termo_fomento_numero} onChange={(e) => set("termo_fomento_numero", e.target.value)} />
          <div className="sm:col-span-2">
            <Input label="Entidade parceira" value={form.nome_entidade} onChange={(e) => set("nome_entidade", e.target.value)} />
          </div>
          <Input label="CNPJ" value={form.cnpj} onChange={(e) => set("cnpj", e.target.value)} />
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

      <Button type="submit" disabled={salvarMutation.isPending}>
        {salvarMutation.isPending ? "Salvando…" : "Salvar"}
      </Button>
    </form>
  );
}
