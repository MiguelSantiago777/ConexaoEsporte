import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Pagina, Polo } from "@/types";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { Paginacao } from "@/components/ui/Paginacao";
import { CalendarCheckIcon, ClipboardIcon, DocumentTextIcon, PencilIcon, TrashIcon } from "@/components/ui/icons";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { baixarExportacao } from "@/features/fichas-execucao/FichasExecucaoPage";
import { CadastrarPoloWizard } from "./CadastrarPoloWizard";
import { EditarPoloModal } from "./EditarPoloModal";

const TAMANHO_PAGINA = 10;

export function PolosPage() {
  const toast = useToast();
  const queryClient = useQueryClient();

  const [filtroNome, setFiltroNome] = useState("");
  const [filtroNomeDebounced, setFiltroNomeDebounced] = useState("");
  const [pagina, setPagina] = useState(1);

  useEffect(() => {
    const t = setTimeout(() => setFiltroNomeDebounced(filtroNome), 300);
    return () => clearTimeout(t);
  }, [filtroNome]);

  useEffect(() => {
    setPagina(1);
  }, [filtroNomeDebounced]);

  const polosQueryKey = ["polos", "pagina", pagina, filtroNomeDebounced];
  const { data: paginaPolos, isLoading: carregando } = useQuery({
    queryKey: polosQueryKey,
    queryFn: () =>
      api
        .get<Pagina<Polo>>("/polos", { params: { pagina, tamanho_pagina: TAMANHO_PAGINA, nome: filtroNomeDebounced || undefined } })
        .then((r) => r.data),
  });
  const polos = paginaPolos?.itens ?? [];
  const totalPolos = paginaPolos?.total ?? 0;

  const [poloEditando, setPoloEditando] = useState<Polo | null>(null);
  const [exportandoGrade, setExportandoGrade] = useState<string | null>(null);
  const [exportandoNucleos, setExportandoNucleos] = useState<string | null>(null);
  const [exportandoTermo, setExportandoTermo] = useState<string | null>(null);

  const desativarMutation = useMutation({
    mutationFn: (p: Polo) => api.patch(`/polos/${p.id}`, { status: "INATIVO" }),
    onSuccess: () => {
      toast.success("Polo desativado.");
      queryClient.invalidateQueries({ queryKey: ["polos"] });
    },
    onError: (err: any) => {
      toast.error(mensagemErroApi(err, "Erro ao desativar polo."));
    },
  });

  function excluirPolo(p: Polo) {
    if (!window.confirm(`Desativar o polo "${p.nome}"? Ele deixa de aparecer como opção em novos cadastros.`)) return;
    desativarMutation.mutate(p);
  }

  async function exportarGradeHoraria(p: Polo) {
    const entrada = window.prompt("Horas de planejamento semanal (opcional):", "0");
    if (entrada === null) return;
    const planejamento = Number(entrada.replace(",", ".")) || 0;
    setExportandoGrade(p.id);
    try {
      await baixarExportacao(
        `/polos/${p.id}/grade-horaria/exportar?planejamento_horas=${planejamento}`,
        `Grade Horaria - ${p.nome}.docx`
      );
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao exportar a Grade Horária."));
    } finally {
      setExportandoGrade(null);
    }
  }

  async function exportarPlanilhaNucleos(p: Polo) {
    setExportandoNucleos(p.id);
    try {
      await baixarExportacao(`/polos/${p.id}/planilha-nucleos/exportar`, `Planilha de Nucleos - ${p.nome}.xlsx`);
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao exportar a Planilha de Núcleos."));
    } finally {
      setExportandoNucleos(null);
    }
  }

  async function exportarTermoResponsabilidade(p: Polo) {
    setExportandoTermo(p.id);
    try {
      await baixarExportacao(`/polos/${p.id}/termo-responsabilidade/exportar`, `Termo de Responsabilidade - ${p.nome}.docx`);
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao exportar o Termo de Responsabilidade."));
    } finally {
      setExportandoTermo(null);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Polos"
        subtitle="Unidades onde os projetos esportivos são executados. Cada polo é sua própria entidade parceira do Termo de Fomento — edite para preencher CNPJ, representante legal etc."
      />
      <CadastrarPoloWizard
        onCadastrado={() => queryClient.invalidateQueries({ queryKey: ["polos"] })}
        style={staggerStyle(0)}
      />
      <Card
        title="Polos"
        actions={<Badge variant="accent">{totalPolos}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(1)}
      >
        <div className="mb-4 sm:max-w-xs">
          <Input label="Buscar por nome" placeholder="Nome do polo" value={filtroNome} onChange={(e) => setFiltroNome(e.target.value)} />
        </div>
        {carregando ? (
          <Spinner label="Carregando polos…" />
        ) : totalPolos === 0 ? (
          <EmptyState message={filtroNome ? "Nenhum polo encontrado com esse filtro." : "Nenhum polo cadastrado ainda."} />
        ) : (
          <>
            {/* Celular: lista de cards. Telas sm+: tabela. */}
            <ul className="sm:hidden divide-y divide-gray-100">
              {polos.map((p) => (
                <li key={p.id} className="py-3.5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="font-medium text-gray-800 truncate">
                        {p.codigo ? `${p.codigo} — ` : ""}
                        {p.nome}
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5 truncate">{p.nome_entidade ?? "—"}</div>
                      <div className="text-xs text-gray-500 mt-0.5 truncate">
                        Termo: {p.termo_fomento_numero ?? "—"}
                      </div>
                    </div>
                    <Badge variant={p.status === "ATIVO" ? "accent" : "gray"}>{p.status}</Badge>
                  </div>
                  <div className="flex items-center gap-5 mt-3 flex-wrap">
                    <button
                      type="button"
                      title="Exportar Grade Horária"
                      onClick={() => exportarGradeHoraria(p)}
                      disabled={exportandoGrade === p.id}
                      className="text-gray-400 hover:text-brand transition-colors disabled:opacity-40 -m-1.5 p-1.5"
                    >
                      <CalendarCheckIcon className="w-[18px] h-[18px]" />
                    </button>
                    <button
                      type="button"
                      title="Exportar Planilha de Núcleos"
                      onClick={() => exportarPlanilhaNucleos(p)}
                      disabled={exportandoNucleos === p.id}
                      className="text-gray-400 hover:text-brand transition-colors disabled:opacity-40 -m-1.5 p-1.5"
                    >
                      <ClipboardIcon className="w-[18px] h-[18px]" />
                    </button>
                    <button
                      type="button"
                      title="Exportar Termo de Responsabilidade"
                      onClick={() => exportarTermoResponsabilidade(p)}
                      disabled={exportandoTermo === p.id}
                      className="text-gray-400 hover:text-brand transition-colors disabled:opacity-40 -m-1.5 p-1.5"
                    >
                      <DocumentTextIcon className="w-[18px] h-[18px]" />
                    </button>
                    <button
                      type="button"
                      title="Editar"
                      onClick={() => setPoloEditando(p)}
                      className="text-gray-400 hover:text-brand transition-colors -m-1.5 p-1.5"
                    >
                      <PencilIcon className="w-[18px] h-[18px]" />
                    </button>
                    {p.status === "ATIVO" && (
                      <button
                        type="button"
                        title="Desativar"
                        onClick={() => excluirPolo(p)}
                        className="text-gray-400 hover:text-red-600 transition-colors -m-1.5 p-1.5"
                      >
                        <TrashIcon className="w-[18px] h-[18px]" />
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>

            <div className="hidden sm:block overflow-x-auto -mx-5 sm:-mx-8">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                    <th className="py-2.5 px-8">Código</th>
                    <th className="px-3">Nome</th>
                    <th className="px-3">Entidade parceira</th>
                    <th className="px-3">Termo de Fomento</th>
                    <th className="px-3">Status</th>
                    <th className="px-3 text-right pr-8">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {polos.map((p) => (
                    <tr key={p.id} className="border-t border-gray-100 hover:bg-brand-light/60 transition-colors">
                      <td className="py-2.5 px-8 font-medium text-gray-800">{p.codigo ?? "—"}</td>
                      <td className="px-3 text-gray-600">{p.nome}</td>
                      <td className="px-3 text-gray-600">{p.nome_entidade ?? "—"}</td>
                      <td className="px-3 text-gray-600">{p.termo_fomento_numero ?? "—"}</td>
                      <td className="px-3">
                        <Badge variant={p.status === "ATIVO" ? "accent" : "gray"}>{p.status}</Badge>
                      </td>
                      <td className="px-3 text-right pr-8">
                        <div className="flex items-center justify-end gap-3">
                          <button
                            type="button"
                            title="Exportar Grade Horária"
                            onClick={() => exportarGradeHoraria(p)}
                            disabled={exportandoGrade === p.id}
                            className="text-gray-400 hover:text-brand transition-colors disabled:opacity-40"
                          >
                            <CalendarCheckIcon className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            title="Exportar Planilha de Núcleos"
                            onClick={() => exportarPlanilhaNucleos(p)}
                            disabled={exportandoNucleos === p.id}
                            className="text-gray-400 hover:text-brand transition-colors disabled:opacity-40"
                          >
                            <ClipboardIcon className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            title="Exportar Termo de Responsabilidade"
                            onClick={() => exportarTermoResponsabilidade(p)}
                            disabled={exportandoTermo === p.id}
                            className="text-gray-400 hover:text-brand transition-colors disabled:opacity-40"
                          >
                            <DocumentTextIcon className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            title="Editar"
                            onClick={() => setPoloEditando(p)}
                            className="text-gray-400 hover:text-brand transition-colors"
                          >
                            <PencilIcon />
                          </button>
                          {p.status === "ATIVO" && (
                            <button
                              type="button"
                              title="Desativar"
                              onClick={() => excluirPolo(p)}
                              className="text-gray-400 hover:text-red-600 transition-colors"
                            >
                              <TrashIcon />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        <Paginacao pagina={pagina} tamanhoPagina={TAMANHO_PAGINA} total={totalPolos} onChange={setPagina} />
      </Card>

      <EditarPoloModal
        polo={poloEditando}
        onClose={() => setPoloEditando(null)}
        onSalvo={() => {
          setPoloEditando(null);
          toast.success("Alterações salvas.");
          queryClient.invalidateQueries({ queryKey: ["polos"] });
        }}
        onAtualizado={() => queryClient.invalidateQueries({ queryKey: ["polos"] })}
      />
    </div>
  );
}
