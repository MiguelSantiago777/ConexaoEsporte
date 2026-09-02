import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { ConfiguracaoGeral } from "@/types";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/toast/ToastContext";

const FORM_INICIAL = { nome_projeto: "", numero_convenio: "", data_inicio_projeto: "", data_fim_projeto: "" };

export function InformacoesGeraisTab() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [form, setForm] = useState(FORM_INICIAL);

  const { data: config, isLoading } = useQuery({
    queryKey: ["configuracao-geral"],
    queryFn: () => api.get<ConfiguracaoGeral | null>("/configuracao-geral").then((r) => r.data),
  });

  useEffect(() => {
    if (config) {
      setForm({
        nome_projeto: config.nome_projeto ?? "",
        numero_convenio: config.numero_convenio ?? "",
        data_inicio_projeto: config.data_inicio_projeto ?? "",
        data_fim_projeto: config.data_fim_projeto ?? "",
      });
    }
  }, [config]);

  const salvarMutation = useMutation({
    mutationFn: (dadosForm: typeof FORM_INICIAL) =>
      api.patch("/configuracao-geral", {
        nome_projeto: dadosForm.nome_projeto || null,
        numero_convenio: dadosForm.numero_convenio || null,
        data_inicio_projeto: dadosForm.data_inicio_projeto || null,
        data_fim_projeto: dadosForm.data_fim_projeto || null,
      }),
    onSuccess: () => {
      toast.success("Informações gerais salvas — já valem para os próximos relatórios exportados.");
      queryClient.invalidateQueries({ queryKey: ["configuracao-geral"] });
    },
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao salvar as informações gerais.")),
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    salvarMutation.mutate(form);
  }

  if (isLoading) return <Spinner label="Carregando…" />;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <p className="text-sm text-gray-500">
        Esses dados aparecem no rodapé de todos os relatórios exportados pelo sistema. Podem ser alterados a
        qualquer momento.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Input
          label="Nome do projeto"
          value={form.nome_projeto}
          onChange={(e) => setForm({ ...form, nome_projeto: e.target.value })}
        />
        <Input
          label="Número do convênio"
          value={form.numero_convenio}
          onChange={(e) => setForm({ ...form, numero_convenio: e.target.value })}
        />
        <Input
          label="Data de início do projeto"
          type="date"
          value={form.data_inicio_projeto}
          onChange={(e) => setForm({ ...form, data_inicio_projeto: e.target.value })}
        />
        <Input
          label="Data final do projeto"
          type="date"
          value={form.data_fim_projeto}
          onChange={(e) => setForm({ ...form, data_fim_projeto: e.target.value })}
        />
      </div>
      <Button type="submit" disabled={salvarMutation.isPending}>
        {salvarMutation.isPending ? "Salvando…" : "Salvar"}
      </Button>
    </form>
  );
}
