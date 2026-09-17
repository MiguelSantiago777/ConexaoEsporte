import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { AnexoGeral, Polo, TipoLancamentoFinanceiro } from "@/types";
import {
  criarLancamento,
  definirVisibilidadeAnexo,
  listarLancamentos,
  removerLancamento,
} from "./transparenciaService";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Tabs } from "@/components/ui/Tabs";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Badge } from "@/components/ui/Badge";
import { TrashIcon } from "@/components/ui/icons";
import { useToast } from "@/components/ui/toast/ToastContext";
import { formatarData, formatarMoeda } from "@/lib/format";

const CATEGORIAS_SUGERIDAS = [
  "Recursos Humanos", "Material Esportivo", "Uniformes", "Alimentação",
  "Transporte", "Infraestrutura", "Administrativo", "Outros",
];

const FORM_INICIAL = {
  categoria: "", tipo: "REPASSE" as TipoLancamentoFinanceiro, valor: "", data_lancamento: "",
  descricao: "", polo_id: "",
};

/** Exclusivo do MASTER: alimenta os dois dados que a página pública do
 * Portal Transparência (`/transparencia`) não consegue derivar sozinha do
 * resto do sistema — os Lançamentos Financeiros do Termo de Fomento (não
 * existe outro cadastro de valores no sistema) e quais Anexos Gerais devem
 * ficar visíveis sem login. */
export function TransparenciaAdminPage() {
  const [aba, setAba] = useState("financeiro");
  return (
    <div className="space-y-6">
      <PageHeader
        title="Portal Transparência"
        subtitle="Lançamentos financeiros e documentos exibidos na página pública do Termo de Fomento."
      />
      <Tabs
        abas={[
          { id: "financeiro", label: "Lançamentos Financeiros" },
          { id: "documentos", label: "Documentos Públicos" },
        ]}
        ativa={aba} onChange={setAba}
      >
        {aba === "financeiro" ? <AbaFinanceiro /> : <AbaDocumentos />}
      </Tabs>
    </div>
  );
}

function AbaFinanceiro() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [form, setForm] = useState(FORM_INICIAL);

  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
  });
  const polosPorId = useMemo(() => new Map(polos.map((p) => [p.id, p.nome])), [polos]);

  const { data: lancamentos = [], isLoading } = useQuery({
    queryKey: ["transparencia-lancamentos"],
    queryFn: () => listarLancamentos(),
  });

  const criar = useMutation({
    mutationFn: () =>
      criarLancamento({
        categoria: form.categoria, tipo: form.tipo, valor: Number(form.valor),
        data_lancamento: form.data_lancamento, descricao: form.descricao || null,
        polo_id: form.polo_id || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transparencia-lancamentos"] });
      setForm(FORM_INICIAL);
      toast.success("Lançamento registrado.");
    },
    onError: (err) => toast.error(mensagemErroApi(err, "Não foi possível registrar o lançamento.")),
  });

  const remover = useMutation({
    mutationFn: (id: string) => removerLancamento(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transparencia-lancamentos"] });
      toast.success("Lançamento removido.");
    },
    onError: (err) => toast.error(mensagemErroApi(err, "Não foi possível remover o lançamento.")),
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    criar.mutate();
  }

  return (
    <div className="space-y-6">
      <Card title="Novo lançamento">
        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="Categoria" value={form.categoria} required
            onChange={(e) => setForm((f) => ({ ...f, categoria: e.target.value }))}
          >
            <option value="">Selecione</option>
            {CATEGORIAS_SUGERIDAS.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </Select>
          <Select
            label="Tipo" value={form.tipo} required
            onChange={(e) => setForm((f) => ({ ...f, tipo: e.target.value as TipoLancamentoFinanceiro }))}
          >
            <option value="REPASSE">Repasse</option>
            <option value="EXECUCAO">Execução</option>
          </Select>
          <Input
            label="Valor (R$)" type="number" step="0.01" min="0.01" value={form.valor} required
            onChange={(e) => setForm((f) => ({ ...f, valor: e.target.value }))}
          />
          <Input
            label="Data" type="date" value={form.data_lancamento} required
            onChange={(e) => setForm((f) => ({ ...f, data_lancamento: e.target.value }))}
          />
          <Select
            label="Polo (opcional)" value={form.polo_id}
            onChange={(e) => setForm((f) => ({ ...f, polo_id: e.target.value }))}
          >
            <option value="">Geral do convênio</option>
            {polos.map((p) => (
              <option key={p.id} value={p.id}>{p.nome}</option>
            ))}
          </Select>
          <Input
            label="Descrição (opcional)" value={form.descricao}
            onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))}
          />
          <div className="sm:col-span-2">
            <Button type="submit" disabled={criar.isPending}>
              {criar.isPending ? "Salvando…" : "Registrar lançamento"}
            </Button>
          </div>
        </form>
      </Card>

      <Card title="Lançamentos registrados">
        {isLoading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : lancamentos.length === 0 ? (
          <EmptyState message="Nenhum lançamento registrado ainda." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500 border-b border-slate-200">
                  <th className="py-2 pr-4">Data</th>
                  <th className="py-2 pr-4">Categoria</th>
                  <th className="py-2 pr-4">Tipo</th>
                  <th className="py-2 pr-4">Polo</th>
                  <th className="py-2 pr-4 text-right">Valor</th>
                  <th className="py-2 pr-4" />
                </tr>
              </thead>
              <tbody>
                {lancamentos.map((l) => (
                  <tr key={l.id} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-4 text-ink whitespace-nowrap">{formatarData(l.data_lancamento)}</td>
                    <td className="py-2 pr-4 text-ink">{l.categoria}</td>
                    <td className="py-2 pr-4">
                      <Badge variant={l.tipo === "REPASSE" ? "brand" : "court"}>
                        {l.tipo === "REPASSE" ? "Repasse" : "Execução"}
                      </Badge>
                    </td>
                    <td className="py-2 pr-4 text-slate-500">
                      {l.polo_id ? polosPorId.get(l.polo_id) ?? "—" : "Geral"}
                    </td>
                    <td className="py-2 pr-4 text-right font-mono tabular-nums text-ink">{formatarMoeda(l.valor)}</td>
                    <td className="py-2 pr-4 text-right">
                      <button
                        type="button"
                        onClick={() => {
                          if (window.confirm("Remover este lançamento?")) remover.mutate(l.id);
                        }}
                        className="text-slate-400 hover:text-danger transition-colors" aria-label="Remover lançamento"
                      >
                        <TrashIcon />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

function AbaDocumentos() {
  const toast = useToast();
  const queryClient = useQueryClient();

  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
  });
  const polosPorId = useMemo(() => new Map(polos.map((p) => [p.id, p.nome])), [polos]);

  const { data: anexos = [], isLoading } = useQuery({
    queryKey: ["anexos-gerais-todos"],
    queryFn: () => api.get<AnexoGeral[]>("/anexos-gerais").then((r) => r.data),
  });

  const alternar = useMutation({
    mutationFn: ({ id, publico }: { id: string; publico: boolean }) => definirVisibilidadeAnexo(id, publico),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["anexos-gerais-todos"] });
      toast.success("Visibilidade atualizada.");
    },
    onError: (err) => toast.error(mensagemErroApi(err, "Não foi possível atualizar a visibilidade.")),
  });

  return (
    <Card
      title="Anexos Gerais" subtitle="Marque quais anexos aparecem no Portal Transparência (página pública, sem login)."
    >
      {isLoading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : anexos.length === 0 ? (
        <EmptyState message="Nenhum anexo cadastrado ainda. Envie documentos em Anexos Gerais." />
      ) : (
        <ul className="divide-y divide-slate-100">
          {anexos.map((anexo) => (
            <li key={anexo.id} className="flex items-center justify-between gap-4 py-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-ink truncate">{anexo.titulo}</p>
                <p className="text-xs text-slate-500">
                  {polosPorId.get(anexo.polo_id) ?? "—"} · {anexo.nome_arquivo}
                </p>
              </div>
              <label className="flex items-center gap-2 shrink-0 cursor-pointer select-none">
                <span className="text-xs text-slate-500">{anexo.publico ? "Público" : "Interno"}</span>
                <input
                  type="checkbox" checked={anexo.publico} className="sr-only peer"
                  onChange={(e) => alternar.mutate({ id: anexo.id, publico: e.target.checked })}
                />
                <span className="relative w-9 h-5 bg-slate-300 rounded-full peer-checked:bg-court transition-colors">
                  <span className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
                </span>
              </label>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
