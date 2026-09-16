import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { baixarModeloImportacao, enviarPlanilhaImportacao } from "@/lib/importacaoService";
import { mensagemErroApi } from "@/lib/erros";
import type { ResultadoImportacao } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { FileInput } from "@/components/ui/FileInput";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/components/ui/toast/ToastContext";
import { ResultadoImportacaoTable } from "./ResultadoImportacaoTable";

interface Props {
  aberto: boolean;
  onFechar: () => void;
  /** Nome do recurso na URL da API — "beneficiarios", "turmas", "usuarios", "produtos" ou "polos". */
  recurso: string;
  titulo: string;
  nomeArquivoModelo: string;
  /** Chamado depois de uma confirmação com pelo menos 1 linha gravada — o
   * chamador invalida as queries da própria listagem. */
  onImportado: () => void;
}

/**
 * Fluxo genérico de importação em massa por planilha, reaproveitado pelas 5
 * telas de cadastro (Beneficiários, Turmas, Professores, Produtos, Polos):
 * baixar modelo → escolher arquivo preenchido → ver a prévia (nada é
 * gravado ainda) → confirmar (grava as linhas válidas, pula as com erro).
 */
export function ImportarPlanilhaModal({ aberto, onFechar, recurso, titulo, nomeArquivoModelo, onImportado }: Props) {
  const toast = useToast();
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [resultado, setResultado] = useState<ResultadoImportacao | null>(null);

  // Começa do zero toda vez que o modal reabre — mesmo padrão de "ajustar
  // estado a partir de uma prop" usado em EditarBeneficiarioModal, em vez de
  // um useEffect (evita o cascading render que o reset síncrono causaria).
  const [abertoAnterior, setAbertoAnterior] = useState(aberto);
  if (aberto !== abertoAnterior) {
    setAbertoAnterior(aberto);
    if (aberto) {
      setArquivo(null);
      setResultado(null);
    }
  }

  const previaMutation = useMutation({
    mutationFn: (arquivo: File) => enviarPlanilhaImportacao(recurso, arquivo, false),
    onSuccess: (res) => setResultado(res),
    onError: (err: unknown) => toast.error(mensagemErroApi(err, "Não foi possível ler a planilha.")),
  });

  const confirmarMutation = useMutation({
    mutationFn: (arquivo: File) => enviarPlanilhaImportacao(recurso, arquivo, true),
    onSuccess: (res) => {
      setResultado(res);
      if (res.sucesso > 0) {
        toast.success(
          res.falha > 0
            ? `${res.sucesso} registro(s) importado(s), ${res.falha} com erro.`
            : `${res.sucesso} registro(s) importado(s) com sucesso.`
        );
        onImportado();
      } else {
        toast.error("Nenhuma linha pôde ser importada — confira os erros abaixo.");
      }
    },
    onError: (err: unknown) => toast.error(mensagemErroApi(err, "Não foi possível importar a planilha.")),
  });

  const etapaPrevia = resultado === null;

  return (
    <Modal open={aberto} onClose={onFechar} title={titulo} maxWidth="max-w-2xl">
      <div className="space-y-5">
        {etapaPrevia ? (
          <>
            <p className="text-sm text-slate-500">
              Baixe o modelo, preencha uma linha por registro e envie o arquivo de volta — a aba
              "Instruções" da planilha explica cada coluna.
            </p>
            <Button
              type="button"
              variant="secondary"
              onClick={() => baixarModeloImportacao(recurso, nomeArquivoModelo)}
            >
              Baixar modelo (.xlsx)
            </Button>
            <FileInput
              label="Planilha preenchida"
              file={arquivo}
              onChange={setArquivo}
              accept=".xlsx"
            />
            <div className="flex justify-end gap-3 pt-2 border-t border-slate-300/60">
              <Button type="button" variant="secondary" onClick={onFechar}>
                Cancelar
              </Button>
              <Button
                type="button"
                disabled={!arquivo || previaMutation.isPending}
                onClick={() => arquivo && previaMutation.mutate(arquivo)}
              >
                {previaMutation.isPending ? "Lendo…" : "Ver prévia"}
              </Button>
            </div>
          </>
        ) : (
          <>
            <div className="flex items-center gap-2">
              <Badge variant="court">{resultado.sucesso} válido(s)</Badge>
              {resultado.falha > 0 && <Badge variant="danger">{resultado.falha} com erro</Badge>}
              {resultado.confirmado && <Badge variant="brand">Gravado</Badge>}
            </div>
            <ResultadoImportacaoTable linhas={resultado.linhas} />
            <div className="flex justify-end gap-3 pt-2 border-t border-slate-300/60">
              {resultado.confirmado ? (
                <Button type="button" onClick={onFechar}>
                  Fechar
                </Button>
              ) : (
                <>
                  <Button type="button" variant="secondary" onClick={() => setResultado(null)}>
                    Voltar
                  </Button>
                  <Button
                    type="button"
                    disabled={resultado.sucesso === 0 || confirmarMutation.isPending}
                    onClick={() => arquivo && confirmarMutation.mutate(arquivo)}
                  >
                    {confirmarMutation.isPending ? "Gravando…" : `Confirmar importação (${resultado.sucesso})`}
                  </Button>
                </>
              )}
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
