import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { AnexoGeral, DocumentoConsolidado, Polo, TipoDocumentoConsolidado } from "@/types";
import { useAuth } from "@/features/auth/AuthContext";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { FileInput } from "@/components/ui/FileInput";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Badge } from "@/components/ui/Badge";
import { Tabs } from "@/components/ui/Tabs";
import { PaperclipIcon, CameraIcon, DocumentTextIcon } from "@/components/ui/icons";
import { useToast } from "@/components/ui/toast/ToastContext";

export function AnexosGeraisPage() {
  const { usuario } = useAuth();
  return usuario?.perfil === "MASTER" ? <VisaoConsolidadaDocumentos /> : <AnexosGeraisDoPolo />;
}

function formatarData(dataIso: string) {
  const [ano, mes, dia] = dataIso.split("-");
  return `${dia}/${mes}/${ano}`;
}

const ABAS_TIPO: { id: TipoDocumentoConsolidado | "TODOS"; label: string }[] = [
  { id: "TODOS", label: "Todos" },
  { id: "ANEXO_GERAL", label: "Anexos dos polos" },
  { id: "EVIDENCIA_CHAMADA", label: "Fotos de chamada" },
  { id: "OBSERVACAO_AULA", label: "Observações de aula" },
];

const INFO_TIPO: Record<TipoDocumentoConsolidado, { icone: typeof PaperclipIcon; badge: "brand" | "accent" | "gray" }> = {
  ANEXO_GERAL: { icone: PaperclipIcon, badge: "brand" },
  EVIDENCIA_CHAMADA: { icone: CameraIcon, badge: "accent" },
  OBSERVACAO_AULA: { icone: DocumentTextIcon, badge: "gray" },
};

function urlArquivo(doc: DocumentoConsolidado): string | null {
  if (doc.tipo === "ANEXO_GERAL") return `/anexos-gerais/${doc.id}/arquivo`;
  if (doc.tipo === "EVIDENCIA_CHAMADA") return `/frequencias/evidencias/${doc.id}/arquivo`;
  return null;
}

/** MASTER: visão somente leitura de tudo que foi anexado — pelos polos
 * (Anexos Gerais), ou pelos professores ao lançar a chamada (fotos de
 * evidência e observações do relatório de aula). Não é possível anexar
 * nada por aqui. */
function VisaoConsolidadaDocumentos() {
  const toast = useToast();

  const { data: polos = [] } = useQuery({
    queryKey: ["polos"],
    queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
  });

  const [poloFiltro, setPoloFiltro] = useState("");
  const [tipoFiltro, setTipoFiltro] = useState<TipoDocumentoConsolidado | "TODOS">("TODOS");

  const { data: documentos = [], isLoading } = useQuery({
    queryKey: ["anexos-gerais-consolidado", poloFiltro],
    queryFn: () =>
      api
        .get<DocumentoConsolidado[]>("/anexos-gerais/consolidado", { params: { polo_id: poloFiltro || undefined } })
        .then((r) => r.data),
  });

  const documentosFiltrados = useMemo(
    () => (tipoFiltro === "TODOS" ? documentos : documentos.filter((d) => d.tipo === tipoFiltro)),
    [documentos, tipoFiltro],
  );

  const [abrindo, setAbrindo] = useState<string | null>(null);
  async function abrir(doc: DocumentoConsolidado) {
    const url = urlArquivo(doc);
    if (!url || !doc.nome_arquivo) return;
    setAbrindo(doc.id);
    try {
      const resp = await api.get(url, { responseType: "blob" });
      const objectUrl = window.URL.createObjectURL(resp.data);
      if (doc.content_type?.startsWith("image/") || doc.content_type === "application/pdf") {
        window.open(objectUrl, "_blank");
      } else {
        const a = document.createElement("a");
        a.href = objectUrl;
        a.download = doc.nome_arquivo;
        document.body.appendChild(a);
        a.click();
        a.remove();
      }
      window.URL.revokeObjectURL(objectUrl);
    } catch {
      toast.error("Não foi possível abrir o arquivo.");
    } finally {
      setAbrindo(null);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Anexos Gerais"
        subtitle="Tudo o que foi anexado pelos polos, gestores de polo e professores — inclusive as fotos e observações registradas na hora da chamada. Consulta somente leitura."
      />
      <Card className="animate-fade-in-up">
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select label="Polo" value={poloFiltro} onChange={(e) => setPoloFiltro(e.target.value)}>
              <option value="">Todos os polos</option>
              {polos.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nome}
                </option>
              ))}
            </Select>
          </div>

          <Tabs abas={ABAS_TIPO} ativa={tipoFiltro} onChange={(id) => setTipoFiltro(id as TipoDocumentoConsolidado | "TODOS")}>
            {isLoading ? (
              <Spinner label="Carregando documentos…" />
            ) : documentosFiltrados.length === 0 ? (
              <EmptyState message="Nenhum documento encontrado." />
            ) : (
              <ul className="divide-y divide-gray-100">
                {documentosFiltrados.map((doc) => {
                  const info = INFO_TIPO[doc.tipo];
                  const Icone = info.icone;
                  return (
                    <li key={`${doc.tipo}-${doc.id}`} className="py-3 flex items-start justify-between gap-3">
                      <div className="min-w-0 flex items-start gap-3">
                        <Icone className="w-5 h-5 text-gray-400 shrink-0 mt-0.5" />
                        <div className="min-w-0 space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-sm font-medium text-gray-800">{doc.titulo}</span>
                            <Badge variant={info.badge}>{ABAS_TIPO.find((a) => a.id === doc.tipo)?.label}</Badge>
                          </div>
                          <div className="text-xs text-gray-400">
                            {doc.polo_nome}
                            {doc.turma_nome ? ` — ${doc.turma_nome}` : ""}
                            {doc.autor_nome ? ` · ${doc.autor_nome}` : ""} · {formatarData(doc.data_evento)}
                          </div>
                          {doc.descricao && <p className="text-sm text-gray-600 whitespace-pre-wrap">{doc.descricao}</p>}
                        </div>
                      </div>
                      {doc.possui_arquivo && (
                        <Button variant="secondary" type="button" onClick={() => abrir(doc)} disabled={abrindo === doc.id} className="shrink-0">
                          {abrindo === doc.id ? "Abrindo…" : "Ver arquivo"}
                        </Button>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </Tabs>
        </div>
      </Card>
    </div>
  );
}

/** GESTOR_POLO: mantém o repositório livre de documentos do próprio polo,
 * podendo enviar, baixar e remover anexos. */
function AnexosGeraisDoPolo() {
  const { usuario } = useAuth();
  const toast = useToast();
  const queryClient = useQueryClient();
  const poloId = usuario?.polo_id ?? "";

  const [titulo, setTitulo] = useState("");
  const [arquivo, setArquivo] = useState<File | null>(null);

  const queryKey = ["anexos-gerais", poloId];
  const { data: anexos = [], isLoading } = useQuery({
    queryKey,
    queryFn: () => api.get<AnexoGeral[]>("/anexos-gerais", { params: { polo_id: poloId } }).then((r) => r.data),
    enabled: !!poloId,
  });

  const enviarMutation = useMutation({
    mutationFn: () => {
      const dados = new FormData();
      dados.append("polo_id", poloId);
      dados.append("titulo", titulo);
      dados.append("arquivo", arquivo as File);
      return api.post("/anexos-gerais", dados);
    },
    onSuccess: () => {
      toast.success("Anexo enviado com sucesso.");
      setTitulo("");
      setArquivo(null);
      queryClient.invalidateQueries({ queryKey });
    },
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao enviar anexo.")),
  });

  const removerMutation = useMutation({
    mutationFn: (anexoId: string) => api.delete(`/anexos-gerais/${anexoId}`),
    onSuccess: () => {
      toast.success("Anexo removido.");
      queryClient.invalidateQueries({ queryKey });
    },
    onError: (err: any) => toast.error(mensagemErroApi(err, "Erro ao remover anexo.")),
  });

  const [baixando, setBaixando] = useState<string | null>(null);
  async function baixar(anexo: AnexoGeral) {
    setBaixando(anexo.id);
    try {
      const resp = await api.get(`/anexos-gerais/${anexo.id}/arquivo`, { responseType: "blob" });
      const url = window.URL.createObjectURL(resp.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = anexo.nome_arquivo;
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
    <div className="space-y-6">
      <PageHeader
        title="Anexos Gerais"
        subtitle="Repositório livre de documentos do seu polo, para qualquer arquivo útil que não pertença a um professor ou beneficiário específico."
      />
      <Card className="animate-fade-in-up">
        <div className="space-y-6">
          {isLoading ? (
            <Spinner label="Carregando anexos…" />
          ) : anexos.length === 0 ? (
            <EmptyState message="Nenhum anexo geral enviado ainda para este polo." />
          ) : (
            <ul className="divide-y divide-gray-100">
              {anexos.map((a) => (
                <li key={a.id} className="py-3 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-gray-800 truncate">{a.titulo}</div>
                    <div className="text-xs text-gray-400 truncate">{a.nome_arquivo}</div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Button variant="secondary" type="button" onClick={() => baixar(a)} disabled={baixando === a.id}>
                      {baixando === a.id ? "Baixando…" : "Baixar"}
                    </Button>
                    <button
                      type="button"
                      onClick={() => {
                        if (window.confirm("Remover este anexo?")) removerMutation.mutate(a.id);
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

          <div className="border-t border-gray-100 pt-4 space-y-4">
            <h3 className="text-sm font-semibold text-brand-dark">Enviar novo anexo</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input label="Título" placeholder="ex.: Apólice de seguro" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
              <FileInput label="Arquivo" accept="image/*,application/pdf" file={arquivo} onChange={setArquivo} />
            </div>
            <Button
              type="button"
              onClick={() => enviarMutation.mutate()}
              disabled={!arquivo || !titulo.trim() || enviarMutation.isPending}
            >
              {enviarMutation.isPending ? "Enviando…" : "Enviar anexo"}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
