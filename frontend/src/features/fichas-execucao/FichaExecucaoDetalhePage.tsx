import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { AjusteStatus, FichaExecucao, Polo } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { PageHeader } from "@/components/ui/PageHeader";
import { Spinner } from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { baixarExportacao } from "./FichasExecucaoPage";

const AJUSTE_LABEL: Record<AjusteStatus, string> = {
  NAO_SOLICITADO: "Não solicitado",
  APROVADO: "Aprovado",
  NAO_APROVADO: "Não aprovado",
};

const PERIODOS = [
  { valor: "MANHA", label: "Manhã" },
  { valor: "TARDE", label: "Tarde" },
  { valor: "NOITE", label: "Noite" },
];

export function FichaExecucaoDetalhePage() {
  const { id } = useParams<{ id: string }>();
  const toast = useToast();
  const queryClient = useQueryClient();

  const { data: fichaCarregada, isLoading: carregando } = useQuery({
    queryKey: ["fichas-execucao", id],
    queryFn: () => api.get<FichaExecucao>(`/fichas-execucao/${id}`).then((r) => r.data),
    enabled: !!id,
  });
  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
  });

  const [ficha, setFicha] = useState<FichaExecucao | null>(null);
  const [salvando, setSalvando] = useState(false);
  const [exportando, setExportando] = useState(false);

  useEffect(() => {
    if (fichaCarregada) setFicha(fichaCarregada);
  }, [fichaCarregada]);

  const polo = ficha ? polos.find((p) => p.id === ficha.polo_id) ?? null : null;

  function patch(campos: Partial<FichaExecucao>) {
    setFicha((f) => (f ? { ...f, ...campos } : f));
  }

  async function salvar() {
    if (!ficha) return;
    setSalvando(true);
    try {
      await api.patch(`/fichas-execucao/${ficha.id}`, {
        valor_recebido_periodo: ficha.valor_recebido_periodo,
        valor_recebido_extenso: ficha.valor_recebido_extenso,
        data_recebimento: ficha.data_recebimento || null,
        ajuste_status: ficha.ajuste_status,
        ajuste_justificativa: ficha.ajuste_justificativa,
        metas: ficha.metas,
        atividades_comparativo: ficha.atividades_comparativo,
        checklist_documentos: ficha.checklist_documentos,
        periodo_inscricao_inicio: ficha.periodo_inscricao_inicio || null,
        periodo_inscricao_fim: ficha.periodo_inscricao_fim || null,
        inscricao_todos_nucleos: ficha.inscricao_todos_nucleos,
        qtd_inscritos: ficha.qtd_inscritos,
        observacoes_inscricao: ficha.observacoes_inscricao,
        quantitativo_beneficiados: ficha.quantitativo_beneficiados,
        modalidades: ficha.modalidades,
        periodo_funcionamento: ficha.periodo_funcionamento,
        descricao_atividades: ficha.descricao_atividades,
        dificuldades: ficha.dificuldades,
        impactos_sociais: ficha.impactos_sociais,
        consideracoes_finais: ficha.consideracoes_finais,
      });
      toast.success("Ficha salva.");
      queryClient.invalidateQueries({ queryKey: ["fichas-execucao"] });
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao salvar a ficha."));
    } finally {
      setSalvando(false);
    }
  }

  async function exportar() {
    if (!ficha) return;
    setExportando(true);
    try {
      await baixarExportacao(
        `/fichas-execucao/${ficha.id}/exportar`,
        `Ficha Tecnica de Execucao - ${ficha.periodo_referencia}.xlsx`
      );
    } catch {
      toast.error("Não foi possível exportar a ficha.");
    } finally {
      setExportando(false);
    }
  }

  if (carregando) return <Spinner label="Carregando ficha…" />;
  if (!ficha) return <p className="text-sm text-gray-500">Ficha não encontrada.</p>;

  return (
    <div className="space-y-6 pb-16">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <PageHeader
          title={`Ficha — ${ficha.periodo_referencia}`}
          subtitle={polo ? `${polo.nome} — Ficha Técnica de Execução da Entidade.` : "Ficha Técnica de Execução da Entidade."}
        />
        <div className="flex gap-2">
          <Link to="/fichas-execucao"><Button variant="secondary">Voltar</Button></Link>
          <Button variant="secondary" onClick={exportar} disabled={exportando}>
            {exportando ? "Exportando…" : "Exportar .xlsx"}
          </Button>
          <Button onClick={salvar} disabled={salvando}>{salvando ? "Salvando…" : "Salvar"}</Button>
        </div>
      </div>

      <Card title="2 — Valores recebidos" className="animate-fade-in-up" style={staggerStyle(0)}>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Input
            label="Valor recebido no período" placeholder="R$ 0,00"
            value={ficha.valor_recebido_periodo ?? ""}
            onChange={(e) => patch({ valor_recebido_periodo: e.target.value })}
          />
          <Input
            label="Valor por extenso"
            value={ficha.valor_recebido_extenso ?? ""}
            onChange={(e) => patch({ valor_recebido_extenso: e.target.value })}
          />
          <Input
            label="Data do recebimento" type="date"
            value={ficha.data_recebimento ?? ""}
            onChange={(e) => patch({ data_recebimento: e.target.value })}
          />
        </div>
      </Card>

      <Card title="1.2 — Ajuste do plano de trabalho" className="animate-fade-in-up" style={staggerStyle(1)}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="Situação do ajuste"
            value={ficha.ajuste_status}
            onChange={(e) => patch({ ajuste_status: e.target.value as AjusteStatus })}
          >
            {Object.entries(AJUSTE_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </Select>
          <Input
            label="Justificativa"
            value={ficha.ajuste_justificativa ?? ""}
            onChange={(e) => patch({ ajuste_justificativa: e.target.value })}
          />
        </div>
      </Card>

      <Card title="3 — Análise de valor (metas e etapas)" className="animate-fade-in-up" style={staggerStyle(2)}>
        <div className="space-y-6">
          {(ficha.metas ?? []).map((meta, mi) => (
            <div key={mi}>
              <h3 className="text-sm font-semibold text-brand-dark mb-2">{meta.meta}</h3>
              <div className="overflow-x-auto -mx-6">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-gray-400">
                      <th className="py-1.5 px-6">Etapa</th>
                      <th className="px-3">Previsto</th>
                      <th className="px-3">Executado</th>
                      <th className="px-3 pr-6 text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(meta.etapas ?? []).map((etapa, ei) => (
                      <tr key={ei} className="border-t border-gray-100">
                        <td className="py-1.5 px-6">
                          <Input value={etapa.nome} onChange={(e) => {
                            const metas = ficha.metas.map((m, i) =>
                              i !== mi ? m : { ...m, etapas: (m.etapas ?? []).map((et, j) => (j === ei ? { ...et, nome: e.target.value } : et)) }
                            );
                            patch({ metas });
                          }} />
                        </td>
                        <td className="px-3">
                          <Input value={etapa.previsto} onChange={(e) => {
                            const metas = ficha.metas.map((m, i) =>
                              i !== mi ? m : { ...m, etapas: (m.etapas ?? []).map((et, j) => (j === ei ? { ...et, previsto: e.target.value } : et)) }
                            );
                            patch({ metas });
                          }} />
                        </td>
                        <td className="px-3">
                          <Input value={etapa.executado} onChange={(e) => {
                            const metas = ficha.metas.map((m, i) =>
                              i !== mi ? m : { ...m, etapas: (m.etapas ?? []).map((et, j) => (j === ei ? { ...et, executado: e.target.value } : et)) }
                            );
                            patch({ metas });
                          }} />
                        </td>
                        <td className="px-3 pr-6 text-right">
                          <button type="button" className="text-xs text-gray-400 hover:text-red-600" onClick={() => {
                            const metas = ficha.metas.map((m, i) =>
                              i !== mi ? m : { ...m, etapas: (m.etapas ?? []).filter((_, j) => j !== ei) }
                            );
                            patch({ metas });
                          }}>remover</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {(meta.etapas ?? []).length < 5 && (
                <button type="button" className="text-xs text-brand hover:underline mt-2" onClick={() => {
                  const metas = ficha.metas.map((m, i) =>
                    i !== mi ? m : { ...m, etapas: [...(m.etapas ?? []), { nome: "", previsto: "", executado: "" }] }
                  );
                  patch({ metas });
                }}>+ adicionar etapa</button>
              )}
            </div>
          ))}
        </div>
      </Card>

      <Card title="4 — Desenvolvimento das atividades (pactuado x executado)" className="animate-fade-in-up" style={staggerStyle(3)}>
        <div className="overflow-x-auto -mx-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-gray-400">
                <th className="py-1.5 px-6">Item</th>
                <th className="px-3">Pactuado</th>
                <th className="px-3">Executado</th>
                <th className="px-3 pr-6">Observações</th>
              </tr>
            </thead>
            <tbody>
              {(ficha.atividades_comparativo ?? []).map((item, i) => (
                <tr key={i} className="border-t border-gray-100">
                  <td className="py-1.5 px-6 font-medium text-gray-700 whitespace-nowrap">{item.item}</td>
                  <td className="px-3"><Input value={item.pactuado} onChange={(e) => {
                    const lista = [...(ficha.atividades_comparativo ?? [])];
                    lista[i] = { ...item, pactuado: e.target.value };
                    patch({ atividades_comparativo: lista });
                  }} /></td>
                  <td className="px-3"><Input value={item.executado} onChange={(e) => {
                    const lista = [...(ficha.atividades_comparativo ?? [])];
                    lista[i] = { ...item, executado: e.target.value };
                    patch({ atividades_comparativo: lista });
                  }} /></td>
                  <td className="px-3 pr-6"><Input value={item.observacoes} onChange={(e) => {
                    const lista = [...(ficha.atividades_comparativo ?? [])];
                    lista[i] = { ...item, observacoes: e.target.value };
                    patch({ atividades_comparativo: lista });
                  }} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="5 — Execução (checklist de documentação)" className="animate-fade-in-up" style={staggerStyle(4)}>
        <div className="overflow-x-auto -mx-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-gray-400">
                <th className="py-1.5 px-6">Documento</th>
                <th className="px-3">Situação</th>
                <th className="px-3 pr-6">Observação</th>
              </tr>
            </thead>
            <tbody>
              {(ficha.checklist_documentos ?? []).map((item, i) => (
                <tr key={i} className="border-t border-gray-100">
                  <td className="py-1.5 px-6 text-gray-700">{item.documento}</td>
                  <td className="px-3 w-44">
                    <Select value={item.situacao} onChange={(e) => {
                      const lista = [...(ficha.checklist_documentos ?? [])];
                      lista[i] = { ...item, situacao: e.target.value as "Inserido" | "Não Inserido" };
                      patch({ checklist_documentos: lista });
                    }}>
                      <option value="Não Inserido">Não Inserido</option>
                      <option value="Inserido">Inserido</option>
                    </Select>
                  </td>
                  <td className="px-3 pr-6"><Input value={item.observacao} onChange={(e) => {
                    const lista = [...ficha.checklist_documentos];
                    lista[i] = { ...item, observacao: e.target.value };
                    patch({ checklist_documentos: lista });
                  }} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="6 — Inscrição dos beneficiados" className="animate-fade-in-up" style={staggerStyle(5)}>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Input label="Início" type="date" value={ficha.periodo_inscricao_inicio ?? ""} onChange={(e) => patch({ periodo_inscricao_inicio: e.target.value })} />
          <Input label="Fim" type="date" value={ficha.periodo_inscricao_fim ?? ""} onChange={(e) => patch({ periodo_inscricao_fim: e.target.value })} />
          <Select
            label="Ocorreu em todos os núcleos?"
            value={ficha.inscricao_todos_nucleos === null ? "" : ficha.inscricao_todos_nucleos ? "sim" : "nao"}
            onChange={(e) => patch({ inscricao_todos_nucleos: e.target.value === "" ? null : e.target.value === "sim" })}
          >
            <option value="">—</option>
            <option value="sim">Sim</option>
            <option value="nao">Não</option>
          </Select>
          <Input
            label="Qtd. inscritos" type="number" min={0}
            value={ficha.qtd_inscritos ?? ""}
            onChange={(e) => patch({ qtd_inscritos: e.target.value === "" ? null : Number(e.target.value) })}
          />
          <div className="sm:col-span-4">
            <Input label="Observações" value={ficha.observacoes_inscricao ?? ""} onChange={(e) => patch({ observacoes_inscricao: e.target.value })} />
          </div>
        </div>
      </Card>

      <Card
        title="7 — Identificação do núcleo"
        subtitle="Nome, endereço e responsável vêm do cadastro do polo — edite em Polos se precisar corrigir."
        className="animate-fade-in-up" style={staggerStyle(6)}
      >
        <div className="space-y-4">
          {polo && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm bg-brand-light/60 rounded-lg p-4">
              <div><span className="text-gray-500">Nome:</span> <span className="font-medium">{polo.nome}</span></div>
              <div><span className="text-gray-500">Endereço:</span> <span className="font-medium">{polo.endereco || "—"}</span></div>
              <div><span className="text-gray-500">Responsável:</span> <span className="font-medium">{polo.responsavel_nome || "—"}</span></div>
              <div><span className="text-gray-500">E-mail:</span> <span className="font-medium">{polo.responsavel_email || "—"}</span></div>
              <div><span className="text-gray-500">Telefone:</span> <span className="font-medium">{polo.responsavel_telefone || "—"}</span></div>
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Quantitativo de beneficiados"
              value={ficha.quantitativo_beneficiados ?? ""}
              onChange={(e) => patch({ quantitativo_beneficiados: e.target.value })}
            />
            <Input
              label="Modalidades"
              value={ficha.modalidades ?? ""}
              onChange={(e) => patch({ modalidades: e.target.value })}
            />
          </div>
          <div>
            <span className="block text-sm font-medium text-gray-700 mb-1">Período</span>
            <div className="flex flex-wrap gap-2">
              {PERIODOS.map((p) => {
                const selecionados = ficha.periodo_funcionamento ? ficha.periodo_funcionamento.split(",") : [];
                const ativo = selecionados.includes(p.valor);
                return (
                  <button type="button" key={p.valor} onClick={() => {
                    const novos = ativo ? selecionados.filter((v) => v !== p.valor) : [...selecionados, p.valor];
                    patch({ periodo_funcionamento: novos.join(",") });
                  }} className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors ${ativo ? "bg-accent text-brand-dark border-accent" : "bg-white border-gray-300 text-gray-600 hover:bg-gray-50"}`}>
                    {p.label}
                  </button>
                );
              })}
            </div>
          </div>
          <Input
            label="Descrição das atividades realizadas"
            value={ficha.descricao_atividades ?? ""}
            onChange={(e) => patch({ descricao_atividades: e.target.value })}
          />
          <Input
            label="Dificuldades enfrentadas"
            value={ficha.dificuldades ?? ""}
            onChange={(e) => patch({ dificuldades: e.target.value })}
          />
        </div>
      </Card>

      <Card title="9 — Impactos do benefício social" className="animate-fade-in-up" style={staggerStyle(7)}>
        <div className="space-y-4">
          <Input label="Impactos sociais do projeto/evento" value={ficha.impactos_sociais ?? ""} onChange={(e) => patch({ impactos_sociais: e.target.value })} />
          <Input label="Considerações finais quanto ao projeto" value={ficha.consideracoes_finais ?? ""} onChange={(e) => patch({ consideracoes_finais: e.target.value })} />
        </div>
      </Card>

      <Button onClick={salvar} disabled={salvando}>{salvando ? "Salvando…" : "Salvar"}</Button>
    </div>
  );
}
