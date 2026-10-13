import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { Beneficiario } from "@/types";
import { useAuth } from "@/features/auth/AuthContext";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { FileInput } from "@/components/ui/FileInput";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";

interface DocumentoAnexo {
  id: string;
  beneficiario_id: string;
  tipo: string;
  nome_arquivo: string;
  content_type: string | null;
  tamanho_bytes: number | null;
  criado_em: string | null;
}

const TIPO_LABEL: Record<string, string> = {
  foto: "Foto",
  certidao_nascimento_ou_identidade: "Certidão de nascimento ou identidade",
  identidade_responsavel: "Identidade do responsável",
  comprovante_residencia: "Comprovante de residência",
  comprovante_escolar: "Comprovante escolar",
};

const TIPOS_DOCUMENTO = Object.keys(TIPO_LABEL);

/** Lista, download e remoção (só MASTER — pra substituir um documento
 * enviado errado) dos documentos de um beneficiário. */
function useDocumentosBeneficiario(beneficiarioId: string | undefined) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [baixando, setBaixando] = useState<string | null>(null);
  const queryKey = ["beneficiarios", beneficiarioId, "documentos"];

  const query = useQuery({
    queryKey,
    queryFn: () => api.get<DocumentoAnexo[]>(`/beneficiarios/${beneficiarioId}/documentos`).then((r) => r.data),
    enabled: !!beneficiarioId,
  });

  const removerMutation = useMutation({
    mutationFn: (documentoId: string) => api.delete(`/beneficiarios/documentos/${documentoId}`),
    onSuccess: () => {
      toast.success("Documento removido.");
      queryClient.invalidateQueries({ queryKey });
    },
    onError: (err: unknown) => toast.error(mensagemErroApi(err, "Erro ao remover documento.")),
  });

  async function baixar(doc: DocumentoAnexo) {
    setBaixando(doc.id);
    try {
      const resp = await api.get(`/beneficiarios/documentos/${doc.id}/arquivo`, { responseType: "blob" });
      const url = window.URL.createObjectURL(resp.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = doc.nome_arquivo;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error("Não foi possível baixar o documento.");
    } finally {
      setBaixando(null);
    }
  }

  function remover(doc: DocumentoAnexo) {
    if (window.confirm(`Remover "${doc.nome_arquivo}"? Depois você poderá anexar outro no lugar.`)) {
      removerMutation.mutate(doc.id);
    }
  }

  return { query, queryKey, baixar, baixando, remover, removendo: removerMutation.isPending };
}

function LinhaDocumento({
  doc,
  titulo,
  baixando,
  podeRemover,
  removendo,
  onBaixar,
  onRemover,
}: {
  doc: DocumentoAnexo;
  titulo: string;
  baixando: boolean;
  podeRemover: boolean;
  removendo: boolean;
  onBaixar: () => void;
  onRemover: () => void;
}) {
  return (
    <li className="py-3 flex items-center justify-between gap-3">
      <div className="min-w-0">
        <div className="text-sm font-medium text-gray-800 truncate">{titulo}</div>
        <div className="text-xs text-gray-400 truncate">{doc.nome_arquivo}</div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <Button variant="secondary" type="button" onClick={onBaixar} disabled={baixando}>
          {baixando ? "Baixando…" : "Baixar"}
        </Button>
        {podeRemover && (
          <button
            type="button"
            onClick={onRemover}
            disabled={removendo}
            className="text-gray-400 hover:text-red-600 transition-colors text-sm px-2 disabled:opacity-50"
          >
            Remover
          </button>
        )}
      </div>
    </li>
  );
}

export function DocumentosModal({
  beneficiario,
  onClose,
}: {
  beneficiario: Beneficiario | null;
  onClose: () => void;
}) {
  const { usuario } = useAuth();
  const ehMaster = usuario?.perfil === "MASTER";
  const { query, baixar, baixando, remover, removendo } = useDocumentosBeneficiario(beneficiario?.id);
  const { data: documentos = [], isLoading: carregando, isError } = query;

  return (
    <Modal open={!!beneficiario} onClose={onClose} title={beneficiario ? `Documentos — ${beneficiario.nome_completo}` : ""}>
      {carregando ? (
        <Spinner label="Carregando documentos…" />
      ) : isError ? (
        <EmptyState message="Não foi possível carregar os documentos." />
      ) : documentos.length === 0 ? (
        <EmptyState message="Nenhum documento anexado ainda." />
      ) : (
        <ul className="divide-y divide-gray-100">
          {documentos.map((doc) => (
            <LinhaDocumento
              key={doc.id}
              doc={doc}
              titulo={TIPO_LABEL[doc.tipo] ?? doc.tipo}
              baixando={baixando === doc.id}
              podeRemover={ehMaster}
              removendo={removendo}
              onBaixar={() => baixar(doc)}
              onRemover={() => remover(doc)}
            />
          ))}
        </ul>
      )}
    </Modal>
  );
}

/** Aba "Documentos" do modal de edição: mostra o que já foi anexado e
 * permite anexar os documentos do cadastro que ainda estão faltando. */
export function DocumentosBeneficiarioTab({ beneficiarioId }: { beneficiarioId: string }) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const { usuario } = useAuth();
  const ehMaster = usuario?.perfil === "MASTER";
  const { query, queryKey, baixar, baixando, remover, removendo } = useDocumentosBeneficiario(beneficiarioId);
  const { data: documentos = [], isLoading, isError } = query;
  const [arquivos, setArquivos] = useState<Record<string, File | null>>({});

  const selecionados = Object.entries(arquivos).filter(([, f]) => f) as [string, File][];

  const enviarMutation = useMutation({
    mutationFn: () => {
      const dados = new FormData();
      selecionados.forEach(([tipo, arquivo]) => dados.append(tipo, arquivo));
      // Não define Content-Type manualmente: o navegador precisa gerar o boundary do multipart.
      return api.post(`/beneficiarios/${beneficiarioId}/documentos`, dados);
    },
    onSuccess: () => {
      toast.success(selecionados.length > 1 ? "Documentos anexados." : "Documento anexado.");
      setArquivos({});
      queryClient.invalidateQueries({ queryKey });
    },
    onError: (err: unknown) => toast.error(mensagemErroApi(err, "Erro ao anexar documentos.")),
  });

  if (isLoading) return <Spinner label="Carregando documentos…" />;
  if (isError) return <EmptyState message="Não foi possível carregar os documentos." />;

  const tiposFaltando = TIPOS_DOCUMENTO.filter((tipo) => !documentos.some((d) => d.tipo === tipo));

  return (
    <div className="space-y-4">
      {documentos.length > 0 && (
        <ul className="divide-y divide-gray-100">
          {documentos.map((doc) => (
            <LinhaDocumento
              key={doc.id}
              doc={doc}
              titulo={TIPO_LABEL[doc.tipo] ?? doc.tipo}
              baixando={baixando === doc.id}
              podeRemover={ehMaster}
              removendo={removendo}
              onBaixar={() => baixar(doc)}
              onRemover={() => remover(doc)}
            />
          ))}
        </ul>
      )}

      {tiposFaltando.length === 0 ? (
        <p className="text-sm text-gray-500">
          Todos os documentos do cadastro já foram anexados.
          {ehMaster && " Para substituir um, remova-o e anexe o novo."}
        </p>
      ) : (
        <div className={`space-y-4 ${documentos.length > 0 ? "pt-4 border-t border-gray-100" : ""}`}>
          <p className="text-sm font-medium text-gray-700">Documentos pendentes</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {tiposFaltando.map((tipo) => (
              <FileInput
                key={tipo}
                label={TIPO_LABEL[tipo]}
                accept="image/*,application/pdf"
                file={arquivos[tipo] ?? null}
                onChange={(f) => setArquivos((atual) => ({ ...atual, [tipo]: f }))}
              />
            ))}
          </div>
          <Button
            type="button"
            onClick={() => enviarMutation.mutate()}
            disabled={selecionados.length === 0 || enviarMutation.isPending}
          >
            {enviarMutation.isPending ? "Enviando…" : "Anexar documentos"}
          </Button>
        </div>
      )}
    </div>
  );
}
