import { FormEvent, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Polo, Produto } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useToast } from "@/components/ui/toast/ToastContext";
import { hoje } from "./datas";

const FORM_INICIAL = { quantidade: "", polo_id: "", data: hoje(), recebido_por: "", observacao: "" };

interface Props {
  // Produto do qual sai o material — o modal só abre a partir do botão
  // "Dar baixa" de um produto na lista, então ele vem sempre definido.
  produto: Produto | null;
  polos: Polo[];
  onClose: () => void;
  onRegistrado: () => void;
}

/** Saída direta do estoque: quanto sai e pra qual polo vai. */
export function DarBaixaModal({ produto, polos, onClose, onRegistrado }: Props) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [form, setForm] = useState(FORM_INICIAL);
  const [enviando, setEnviando] = useState(false);

  const [produtoAnterior, setProdutoAnterior] = useState(produto);
  if (produto !== produtoAnterior) {
    setProdutoAnterior(produto);
    if (produto) setForm({ ...FORM_INICIAL, data: hoje() });
  }

  if (!produto) return null;

  const quantidade = Number(form.quantidade);
  const acimaDoSaldo = quantidade > produto.saldo_atual;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!produto || acimaDoSaldo) return;
    setEnviando(true);
    try {
      await api.post("/movimentos-estoque/baixa", {
        produto_id: produto.id,
        polo_id: form.polo_id,
        quantidade,
        data: form.data,
        recebido_por: form.recebido_por || null,
        observacao: form.observacao || null,
      });
      toast.success("Baixa registrada com sucesso.");
      queryClient.invalidateQueries({ queryKey: ["produtos"] });
      queryClient.invalidateQueries({ queryKey: ["movimentos-estoque"] });
      onRegistrado();
    } catch (err: unknown) {
      toast.error(mensagemErroApi(err, "Erro ao dar baixa."));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Modal open={!!produto} onClose={onClose} title={`Dar baixa — ${produto.nome}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-sm text-gray-600">
          Em estoque agora: <strong className="text-gray-800">{produto.saldo_atual} {produto.unidade_medida}</strong>
        </p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Input label="Quantidade que sai" type="number" min={1} max={produto.saldo_atual} placeholder="ex.: 10"
              value={form.quantidade} onChange={(e) => setForm({ ...form, quantidade: e.target.value })} required />
            {acimaDoSaldo && (
              <span className="block text-xs text-red-600 mt-1">Maior que o disponível em estoque.</span>
            )}
          </div>
          <Input label="Data" type="date" value={form.data}
            onChange={(e) => setForm({ ...form, data: e.target.value })} required />
        </div>
        <Select label="Para onde vai (polo)" value={form.polo_id}
          onChange={(e) => setForm({ ...form, polo_id: e.target.value })} required>
          <option value="">— Selecione o polo —</option>
          {polos.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
        </Select>
        <Input label="Quem retirou / recebeu (opcional)" placeholder="ex.: Maria, coordenadora do polo" value={form.recebido_por}
          onChange={(e) => setForm({ ...form, recebido_por: e.target.value })} />
        <Input label="Observação (opcional)" value={form.observacao}
          onChange={(e) => setForm({ ...form, observacao: e.target.value })} />
        <div className="flex flex-wrap gap-3">
          <Button type="submit" disabled={enviando || acimaDoSaldo || produto.saldo_atual === 0}>
            {enviando ? "Registrando…" : "Confirmar baixa"}
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
        </div>
      </form>
    </Modal>
  );
}
