import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { EntregaMaterial } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { FileInput } from "@/components/ui/FileInput";
import { useToast } from "@/components/ui/toast/ToastContext";

interface Props {
  entrega: EntregaMaterial | null;
  onClose: () => void;
  onSalvo: () => void;
}

/** Fecha o processo entrada -> saída -> recebimento no polo: anexa a foto
 * ou o PDF assinado comprovando que o polo recebeu os materiais, e registra
 * o nome de quem de fato assinou o recebimento (pré-preenchido com o
 * coordenador cadastrado do polo, mas editável — pode ter sido outra
 * pessoa quem recebeu de verdade). */
export function ConfirmarRecebimentoModal({ entrega, onClose, onSalvo }: Props) {
  const toast = useToast();
  const [recebidoPor, setRecebidoPor] = useState("");
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (entrega) {
      setRecebidoPor(entrega.coordenador_nome ?? "");
      setArquivo(null);
    }
  }, [entrega]);

  if (!entrega) return null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!arquivo || !entrega) return;
    setEnviando(true);
    try {
      const dados = new FormData();
      dados.append("arquivo", arquivo);
      if (recebidoPor.trim()) dados.append("recebido_por", recebidoPor.trim());
      await api.post(`/entregas-materiais/${entrega.id}/comprovante`, dados);
      onSalvo();
    } catch (err: any) {
      toast.error(mensagemErroApi(err, "Erro ao anexar o comprovante."));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Modal open={!!entrega} onClose={onClose} title="Confirmar recebimento no polo">
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-sm text-gray-500">
          Anexe a foto ou o PDF assinado comprovando que o polo recebeu os materiais, e confirme quem assinou o recebimento.
        </p>
        <Input label="Recebido por" placeholder="Nome de quem recebeu no polo" value={recebidoPor} onChange={(e) => setRecebidoPor(e.target.value)} />
        <FileInput label="Comprovante (foto ou PDF assinado)" accept="image/*,application/pdf" file={arquivo} onChange={setArquivo} />
        <div className="flex flex-wrap gap-3">
          <Button type="submit" disabled={!arquivo || enviando}>
            {enviando ? "Enviando…" : "Confirmar recebimento"}
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
        </div>
      </form>
    </Modal>
  );
}
