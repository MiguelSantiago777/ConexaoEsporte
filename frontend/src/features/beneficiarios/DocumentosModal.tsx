import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Beneficiario } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
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
  certidao_nascimento_ou_identidade: "Certidão de nascimento ou identidade",
  identidade_responsavel: "Identidade do responsável",
  comprovante_residencia: "Comprovante de residência",
  comprovante_escolar: "Comprovante escolar",
};

export function DocumentosModal({
  beneficiario,
  onClose,
}: {
  beneficiario: Beneficiario | null;
  onClose: () => void;
}) {
  const toast = useToast();
  const [baixando, setBaixando] = useState<string | null>(null);

  const { data: documentos = [], isLoading: carregando, isError } = useQuery({
    queryKey: ["beneficiarios", beneficiario?.id, "documentos"],
    queryFn: () =>
      api.get<DocumentoAnexo[]>(`/beneficiarios/${beneficiario!.id}/documentos`).then((r) => r.data),
    enabled: !!beneficiario,
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
            <li key={doc.id} className="py-3 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="text-sm font-medium text-gray-800 truncate">{TIPO_LABEL[doc.tipo] ?? doc.tipo}</div>
                <div className="text-xs text-gray-400 truncate">{doc.nome_arquivo}</div>
              </div>
              <Button variant="secondary" type="button" onClick={() => baixar(doc)} disabled={baixando === doc.id}>
                {baixando === doc.id ? "Baixando…" : "Baixar"}
              </Button>
            </li>
          ))}
        </ul>
      )}
    </Modal>
  );
}
