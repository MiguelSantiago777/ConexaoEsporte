import { FormEvent, useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { EntregaMaterial, ItemEntrega, Pagina, Polo } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";
import { Paginacao } from "@/components/ui/Paginacao";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { formatarData } from "@/lib/format";
import { baixarExportacao } from "@/features/fichas-execucao/FichasExecucaoPage";
import { useAuth } from "@/features/auth/AuthContext";

const ITEM_VAZIO: ItemEntrega = { descricao: "", quantidade: "" };
const TAMANHO_PAGINA = 10;

export function EntregasMateriaisPage() {
  const { usuario } = useAuth();
  const toast = useToast();
  const ehMaster = usuario?.perfil === "MASTER";

  const queryClient = useQueryClient();
  const [pagina, setPagina] = useState(1);
  const entregasQueryKey = ["entregas-materiais", "pagina", pagina];
  const { data: paginaEntregas, isLoading: carregando } = useQuery({
    queryKey: entregasQueryKey,
    queryFn: () =>
      api
        .get<Pagina<EntregaMaterial>>("/entregas-materiais", { params: { pagina, tamanho_pagina: TAMANHO_PAGINA } })
        .then((r) => r.data),
  });
  const entregas = paginaEntregas?.itens ?? [];
  const totalEntregas = paginaEntregas?.total ?? 0;
  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
  });

  const [salvando, setSalvando] = useState(false);
  const [exportando, setExportando] = useState<string | null>(null);
  const [poloId, setPoloId] = useState("");
  const [dataEntrega, setDataEntrega] = useState("");
  const [entreguePor, setEntreguePor] = useState("");
  const [itens, setItens] = useState<ItemEntrega[]>([{ ...ITEM_VAZIO }]);

  useEffect(() => {
    if (!ehMaster && usuario?.polo_id) setPoloId(usuario.polo_id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [usuario]);

  function poloNome(id: string) {
    return polos.find((p) => p.id === id)?.nome ?? "—";
  }

  function atualizarItem(idx: number, campo: keyof ItemEntrega, valor: string) {
    setItens((lista) => lista.map((item, i) => (i === idx ? { ...item, [campo]: valor } : item)));
  }

  function removerItem(idx: number) {
    setItens((lista) => lista.filter((_, i) => i !== idx));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
      await api.post("/entregas-materiais", {
        polo_id: poloId,
        data_entrega: dataEntrega || null,
        entregue_por: entreguePor || null,
        itens: itens.filter((i) => i.descricao.trim()),
      });
      setPoloId(ehMaster ? "" : usuario?.polo_id ?? "");
      setDataEntrega("");
      setEntreguePor("");
      setItens([{ ...ITEM_VAZIO }]);
      toast.success("Entrega de materiais registrada.");
      queryClient.invalidateQueries({ queryKey: ["entregas-materiais"] });
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao registrar a entrega."));
    } finally {
      setSalvando(false);
    }
  }

  async function exportar(entrega: EntregaMaterial) {
    setExportando(entrega.id);
    try {
      await baixarExportacao(
        `/entregas-materiais/${entrega.id}/exportar`,
        `Termo de Entrega de Materiais - ${poloNome(entrega.polo_id)}.docx`
      );
    } catch {
      toast.error("Não foi possível exportar o termo.");
    } finally {
      setExportando(null);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Entregas de Materiais"
        subtitle="Registre cada entrega de materiais/uniformes ao núcleo e exporte o Termo assinável."
      />
      <Card title="Registrar entrega" className="animate-fade-in-up" style={staggerStyle(0)}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select label="Polo" value={poloId} onChange={(e) => setPoloId(e.target.value)} disabled={!ehMaster} required>
              <option value="">— Selecione —</option>
              {polos.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
            </Select>
            <Input label="Data da entrega" type="date" value={dataEntrega} onChange={(e) => setDataEntrega(e.target.value)} />
            <Input
              label="Entregue por"
              placeholder="Nome de quem foi levar os materiais"
              value={entreguePor}
              onChange={(e) => setEntreguePor(e.target.value)}
            />
          </div>

          <div>
            <span className="block text-sm font-medium text-gray-700 mb-2">Itens entregues</span>
            <div className="space-y-2">
              {itens.map((item, idx) => (
                <div key={idx} className="grid grid-cols-1 sm:grid-cols-[1fr_140px_auto] gap-2 items-end">
                  <Input
                    label={idx === 0 ? "Descrição do item" : undefined}
                    placeholder="ex.: Bolas de futebol"
                    value={item.descricao}
                    onChange={(e) => atualizarItem(idx, "descricao", e.target.value)}
                  />
                  <Input
                    label={idx === 0 ? "Qtde entregue" : undefined}
                    placeholder="ex.: 10"
                    value={item.quantidade}
                    onChange={(e) => atualizarItem(idx, "quantidade", e.target.value)}
                  />
                  <button
                    type="button"
                    className="text-xs text-gray-400 hover:text-red-600 pb-2"
                    onClick={() => removerItem(idx)}
                    disabled={itens.length === 1}
                  >
                    remover
                  </button>
                </div>
              ))}
            </div>
            {itens.length < 18 && (
              <button
                type="button"
                className="text-xs text-brand hover:underline mt-2"
                onClick={() => setItens((lista) => [...lista, { ...ITEM_VAZIO }])}
              >
                + adicionar item
              </button>
            )}
          </div>

          <Button type="submit" disabled={salvando}>{salvando ? "Registrando…" : "Registrar entrega"}</Button>
        </form>
      </Card>

      <Card title="Entregas registradas" actions={<Badge variant="accent">{totalEntregas}</Badge>} className="animate-fade-in-up" style={staggerStyle(1)}>
        {carregando ? (
          <Spinner label="Carregando entregas…" />
        ) : totalEntregas === 0 ? (
          <EmptyState message="Nenhuma entrega registrada ainda." />
        ) : (
          <>
            {/* Celular: lista de cards. Telas sm+: tabela. */}
            <ul className="sm:hidden divide-y divide-gray-100">
              {entregas.map((e) => (
                <li key={e.id} className="py-3.5">
                  <div className="min-w-0">
                    <div className="font-medium text-gray-800 truncate">{poloNome(e.polo_id)}</div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {e.data_entrega ? formatarData(e.data_entrega) : "—"} · {e.itens.length} {e.itens.length === 1 ? "item" : "itens"}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5 truncate">
                      Entregue por {e.entregue_por ?? "—"}
                      {e.coordenador_nome ? ` · Coordenador: ${e.coordenador_nome}` : ""}
                    </div>
                  </div>
                  <Button variant="secondary" className="mt-3 w-full" onClick={() => exportar(e)} disabled={exportando === e.id}>
                    {exportando === e.id ? "Exportando…" : "Exportar .docx"}
                  </Button>
                </li>
              ))}
            </ul>

            <div className="hidden sm:block overflow-x-auto -mx-5 sm:-mx-8">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                    <th className="py-2.5 px-8">Polo</th>
                    <th className="px-3">Data</th>
                    <th className="px-3">Entregue por</th>
                    <th className="px-3">Coordenador</th>
                    <th className="px-3">Itens</th>
                    <th className="px-3 text-right pr-8">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {entregas.map((e) => (
                    <tr key={e.id} className="border-t border-gray-100 hover:bg-brand-light/60 transition-colors">
                      <td className="py-2.5 px-8 font-medium text-gray-800">{poloNome(e.polo_id)}</td>
                      <td className="px-3 text-gray-600">{e.data_entrega ? formatarData(e.data_entrega) : "—"}</td>
                      <td className="px-3 text-gray-600">{e.entregue_por ?? "—"}</td>
                      <td className="px-3 text-gray-600">{e.coordenador_nome ?? "—"}</td>
                      <td className="px-3 text-gray-600">{e.itens.length}</td>
                      <td className="px-3 text-right pr-8">
                        <Button variant="secondary" onClick={() => exportar(e)} disabled={exportando === e.id}>
                          {exportando === e.id ? "Exportando…" : "Exportar .docx"}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        <Paginacao pagina={pagina} tamanhoPagina={TAMANHO_PAGINA} total={totalEntregas} onChange={setPagina} />
      </Card>
    </div>
  );
}
