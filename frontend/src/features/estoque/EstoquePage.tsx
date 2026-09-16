import { Fragment, FormEvent, useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Almoxarifado, MovimentoEstoque, Pagina, Produto, SaldoAlmoxarifado } from "@/types";
import { useAuth } from "@/features/auth/AuthContext";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { FileInput } from "@/components/ui/FileInput";
import { Modal } from "@/components/ui/Modal";
import { PageHeader } from "@/components/ui/PageHeader";
import { Paginacao } from "@/components/ui/Paginacao";
import { DocumentTextIcon, PencilIcon, TrashIcon } from "@/components/ui/icons";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { exportarPdf } from "@/lib/exportarPdf";
import { dataBR } from "@/features/frequencia/statusChamada";
import { EditarProdutoModal } from "./EditarProdutoModal";
import { ImportarPlanilhaModal } from "@/components/import/ImportarPlanilhaModal";

const TAMANHO_PAGINA = 10;
const FORM_PRODUTO_INICIAL = { nome: "", unidade_medida: "", descricao: "" };

function hoje() {
  return new Date().toISOString().slice(0, 10);
}

export function EstoquePage() {
  const { temPerfil } = useAuth();
  const toast = useToast();
  const queryClient = useQueryClient();
  const ehMaster = temPerfil("MASTER");

  // --- Cadastrar produto (MASTER) ---
  const [formProduto, setFormProduto] = useState(FORM_PRODUTO_INICIAL);
  const [salvandoProduto, setSalvandoProduto] = useState(false);
  const [produtoEditando, setProdutoEditando] = useState<Produto | null>(null);

  async function cadastrarProduto(e: FormEvent) {
    e.preventDefault();
    setSalvandoProduto(true);
    try {
      await api.post("/produtos", {
        nome: formProduto.nome, unidade_medida: formProduto.unidade_medida,
        descricao: formProduto.descricao || null,
      });
      setFormProduto(FORM_PRODUTO_INICIAL);
      toast.success("Produto cadastrado com sucesso.");
      queryClient.invalidateQueries({ queryKey: ["produtos"] });
    } catch (err: unknown) {
      toast.error(mensagemErroApi(err, "Erro ao cadastrar produto."));
    } finally {
      setSalvandoProduto(false);
    }
  }

  const removerProdutoMutation = useMutation({
    mutationFn: (p: Produto) => api.delete(`/produtos/${p.id}`),
    onSuccess: () => {
      toast.success("Produto removido.");
      queryClient.invalidateQueries({ queryKey: ["produtos"] });
    },
    onError: (err: unknown) => toast.error(mensagemErroApi(err, "Erro ao remover produto.")),
  });

  function removerProduto(p: Produto) {
    if (!window.confirm(`Remover o produto "${p.nome}"?`)) return;
    removerProdutoMutation.mutate(p);
  }

  // --- Lista completa (sem paginação) de produtos ativos — usada pelo
  // <select> do formulário de Entrada, que precisa de todas as opções. ---
  const { data: produtosAtivos = [] } = useQuery({
    queryKey: ["produtos", "ativos"],
    queryFn: () => api.get<Produto[]>("/produtos", { params: { apenas_ativos: true } }).then((r) => r.data),
  });

  // --- Almoxarifados — cadastro fica na página dedicada (Cadastros >
  // Almoxarifados); aqui só reaproveita a lista completa pros <select> de
  // Entrada/Movimentações. ---
  const { data: almoxarifados = [] } = useQuery({
    queryKey: ["almoxarifados"],
    queryFn: () => api.get<Almoxarifado[]>("/almoxarifados").then((r) => r.data),
  });

  function nomeAlmoxarifado(id: string) {
    return almoxarifados.find((a) => a.id === id)?.nome ?? "—";
  }

  // --- Detalhamento de saldo por almoxarifado (só busca quando expandido) ---
  const [produtoDetalhado, setProdutoDetalhado] = useState<string | null>(null);
  const { data: saldosDetalhados = [], isLoading: carregandoSaldos } = useQuery({
    queryKey: ["produtos", produtoDetalhado, "saldos-por-almoxarifado"],
    queryFn: () => api.get<SaldoAlmoxarifado[]>(`/produtos/${produtoDetalhado}/saldos-por-almoxarifado`).then((r) => r.data),
    enabled: !!produtoDetalhado,
  });

  // --- Registrar entrada (MASTER) ---
  const FORM_ENTRADA_INICIAL = { produto_id: "", almoxarifado_id: "", quantidade: "", data: hoje(), observacao: "", entregue_por: "", recebido_por: "" };
  const [formEntrada, setFormEntrada] = useState(FORM_ENTRADA_INICIAL);
  const [arquivoEntrada, setArquivoEntrada] = useState<File | null>(null);
  const [enviandoEntrada, setEnviandoEntrada] = useState(false);

  async function registrarEntrada(e: FormEvent) {
    e.preventDefault();
    if (!arquivoEntrada) return;
    setEnviandoEntrada(true);
    try {
      const dados = new FormData();
      dados.append("produto_id", formEntrada.produto_id);
      dados.append("almoxarifado_id", formEntrada.almoxarifado_id);
      dados.append("quantidade", formEntrada.quantidade);
      dados.append("data", formEntrada.data);
      if (formEntrada.observacao) dados.append("observacao", formEntrada.observacao);
      if (formEntrada.entregue_por) dados.append("entregue_por", formEntrada.entregue_por);
      if (formEntrada.recebido_por) dados.append("recebido_por", formEntrada.recebido_por);
      dados.append("arquivo", arquivoEntrada);
      await api.post("/movimentos-estoque", dados);
      setFormEntrada(FORM_ENTRADA_INICIAL);
      setArquivoEntrada(null);
      toast.success("Entrada registrada com sucesso.");
      queryClient.invalidateQueries({ queryKey: ["produtos"] });
      queryClient.invalidateQueries({ queryKey: ["movimentos-estoque"] });
      queryClient.invalidateQueries({ queryKey: ["produtos", formEntrada.produto_id, "saldos-por-almoxarifado"] });
    } catch (err: unknown) {
      toast.error(mensagemErroApi(err, "Erro ao registrar entrada."));
    } finally {
      setEnviandoEntrada(false);
    }
  }

  // --- Produtos em estoque (paginado) ---
  const [filtroNomeProduto, setFiltroNomeProduto] = useState("");
  const [filtroNomeProdutoDebounced, setFiltroNomeProdutoDebounced] = useState("");
  const [paginaProdutos, setPaginaProdutos] = useState(1);
  const [importarAberto, setImportarAberto] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setFiltroNomeProdutoDebounced(filtroNomeProduto), 300);
    return () => clearTimeout(t);
  }, [filtroNomeProduto]);
  const [filtroNomeProdutoAnterior, setFiltroNomeProdutoAnterior] = useState(filtroNomeProdutoDebounced);
  if (filtroNomeProdutoDebounced !== filtroNomeProdutoAnterior) {
    setFiltroNomeProdutoAnterior(filtroNomeProdutoDebounced);
    setPaginaProdutos(1);
  }

  const { data: paginaProdutosResp, isLoading: carregandoProdutos } = useQuery({
    queryKey: ["produtos", "pagina", paginaProdutos, filtroNomeProdutoDebounced],
    queryFn: () =>
      api
        .get<Pagina<Produto>>("/produtos", { params: { pagina: paginaProdutos, tamanho_pagina: TAMANHO_PAGINA, nome: filtroNomeProdutoDebounced || undefined } })
        .then((r) => r.data),
  });
  const produtos = paginaProdutosResp?.itens ?? [];
  const totalProdutos = paginaProdutosResp?.total ?? 0;

  function nomeProduto(id: string) {
    return produtosAtivos.find((p) => p.id === id)?.nome ?? produtos.find((p) => p.id === id)?.nome ?? "—";
  }

  // --- Movimentações (paginado, com filtros) ---
  const [filtroProdutoMov, setFiltroProdutoMov] = useState("");
  const [filtroAlmoxarifadoMov, setFiltroAlmoxarifadoMov] = useState("");
  const [filtroTipoMov, setFiltroTipoMov] = useState("");
  const [paginaMovs, setPaginaMovs] = useState(1);

  const [filtrosMovAnteriores, setFiltrosMovAnteriores] = useState([filtroProdutoMov, filtroAlmoxarifadoMov, filtroTipoMov]);
  if (
    filtrosMovAnteriores[0] !== filtroProdutoMov ||
    filtrosMovAnteriores[1] !== filtroAlmoxarifadoMov ||
    filtrosMovAnteriores[2] !== filtroTipoMov
  ) {
    setFiltrosMovAnteriores([filtroProdutoMov, filtroAlmoxarifadoMov, filtroTipoMov]);
    setPaginaMovs(1);
  }

  const { data: paginaMovsResp, isLoading: carregandoMovs } = useQuery({
    queryKey: ["movimentos-estoque", "pagina", paginaMovs, filtroProdutoMov, filtroAlmoxarifadoMov, filtroTipoMov],
    queryFn: () =>
      api
        .get<Pagina<MovimentoEstoque>>("/movimentos-estoque", {
          params: {
            pagina: paginaMovs, tamanho_pagina: TAMANHO_PAGINA,
            produto_id: filtroProdutoMov || undefined, almoxarifado_id: filtroAlmoxarifadoMov || undefined,
            tipo: filtroTipoMov || undefined,
          },
        })
        .then((r) => r.data),
  });
  const movimentos = paginaMovsResp?.itens ?? [];
  const totalMovs = paginaMovsResp?.total ?? 0;

  // --- Termo de Retirada e Recebimento — documento pra assinatura de quem
  // entregou/retirou e de quem recebeu no almoxarifado, gerado a partir dos
  // dados já registrados no movimento (mesmo padrão client-side da
  // Autorização de Imagem: renderiza o termo escondido e baixa como PDF,
  // sem passar pelo backend). ---
  const [movimentoTermo, setMovimentoTermo] = useState<MovimentoEstoque | null>(null);
  const [exportandoTermo, setExportandoTermo] = useState(false);
  const termoRef = useRef<HTMLDivElement>(null);

  async function baixarTermo() {
    if (!termoRef.current || !movimentoTermo) return;
    setExportandoTermo(true);
    try {
      await exportarPdf(termoRef.current, `Termo de Retirada e Recebimento - ${nomeProduto(movimentoTermo.produto_id)}.pdf`);
    } catch {
      toast.error("Não foi possível gerar o PDF. Tente novamente.");
    } finally {
      setExportandoTermo(false);
    }
  }

  const [baixando, setBaixando] = useState<string | null>(null);
  async function baixarArquivoMovimento(m: MovimentoEstoque) {
    if (!m.nome_arquivo) return;
    setBaixando(m.id);
    try {
      const resp = await api.get(`/movimentos-estoque/${m.id}/arquivo`, { responseType: "blob" });
      const url = window.URL.createObjectURL(resp.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = m.nome_arquivo;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error("Não foi possível abrir o arquivo.");
    } finally {
      setBaixando(null);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Estoque"
        subtitle="Catálogo de produtos e movimentações de Entrada e Saída — a Saída acontece automaticamente ao registrar uma Entrega de Materiais com um item do estoque."
      />

      {ehMaster && (
        <Card
          title="Cadastrar produto"
          actions={
            <Button type="button" variant="secondary" onClick={() => setImportarAberto(true)}>
              Importar planilha
            </Button>
          }
          className="animate-fade-in-up"
          style={staggerStyle(0)}
        >
          <form onSubmit={cadastrarProduto} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-2">
              <Input label="Nome" placeholder="ex.: Bola de futebol" value={formProduto.nome}
                onChange={(e) => setFormProduto({ ...formProduto, nome: e.target.value })} required />
            </div>
            <Input label="Unidade de medida" placeholder="ex.: unidade, par, caixa" value={formProduto.unidade_medida}
              onChange={(e) => setFormProduto({ ...formProduto, unidade_medida: e.target.value })} required />
            <div className="sm:col-span-3">
              <Input label="Descrição (opcional)" value={formProduto.descricao}
                onChange={(e) => setFormProduto({ ...formProduto, descricao: e.target.value })} />
            </div>
            <div className="sm:col-span-3">
              <Button type="submit" disabled={salvandoProduto}>{salvandoProduto ? "Cadastrando…" : "Cadastrar produto"}</Button>
            </div>
          </form>
        </Card>
      )}

      {ehMaster && (
        <Card
          title="Registrar entrada"
          subtitle="Nota fiscal ou comprovante da compra/recebimento é obrigatório — fica anexado ao movimento, junto de quem entregou e quem recebeu no estoque. Não achou o almoxarifado? Cadastre em Cadastros → Almoxarifados."
          className="animate-fade-in-up"
          style={staggerStyle(1)}
        >
          <form onSubmit={registrarEntrada} className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="sm:col-span-2">
              <Select label="Produto" value={formEntrada.produto_id}
                onChange={(e) => setFormEntrada({ ...formEntrada, produto_id: e.target.value })} required>
                <option value="">— Selecione —</option>
                {produtosAtivos.map((p) => (
                  <option key={p.id} value={p.id}>{p.nome} ({p.unidade_medida})</option>
                ))}
              </Select>
            </div>
            <div className="sm:col-span-2">
              <Select label="Almoxarifado (onde entrou)" value={formEntrada.almoxarifado_id}
                onChange={(e) => setFormEntrada({ ...formEntrada, almoxarifado_id: e.target.value })} required>
                <option value="">— Selecione —</option>
                {almoxarifados.map((a) => <option key={a.id} value={a.id}>{a.nome}</option>)}
              </Select>
            </div>
            <Input label="Quantidade" type="number" min={1} placeholder="ex.: 50" value={formEntrada.quantidade}
              onChange={(e) => setFormEntrada({ ...formEntrada, quantidade: e.target.value })} required />
            <Input label="Data" type="date" value={formEntrada.data}
              onChange={(e) => setFormEntrada({ ...formEntrada, data: e.target.value })} required />
            <Input label="Entregue por" placeholder="ex.: Transportadora XYZ" value={formEntrada.entregue_por}
              onChange={(e) => setFormEntrada({ ...formEntrada, entregue_por: e.target.value })} />
            <Input label="Recebido por (no estoque)" placeholder="ex.: João do Almoxarifado" value={formEntrada.recebido_por}
              onChange={(e) => setFormEntrada({ ...formEntrada, recebido_por: e.target.value })} />
            <div className="sm:col-span-2">
              <Input label="Observação (opcional)" value={formEntrada.observacao}
                onChange={(e) => setFormEntrada({ ...formEntrada, observacao: e.target.value })} />
            </div>
            <div className="sm:col-span-2">
              <FileInput label="Comprovante (nota fiscal, recibo etc.)" accept="image/*,application/pdf" file={arquivoEntrada} onChange={setArquivoEntrada} />
            </div>
            <div className="sm:col-span-4">
              <Button type="submit" disabled={enviandoEntrada || !arquivoEntrada}>
                {enviandoEntrada ? "Registrando…" : "Registrar entrada"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      <Card
        title="Produtos em estoque"
        actions={<Badge variant="accent">{totalProdutos}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(2)}
      >
        <div className="mb-4 sm:max-w-xs">
          <Input label="Buscar por nome" placeholder="Nome do produto" value={filtroNomeProduto} onChange={(e) => setFiltroNomeProduto(e.target.value)} />
        </div>
        {carregandoProdutos ? (
          <Spinner label="Carregando produtos…" />
        ) : totalProdutos === 0 ? (
          <EmptyState message={filtroNomeProduto ? "Nenhum produto encontrado com esse filtro." : "Nenhum produto cadastrado ainda."} />
        ) : (
          <>
            {/* Celular: lista de cards. Telas sm+: tabela. */}
            <ul className="sm:hidden divide-y divide-gray-100">
              {produtos.map((p) => (
                <li key={p.id} className="py-3.5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-gray-800 truncate">{p.nome}</span>
                        {!p.ativo && <Badge variant="gray">Inativo</Badge>}
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5">{p.unidade_medida}</div>
                      {p.descricao && <div className="text-xs text-gray-500 mt-0.5 truncate">{p.descricao}</div>}
                    </div>
                    <Badge variant="brand">{p.saldo_atual}</Badge>
                  </div>
                  <button
                    type="button"
                    className="text-xs text-brand hover:underline mt-1.5"
                    onClick={() => setProdutoDetalhado(produtoDetalhado === p.id ? null : p.id)}
                  >
                    {produtoDetalhado === p.id ? "ocultar saldo por almoxarifado" : "ver saldo por almoxarifado"}
                  </button>
                  {produtoDetalhado === p.id && (
                    <div className="mt-1.5 text-xs text-gray-600 space-y-0.5">
                      {carregandoSaldos ? (
                        <span className="text-gray-400">Carregando…</span>
                      ) : saldosDetalhados.length === 0 ? (
                        <span className="text-gray-400">Nenhuma movimentação em nenhum almoxarifado ainda.</span>
                      ) : (
                        saldosDetalhados.map((s) => (
                          <div key={s.almoxarifado_id} className="flex items-center justify-between gap-2">
                            <span>{s.almoxarifado_nome}</span>
                            <span className="font-medium text-gray-700">{s.saldo}</span>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                  {ehMaster && (
                    <div className="flex items-center gap-5 mt-3">
                      <button type="button" title="Editar" onClick={() => setProdutoEditando(p)} className="text-gray-400 hover:text-brand transition-colors -m-1.5 p-1.5">
                        <PencilIcon className="w-[18px] h-[18px]" />
                      </button>
                      <button type="button" title="Remover" onClick={() => removerProduto(p)} className="text-gray-400 hover:text-red-600 transition-colors -m-1.5 p-1.5">
                        <TrashIcon className="w-[18px] h-[18px]" />
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>

            <div className="hidden sm:block overflow-x-auto -mx-5 sm:-mx-8">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                    <th className="py-2.5 px-8">Nome</th>
                    <th className="px-3">Unidade</th>
                    <th className="px-3">Saldo atual</th>
                    <th className="px-3">Situação</th>
                    {ehMaster && <th className="px-3 text-right pr-8">Ações</th>}
                  </tr>
                </thead>
                <tbody>
                  {produtos.map((p) => (
                    <Fragment key={p.id}>
                      <tr className="border-t border-gray-100 hover:bg-brand-light/60 transition-colors">
                        <td className="py-2.5 px-8 font-medium text-gray-800">{p.nome}</td>
                        <td className="px-3 text-gray-600">{p.unidade_medida}</td>
                        <td className="px-3">
                          <div className="flex items-center gap-2">
                            <Badge variant="brand">{p.saldo_atual}</Badge>
                            <button
                              type="button"
                              className="text-xs text-brand hover:underline"
                              onClick={() => setProdutoDetalhado(produtoDetalhado === p.id ? null : p.id)}
                            >
                              {produtoDetalhado === p.id ? "ocultar" : "por almoxarifado"}
                            </button>
                          </div>
                        </td>
                        <td className="px-3"><Badge variant={p.ativo ? "accent" : "gray"}>{p.ativo ? "Ativo" : "Inativo"}</Badge></td>
                        {ehMaster && (
                          <td className="px-3 text-right pr-8">
                            <div className="flex items-center justify-end gap-3">
                              <button type="button" title="Editar" onClick={() => setProdutoEditando(p)} className="text-gray-400 hover:text-brand transition-colors">
                                <PencilIcon />
                              </button>
                              <button type="button" title="Remover" onClick={() => removerProduto(p)} className="text-gray-400 hover:text-red-600 transition-colors">
                                <TrashIcon />
                              </button>
                            </div>
                          </td>
                        )}
                      </tr>
                      {produtoDetalhado === p.id && (
                        <tr className="bg-brand-light/40">
                          <td colSpan={ehMaster ? 5 : 4} className="px-8 py-3">
                            {carregandoSaldos ? (
                              <span className="text-xs text-gray-400">Carregando…</span>
                            ) : saldosDetalhados.length === 0 ? (
                              <span className="text-xs text-gray-400">Nenhuma movimentação em nenhum almoxarifado ainda.</span>
                            ) : (
                              <div className="flex flex-wrap gap-x-6 gap-y-1">
                                {saldosDetalhados.map((s) => (
                                  <div key={s.almoxarifado_id} className="text-xs text-gray-600">
                                    <span className="text-gray-500">{s.almoxarifado_nome}:</span>{" "}
                                    <span className="font-medium text-gray-800">{s.saldo}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        <Paginacao pagina={paginaProdutos} tamanhoPagina={TAMANHO_PAGINA} total={totalProdutos} onChange={setPaginaProdutos} />
      </Card>

      <Card
        title="Movimentações"
        actions={<Badge variant="accent">{totalMovs}</Badge>}
        className="animate-fade-in-up"
        style={staggerStyle(3)}
      >
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
          <Select label="Filtrar por produto" value={filtroProdutoMov} onChange={(e) => setFiltroProdutoMov(e.target.value)}>
            <option value="">Todos os produtos</option>
            {produtosAtivos.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
          </Select>
          <Select label="Filtrar por almoxarifado" value={filtroAlmoxarifadoMov} onChange={(e) => setFiltroAlmoxarifadoMov(e.target.value)}>
            <option value="">Todos os almoxarifados</option>
            {almoxarifados.map((a) => <option key={a.id} value={a.id}>{a.nome}</option>)}
          </Select>
          <Select label="Filtrar por tipo" value={filtroTipoMov} onChange={(e) => setFiltroTipoMov(e.target.value)}>
            <option value="">Entradas e Saídas</option>
            <option value="ENTRADA">Só Entradas</option>
            <option value="SAIDA">Só Saídas</option>
          </Select>
        </div>
        {carregandoMovs ? (
          <Spinner label="Carregando movimentações…" />
        ) : totalMovs === 0 ? (
          <EmptyState message="Nenhuma movimentação registrada ainda." />
        ) : (
          <>
            <ul className="sm:hidden divide-y divide-gray-100">
              {movimentos.map((m) => (
                <li key={m.id} className="py-3.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant={m.tipo === "ENTRADA" ? "accent" : "gray"}>{m.tipo === "ENTRADA" ? "Entrada" : "Saída"}</Badge>
                    <span className="font-medium text-gray-800">{nomeProduto(m.produto_id)}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {m.quantidade} un. · {nomeAlmoxarifado(m.almoxarifado_id)} · {dataBR(m.data)}
                    {m.entrega_material_id ? " · gerado por uma Entrega de Materiais" : ""}
                  </div>
                  {(m.entregue_por || m.recebido_por) && (
                    <div className="text-xs text-gray-500 mt-0.5">
                      {m.entregue_por ? `Entregue por: ${m.entregue_por}` : ""}
                      {m.entregue_por && m.recebido_por ? " · " : ""}
                      {m.recebido_por ? `Recebido por: ${m.recebido_por}` : ""}
                    </div>
                  )}
                  {m.observacao && <div className="text-sm text-gray-600 mt-0.5">{m.observacao}</div>}
                  <div className="flex flex-wrap gap-2 mt-2">
                    {m.nome_arquivo && (
                      <Button variant="secondary" onClick={() => baixarArquivoMovimento(m)} disabled={baixando === m.id}>
                        {baixando === m.id ? "Abrindo…" : "Ver comprovante"}
                      </Button>
                    )}
                    <Button variant="secondary" onClick={() => setMovimentoTermo(m)}>
                      Gerar termo
                    </Button>
                  </div>
                </li>
              ))}
            </ul>

            <div className="hidden sm:block overflow-x-auto -mx-5 sm:-mx-8">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                    <th className="py-2.5 px-8">Tipo</th>
                    <th className="px-3">Produto</th>
                    <th className="px-3">Almoxarifado</th>
                    <th className="px-3">Quantidade</th>
                    <th className="px-3">Data</th>
                    <th className="px-3">Origem</th>
                    <th className="px-3">Entregue por</th>
                    <th className="px-3">Recebido por</th>
                    <th className="px-3 text-right pr-8">Comprovante</th>
                    <th className="px-3 text-right pr-8">Termo</th>
                  </tr>
                </thead>
                <tbody>
                  {movimentos.map((m) => (
                    <tr key={m.id} className="border-t border-gray-100 hover:bg-brand-light/60 transition-colors">
                      <td className="py-2.5 px-8"><Badge variant={m.tipo === "ENTRADA" ? "accent" : "gray"}>{m.tipo === "ENTRADA" ? "Entrada" : "Saída"}</Badge></td>
                      <td className="px-3 text-gray-600">{nomeProduto(m.produto_id)}</td>
                      <td className="px-3 text-gray-600">{nomeAlmoxarifado(m.almoxarifado_id)}</td>
                      <td className="px-3 text-gray-600">{m.quantidade}</td>
                      <td className="px-3 text-gray-600">{dataBR(m.data)}</td>
                      <td className="px-3 text-gray-500 text-xs">{m.entrega_material_id ? "Entrega de Materiais" : "—"}</td>
                      <td className="px-3 text-gray-600">{m.entregue_por ?? "—"}</td>
                      <td className="px-3 text-gray-600">{m.recebido_por ?? "—"}</td>
                      <td className="px-3 text-right pr-8">
                        {m.nome_arquivo ? (
                          <Button variant="secondary" onClick={() => baixarArquivoMovimento(m)} disabled={baixando === m.id}>
                            {baixando === m.id ? "Abrindo…" : "Ver"}
                          </Button>
                        ) : (
                          <span className="text-gray-400 text-xs">—</span>
                        )}
                      </td>
                      <td className="px-3 text-right pr-8">
                        <button
                          type="button"
                          title="Gerar Termo de Retirada e Recebimento"
                          onClick={() => setMovimentoTermo(m)}
                          className="text-gray-400 hover:text-brand transition-colors"
                        >
                          <DocumentTextIcon />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        <Paginacao pagina={paginaMovs} tamanhoPagina={TAMANHO_PAGINA} total={totalMovs} onChange={setPaginaMovs} />
      </Card>

      <EditarProdutoModal
        produto={produtoEditando}
        onClose={() => setProdutoEditando(null)}
        onSalvo={() => {
          setProdutoEditando(null);
          toast.success("Alterações salvas.");
          queryClient.invalidateQueries({ queryKey: ["produtos"] });
        }}
      />

      <Modal
        open={!!movimentoTermo}
        onClose={() => setMovimentoTermo(null)}
        title="Termo de Retirada e Recebimento"
        maxWidth="max-w-2xl"
      >
        {movimentoTermo && (
          <div className="space-y-4">
            <div ref={termoRef} className="bg-white p-8 text-sm text-gray-800 leading-relaxed">
              <div className="flex items-center gap-3 mb-8">
                <img src="/logo.png" alt="Conexão Esporte" className="w-12 h-12 object-contain" />
                <div>
                  <div className="font-bold text-brand-dark">Conexão Esporte</div>
                  <div className="text-xs text-gray-500">Gestão de projetos esportivos</div>
                </div>
              </div>

              <h1 className="text-center font-bold text-base uppercase tracking-wide mb-8">
                Termo de Retirada e Recebimento de Material
              </h1>

              <p className="mb-6">
                Registro de <strong>{movimentoTermo.tipo === "ENTRADA" ? "entrada" : "saída"}</strong> de material no
                almoxarifado <strong>{nomeAlmoxarifado(movimentoTermo.almoxarifado_id)}</strong>, referente ao produto{" "}
                <strong>{nomeProduto(movimentoTermo.produto_id)}</strong>, quantidade{" "}
                <strong>{movimentoTermo.quantidade}</strong>, na data <strong>{dataBR(movimentoTermo.data)}</strong>.
                {movimentoTermo.observacao ? ` Observação: ${movimentoTermo.observacao}` : ""}
              </p>

              <div className="grid grid-cols-2 gap-10 mt-16">
                <div className="text-center">
                  <div className="border-t border-gray-400 mb-1" />
                  <div>{movimentoTermo.tipo === "ENTRADA" ? "Entregue por" : "Retirado por"}</div>
                  <div className="text-gray-500">{movimentoTermo.entregue_por || "________________________"}</div>
                </div>
                <div className="text-center">
                  <div className="border-t border-gray-400 mb-1" />
                  <div>Recebido por (almoxarifado)</div>
                  <div className="text-gray-500">{movimentoTermo.recebido_por || "________________________"}</div>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <Button onClick={baixarTermo} disabled={exportandoTermo}>
                {exportandoTermo ? "Gerando…" : "Baixar PDF"}
              </Button>
              <Button variant="secondary" type="button" onClick={() => setMovimentoTermo(null)}>
                Fechar
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {ehMaster && (
        <ImportarPlanilhaModal
          aberto={importarAberto}
          onFechar={() => setImportarAberto(false)}
          recurso="produtos"
          titulo="Importar produtos"
          nomeArquivoModelo="modelo-importacao-produtos.xlsx"
          onImportado={() => queryClient.invalidateQueries({ queryKey: ["produtos"] })}
        />
      )}
    </div>
  );
}
