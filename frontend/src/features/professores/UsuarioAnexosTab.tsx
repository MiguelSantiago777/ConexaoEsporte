import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { UsuarioDocumento } from "@/types";
import { Button } from "@/components/ui/Button";
import { FileInput } from "@/components/ui/FileInput";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/components/ui/toast/ToastContext";

export function UsuarioAnexosTab({
  usuarioId,
  tipo,
  label,
}: {
  usuarioId: string;
  tipo: "FOTO" | "DOCUMENTO" | "CONTRATO";
  label: string;
}) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [baixando, setBaixando] = useState<string | null>(null);

  const queryKey = ["usuarios", usuarioId, "documentos"];
  const { data: documentos = [], isLoading } = useQuery({
    queryKey,
    queryFn: () => api.get<UsuarioDocumento[]>(`/usuarios/${usuarioId}/documentos`).then((r) => r.data),
  });
  const documentosDoTipo = documentos.filter((d) => d.tipo === tipo);

  const enviarMutation = useMutation({
    mutationFn: () => {
      const dados = new FormData();
      dados.append("tipo", tipo);
      dados.append("arquivo", arquivo as File);
      return api.post(`/usuarios/${usuarioId}/documentos`, dados);
    },
    onSuccess: () => {
      toast.success(`${label} enviado com sucesso.`);
      setArquivo(null);
      queryClient.invalidateQueries({ queryKey });
    },
    onError: (err: any) => toast.error(mensagemErroApi(err, `Erro ao enviar ${label.toLowerCase()}.`)),
  });

  const removerMutation = useMutation({
    mutationFn: (documentoId: string) => api.delete(`/usuarios/documentos/${documentoId}`),
    onSuccess: () => {
      toast.success("Anexo removido.");
      queryClient.invalidateQueries({ queryKey });
    },
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao remover anexo.")),
  });

  async function baixar(doc: UsuarioDocumento) {
    setBaixando(doc.id);
    try {
      const resp = await api.get(`/usuarios/documentos/${doc.id}/arquivo`, { responseType: "blob" });
      const url = window.URL.createObjectURL(resp.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = doc.nome_arquivo;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error("Não foi possível baixar o arquivo.");
    } finally {
      setBaixando(null);
    }
  }

  return (
    <div className="space-y-4">
      {isLoading ? (
        <Spinner label="Carregando anexos…" />
      ) : documentosDoTipo.length === 0 ? (
        <EmptyState message={`Nenhum anexo de ${label.toLowerCase()} enviado ainda.`} />
      ) : (
        <ul className="divide-y divide-gray-100">
          {documentosDoTipo.map((doc) => (
            <li key={doc.id} className="py-3 flex items-center justify-between gap-3">
              <span className="text-sm text-gray-700 truncate">{doc.nome_arquivo}</span>
              <div className="flex items-center gap-2 shrink-0">
                <Button variant="secondary" type="button" onClick={() => baixar(doc)} disabled={baixando === doc.id}>
                  {baixando === doc.id ? "Baixando…" : "Baixar"}
                </Button>
                <button
                  type="button"
                  onClick={() => {
                    if (window.confirm("Remover este anexo?")) removerMutation.mutate(doc.id);
                  }}
                  className="text-gray-400 hover:text-red-600 transition-colors text-sm px-2"
                >
                  Remover
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="flex flex-col sm:flex-row sm:items-end gap-3 pt-2 border-t border-gray-100">
        <div className="flex-1">
          <FileInput label={`Enviar ${label.toLowerCase()}`} accept="image/*,application/pdf" file={arquivo} onChange={setArquivo} />
        </div>
        <Button type="button" onClick={() => enviarMutation.mutate()} disabled={!arquivo || enviarMutation.isPending}>
          {enviarMutation.isPending ? "Enviando…" : "Enviar"}
        </Button>
      </div>
    </div>
  );
}
