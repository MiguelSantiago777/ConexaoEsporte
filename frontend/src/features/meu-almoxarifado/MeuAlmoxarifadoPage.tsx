import { FormEvent, useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { MovimentoEstoque, Pagina, Produto, SaldoProdutoNoAlmoxarifado } from "@/types";
import { useAuth } from "@/features/auth/AuthContext";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { FileInput } from "@/components/ui/FileInput";
import { PageHeader } from "@/components/ui/PageHeader";
import { Paginacao } from "@/components/ui/Paginacao";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";
import { dataBR } from "@/features/frequencia/statusChamada";

const TAMANHO_PAGINA = 10;
const FORM_ENTRADA_INICIAL = { produto_id: "", quantidade: "", data: "", observacao: "", entregue_por: "", recebido_por: "" };

function hoje() {
  return new Date().toISOString().slice(0, 10);
}

/** Estoque do Coordenador de Almoxarifado — igual à tela de Estoque do
 * MASTER, mas sempre restrita ao almoxarifado vinculado ao próprio usuário
 * (o backend já força esse escopo em toda rota de /movimentos-estoque e
 * /almoxarifados; aqui a UI só não dá a opção de escolher outro). */
export function MeuAlmoxarifadoPage() {
  const { usuario } = useAuth();
  const toast = useToast();
  const queryClient = useQueryClient();
  const almoxarifadoId = usuario?.almoxarifado_id ?? "";

  const { data: produtosAtivos = [] } = useQuery({
    queryKey: ["produtos", "ativos"],
    queryFn: () => api.get<Produto[]>("/produtos", { params: { apenas_ativos: true } }).then((r) => r.data),
  });

  const { data: saldos = [], isLoading: carregandoSaldos } = useQuery({
    queryKey: ["almoxarifados", almoxarifadoId, "saldos"],
    queryFn: () => api.get<SaldoProdutoNoAlmoxarifado[]>(`/almoxarifados/${almoxarifadoId}/saldos`).then((r) => r.data),
    enabled: !!almoxarifadoId,
  });

  // --- Registrar entrada ---
  const [formEntrada, setFormEntrada] = useState({ ...FORM_ENTRADA_INICIAL, data: hoje() });
  const [arquivoEntrada, setArquivoEntrada] = useState<File | null>(null);
  const [enviandoEntrada, setEnviandoEntrada] = useState(false);

  async function registrarEntrada(e: FormEvent) {
    e.preventDefault();
    if (!arquivoEntrada || !almoxarifadoId) return;
    setEnviandoEntrada(true);
    try {
      const dados = new FormData();
      dados.append("produto_id", formEntrada.produto_id);
      dados.append("almoxarifado_id", almoxarifadoId);
      dados.append("quantidade", formEntrada.quantidade);
      dados.append("data", formEntrada.data);
      if (formEntrada.observacao) dados.append("observacao", formEntrada.observacao);
      if (formEntrada.entregue_por) dados.append("entregue_por", formEntrada.entregue_por);
      if (formEntrada.recebido_por) dados.append("recebido_por", formEntrada.recebido_por);
      dados.append("arquivo", arquivoEntrada);
      await api.post("/movimentos-estoque", dados);
      setFormEntrada({ ...FORM_ENTRADA_INICIAL, data: hoje() });
      setArquivoEntrada(null);
      toast.success("Entrada registrada com sucesso.");
      queryClient.invalidateQueries({ queryKey: ["almoxarifados", almoxarifadoId, "saldos"] });
      queryClient.invalidateQueries({ queryKey: ["movimentos-estoque"] });
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao registrar entrada."));
    } finally {
      setEnviandoEntrada(false);
    }
  }

  // --- Movimentações (paginado, com filtros — o backend já restringe ao
  // próprio almoxarifado, mesmo sem informar o filtro). ---
  const [filtroProdutoMov, setFiltroProdutoMov] = useState("");
  const [filtroTipoMov, setFiltroTipoMov] = useState("");
  const [paginaMovs, setPaginaMovs] = useState(1);

  useEffect(() => setPaginaMovs(1), [filtroProdutoMov, filtroTipoMov]);

  const { data: paginaMovsResp, isLoading: carregandoMovs } = useQuery({
    queryKey: ["movimentos-estoque", "pagina", paginaMovs, filtroProdutoMov, filtroTipoMov],
    queryFn: () =>
      api
        .get<Pagina<MovimentoEstoque>>("/movimentos-estoque", {
          params: { pagina: paginaMovs, tamanho_pagina: TAMANHO_PAGINA, produto_id: filtroProdutoMov || undefined, tipo: filtroTipoMov || undefined },
        })
        .then((r) => r.data),
  });
  const movimentos = paginaMovsResp?.itens ?? [];
  const totalMovs = paginaMovsResp?.total ?? 0;

  function nomeProduto(id: string) {
    return produtosAtivos.find((p) => p.id === id)?.nome ?? saldos.find((s) => s.produto_id === id)?.produto_nome ?? "—";
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
        title="Meu Almoxarifado"
        subtitle={
          usuario?.almoxarifado_nome
            ? `Você opera o estoque de "${usuario.almoxarifado_nome}" — registre a Entrada com a nota fiscal ou comprovante.`
            : "Registre a Entrada de produtos no seu almoxarifado."
        }
      />

      <Card
        title="Registrar entrada"
        subtitle="Nota fiscal ou comprovante da compra/recebimento é obrigatório — fica anexado ao movimento, junto de quem entregou e quem recebeu."
        className="animate-fade-in-up"
        style={staggerStyle(0)}
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
          <Input label="Quantidade" type="number" min={1} placeholder="ex.: 50" value={formEntrada.quantidade}
            onChange={(e) => setFormEntrada({ ...formEntrada, quantidade: e.target.value })} required />
          <Input label="Data" type="date" value={formEntrada.data}
            onChange={(e) => setFormEntrada({ ...formEntrada, data: e.target.value })} required />
          <Input label="Entregue por" placeholder="ex.: Transportadora XYZ" value={formEntrada.entregue_por}
            onChange={(e) => setFormEntrada({ ...formEntrada, entregue_por: e.target.value })} />
          <Input label="Recebido por" placeholder="ex.: seu nome" value={formEntrada.recebido_por}
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

      <Card title="Saldo dos produtos" actions={<Badge variant="accent">{saldos.length}</Badge>} className="animate-fade-in-up" style={staggerStyle(1)}>
        {carregandoSaldos ? (
          <Spinner label="Carregando saldos…" />
        ) : saldos.length === 0 ? (
          <EmptyState message="Nenhuma movimentação registrada ainda neste almoxarifado." />
        ) : (
          <ul className="divide-y divide-gray-100">
            {saldos.map((s) => (
              <li key={s.produto_id} className="py-3 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <span className="font-medium text-gray-800 truncate">{s.produto_nome}</span>
                  <span className="text-gray-500 text-sm ml-2">{s.unidade_medida}</span>
                </div>
                <Badge variant="brand">{s.saldo}</Badge>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card title="Movimentações" actions={<Badge variant="accent">{totalMovs}</Badge>} className="animate-fade-in-up" style={staggerStyle(2)}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <Select label="Filtrar por produto" value={filtroProdutoMov} onChange={(e) => setFiltroProdutoMov(e.target.value)}>
            <option value="">Todos os produtos</option>
            {produtosAtivos.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
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
                    {m.quantidade} un. · {dataBR(m.data)}
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
                  {m.nome_arquivo && (
                    <Button variant="secondary" className="mt-2" onClick={() => baixarArquivoMovimento(m)} disabled={baixando === m.id}>
                      {baixando === m.id ? "Abrindo…" : "Ver comprovante"}
                    </Button>
                  )}
                </li>
              ))}
            </ul>

            <div className="hidden sm:block overflow-x-auto -mx-5 sm:-mx-8">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-brand-dark/70 bg-brand-light">
                    <th className="py-2.5 px-8">Tipo</th>
                    <th className="px-3">Produto</th>
                    <th className="px-3">Quantidade</th>
                    <th className="px-3">Data</th>
                    <th className="px-3">Origem</th>
                    <th className="px-3">Entregue por</th>
                    <th className="px-3">Recebido por</th>
                    <th className="px-3 text-right pr-8">Comprovante</th>
                  </tr>
                </thead>
                <tbody>
                  {movimentos.map((m) => (
                    <tr key={m.id} className="border-t border-gray-100 hover:bg-brand-light/60 transition-colors">
                      <td className="py-2.5 px-8"><Badge variant={m.tipo === "ENTRADA" ? "accent" : "gray"}>{m.tipo === "ENTRADA" ? "Entrada" : "Saída"}</Badge></td>
                      <td className="px-3 text-gray-600">{nomeProduto(m.produto_id)}</td>
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
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        <Paginacao pagina={paginaMovs} tamanhoPagina={TAMANHO_PAGINA} total={totalMovs} onChange={setPaginaMovs} />
      </Card>
    </div>
  );
}
