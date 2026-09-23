import { FormEvent, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Produto } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { FileInput } from "@/components/ui/FileInput";
import { useToast } from "@/components/ui/toast/ToastContext";
import { hoje } from "./datas";

const FORM_INICIAL = { quantidade: "", data: hoje(), observacao: "", entregue_por: "", recebido_por: "" };

interface Props {
  aberto: boolean;
  // Preenchido quando aberto a partir do botão "Entrada" de um produto na
  // lista — o produto fica travado (sem select) pra reduzir cliques. Quando
  // aberto pelo botão genérico "Nova entrada" do card, vem null e o usuário
  // escolhe.
  produtoFixo: Produto | null;
  produtosAtivos: Produto[];
  onClose: () => void;
  onRegistrado: () => void;
}

export function RegistrarEntradaModal({ aberto, produtoFixo, produtosAtivos, onClose, onRegistrado }: Props) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [produtoId, setProdutoId] = useState("");
  const [form, setForm] = useState(FORM_INICIAL);
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [enviando, setEnviando] = useState(false);

  const [estadoAnterior, setEstadoAnterior] = useState({ aberto, produtoFixoId: produtoFixo?.id ?? null });
  const chaveAtual = { aberto, produtoFixoId: produtoFixo?.id ?? null };
  if (estadoAnterior.aberto !== chaveAtual.aberto || estadoAnterior.produtoFixoId !== chaveAtual.produtoFixoId) {
    setEstadoAnterior(chaveAtual);
    if (aberto) {
      setProdutoId(produtoFixo?.id ?? "");
      setForm({ ...FORM_INICIAL, data: hoje() });
      setArquivo(null);
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const pid = produtoFixo?.id ?? produtoId;
    if (!pid) return;
    setEnviando(true);
    try {
      const dados = new FormData();
      dados.append("produto_id", pid);
      dados.append("quantidade", form.quantidade);
      dados.append("data", form.data);
      if (form.observacao) dados.append("observacao", form.observacao);
      if (form.entregue_por) dados.append("entregue_por", form.entregue_por);
      if (form.recebido_por) dados.append("recebido_por", form.recebido_por);
      if (arquivo) dados.append("arquivo", arquivo);
      await api.post("/movimentos-estoque", dados);
      toast.success("Entrada registrada com sucesso.");
      queryClient.invalidateQueries({ queryKey: ["produtos"] });
      queryClient.invalidateQueries({ queryKey: ["movimentos-estoque"] });
      onRegistrado();
    } catch (err: unknown) {
      toast.error(mensagemErroApi(err, "Erro ao registrar entrada."));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Modal open={aberto} onClose={onClose} title={produtoFixo ? `Registrar entrada — ${produtoFixo.nome}` : "Registrar entrada"}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {produtoFixo ? (
          <Input label="Produto" value={`${produtoFixo.nome} (${produtoFixo.unidade_medida})`} disabled />
        ) : (
          <Select label="Produto" value={produtoId} onChange={(e) => setProdutoId(e.target.value)} required>
            <option value="">— Selecione —</option>
            {produtosAtivos.map((p) => (
              <option key={p.id} value={p.id}>{p.nome} ({p.unidade_medida})</option>
            ))}
          </Select>
        )}
        <div className="grid grid-cols-2 gap-4">
          <Input label="Quantidade" type="number" min={1} placeholder="ex.: 50" value={form.quantidade}
            onChange={(e) => setForm({ ...form, quantidade: e.target.value })} required />
          <Input label="Data" type="date" value={form.data}
            onChange={(e) => setForm({ ...form, data: e.target.value })} required />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input label="Entregue por (opcional)" placeholder="ex.: Transportadora XYZ" value={form.entregue_por}
            onChange={(e) => setForm({ ...form, entregue_por: e.target.value })} />
          <Input label="Recebido por (opcional)" placeholder="ex.: João do Estoque" value={form.recebido_por}
            onChange={(e) => setForm({ ...form, recebido_por: e.target.value })} />
        </div>
        <Input label="Observação (opcional)" value={form.observacao}
          onChange={(e) => setForm({ ...form, observacao: e.target.value })} />
        <FileInput label="Comprovante — nota fiscal, recibo etc. (opcional)" accept="image/*,application/pdf" file={arquivo} onChange={setArquivo} />
        <div className="flex flex-wrap gap-3">
          <Button type="submit" disabled={enviando}>
            {enviando ? "Registrando…" : "Registrar entrada"}
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
        </div>
      </form>
    </Modal>
  );
}
