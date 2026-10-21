import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { InscricaoListaEspera, Modalidade, Polo, Turma } from "@/types";
import {
  aceitarInscricao, baixarDocumentoIdentidade, excluirInscricao, listarInscricoesPendentes,
} from "./listaEsperaService";
import { turnoLabel } from "./constants";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { PageHeader } from "@/components/ui/PageHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { Spinner } from "@/components/ui/Spinner";
import { PaperclipIcon, TrashIcon } from "@/components/ui/icons";
import { useToast } from "@/components/ui/toast/ToastContext";
import { staggerStyle } from "@/lib/animation";

const DIAS_SEMANA_LABEL: Record<string, string> = {
  SEG: "seg", TER: "ter", QUA: "qua", QUI: "qui", SEX: "sex", SAB: "sáb", DOM: "dom",
};

function calcularIdade(dataNascimento: string): number {
  const nascimento = new Date(dataNascimento + "T00:00:00");
  const hoje = new Date();
  let anos = hoje.getFullYear() - nascimento.getFullYear();
  const aindaNaoFezAniversario =
    hoje.getMonth() < nascimento.getMonth() ||
    (hoje.getMonth() === nascimento.getMonth() && hoje.getDate() < nascimento.getDate());
  if (aindaNaoFezAniversario) anos -= 1;
  return anos;
}

/** "2015-03-09" → "09/03/2015" sem passar por Date (evita o deslocamento
 * de fuso que jogaria a data um dia pra trás). */
function formatarData(dataISO: string): string {
  const [ano, mes, dia] = dataISO.split("-");
  return `${dia}/${mes}/${ano}`;
}

/** Abre o documento de identidade anexado numa nova aba — imagem/PDF o
 * navegador exibe direto. A aba é aberta antes do download pra não cair no
 * bloqueador de pop-up. */
async function abrirDocumentoIdentidade(inscricao: InscricaoListaEspera, onErro: (msg: string) => void) {
  const aba = window.open("", "_blank");
  try {
    const blob = await baixarDocumentoIdentidade(inscricao.id);
    const url = window.URL.createObjectURL(blob);
    if (aba) aba.location.href = url;
    else window.location.href = url;
    setTimeout(() => window.URL.revokeObjectURL(url), 60_000);
  } catch (err) {
    aba?.close();
    onErro(mensagemErroApi(err, "Não foi possível abrir o documento."));
  }
}

function AceitarModal({
  inscricao, onClose,
}: {
  inscricao: InscricaoListaEspera;
  onClose: () => void;
}) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [turmaId, setTurmaId] = useState("");

  // GET /turmas ignora o parâmetro `polo_id` pra usuários MASTER (sempre devolve
  // turmas de todos os polos pra esse perfil) — por isso o filtro por polo E
  // modalidade precisa acontecer aqui no cliente, não só no query param.
  const { data: turmas = [], isLoading: carregandoTurmas } = useQuery({
    queryKey: ["turmas-do-polo", inscricao.polo_id],
    queryFn: () => api.get<Turma[]>("/turmas", { params: { polo_id: inscricao.polo_id } }).then((r) => r.data),
  });
  const turmasDaModalidade = turmas.filter(
    (t) => t.polo_id === inscricao.polo_id && t.modalidade_id === inscricao.modalidade_id && t.ativo,
  );

  const mutation = useMutation({
    mutationFn: () => aceitarInscricao(inscricao.id, turmaId),
    onSuccess: () => {
      toast.success(`${inscricao.nome_completo} foi aceito(a) e matriculado(a) com sucesso.`);
      queryClient.invalidateQueries({ queryKey: ["lista-espera-pendentes"] });
      onClose();
    },
    onError: (err) => toast.error(mensagemErroApi(err, "Erro ao aceitar a inscrição.")),
  });

  return (
    <Modal open onClose={onClose} title="Aceitar inscrição">
      <div className="space-y-4">
        <div className="text-sm text-gray-600 space-y-1">
          <p><strong className="text-brand-dark">{inscricao.nome_completo}</strong> — {calcularIdade(inscricao.data_nascimento)} anos</p>
          <p>Nascimento: {formatarData(inscricao.data_nascimento)} · Turno: {turnoLabel(inscricao.turno)}</p>
          <p>CPF: {inscricao.documento} · WhatsApp: {inscricao.telefone_whatsapp}</p>
          <p>Email: {inscricao.email}</p>
          {inscricao.nome_responsavel && (
            <p>Responsável: {inscricao.nome_responsavel} — CPF: {inscricao.documento_responsavel ?? "—"}</p>
          )}
          {inscricao.documento_identidade_nome_arquivo && (
            <button
              type="button" onClick={() => abrirDocumentoIdentidade(inscricao, toast.error)}
              className="inline-flex items-center gap-1 text-brand hover:underline"
            >
              <PaperclipIcon className="w-4 h-4" /> Ver documento de identidade
            </button>
          )}
        </div>

        {carregandoTurmas ? (
          <div className="flex justify-center py-6"><Spinner /></div>
        ) : turmasDaModalidade.length === 0 ? (
          <EmptyState message="Não há turmas ativas dessa modalidade nesse polo. Cadastre uma turma antes de aceitar." />
        ) : (
          <Select label="Turma" value={turmaId} onChange={(e) => setTurmaId(e.target.value)} required>
            <option value="">Selecione a turma</option>
            {turmasDaModalidade.map((t) => (
              <option key={t.id} value={t.id}>
                {t.dias_semana.map((d) => DIAS_SEMANA_LABEL[d] ?? d).join(", ")} · {t.horario_inicio}–{t.horario_fim}
              </option>
            ))}
          </Select>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button onClick={() => mutation.mutate()} disabled={!turmaId || mutation.isPending}>
            {mutation.isPending ? "Aceitando…" : "Aceitar e matricular"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

export function ListaEsperaPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [inscricaoSelecionada, setInscricaoSelecionada] = useState<InscricaoListaEspera | null>(null);

  const excluirMutation = useMutation({
    mutationFn: (i: InscricaoListaEspera) => excluirInscricao(i.id),
    onSuccess: () => {
      toast.success("Inscrição excluída.");
      queryClient.invalidateQueries({ queryKey: ["lista-espera-pendentes"] });
    },
    onError: (err) => toast.error(mensagemErroApi(err, "Erro ao excluir a inscrição.")),
  });

  function excluir(i: InscricaoListaEspera) {
    if (!window.confirm(`Excluir a inscrição de ${i.nome_completo} definitivamente? Essa ação não pode ser desfeita.`)) {
      return;
    }
    excluirMutation.mutate(i);
  }

  const { data: inscricoes = [], isLoading } = useQuery({
    queryKey: ["lista-espera-pendentes"],
    queryFn: () => listarInscricoesPendentes(),
  });
  const { data: polos = [] } = useQuery({
    queryKey: ["polos"], queryFn: () => api.get<Polo[]>("/polos").then((r) => r.data),
  });
  const { data: modalidades = [] } = useQuery({
    queryKey: ["modalidades"], queryFn: () => api.get<Modalidade[]>("/modalidades").then((r) => r.data),
  });

  const nomePolo = (id: string) => polos.find((p) => p.id === id)?.nome ?? "—";
  const nomeModalidade = (id: string) => modalidades.find((m) => m.id === id)?.nome ?? "—";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Lista de Espera"
        subtitle="Inscrições recebidas pelo formulário público, aguardando aceite."
      />
      <Card className="animate-fade-in-up" style={staggerStyle(0)}>
        {isLoading ? (
          <div className="flex justify-center py-12"><Spinner /></div>
        ) : inscricoes.length === 0 ? (
          <EmptyState message="Nenhuma inscrição pendente no momento." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-100">
                  <th className="py-2 pr-4 font-medium">Participante</th>
                  <th className="py-2 pr-4 font-medium">Modalidade</th>
                  <th className="py-2 pr-4 font-medium">Polo</th>
                  <th className="py-2 pr-4 font-medium">Turno</th>
                  <th className="py-2 pr-4 font-medium">Contato</th>
                  <th className="py-2 pr-4 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {inscricoes.map((i) => (
                  <tr key={i.id} className="border-b border-gray-50 last:border-0">
                    <td className="py-3 pr-4">
                      <div className="font-medium text-brand-dark">{i.nome_completo}</div>
                      <div className="text-xs text-gray-400">
                        {formatarData(i.data_nascimento)} · {calcularIdade(i.data_nascimento)} anos
                      </div>
                      {i.documento_identidade_nome_arquivo && (
                        <button
                          type="button" onClick={() => abrirDocumentoIdentidade(i, toast.error)}
                          className="inline-flex items-center gap-1 text-xs text-brand hover:underline mt-0.5"
                        >
                          <PaperclipIcon className="w-3.5 h-3.5" /> Documento de identidade
                        </button>
                      )}
                    </td>
                    <td className="py-3 pr-4">{nomeModalidade(i.modalidade_id)}</td>
                    <td className="py-3 pr-4">{nomePolo(i.polo_id)}</td>
                    <td className="py-3 pr-4">{turnoLabel(i.turno)}</td>
                    <td className="py-3 pr-4">
                      <div>{i.telefone_whatsapp}</div>
                      <div className="text-xs text-gray-400">{i.email}</div>
                    </td>
                    <td className="py-3 pr-4 text-right">
                      <div className="flex items-center justify-end gap-3">
                        <Button onClick={() => setInscricaoSelecionada(i)}>Aceitar</Button>
                        <button
                          type="button"
                          title="Excluir"
                          onClick={() => excluir(i)}
                          disabled={excluirMutation.isPending}
                          className="text-slate-400 hover:text-danger transition-colors -m-1.5 p-1.5 disabled:opacity-50"
                        >
                          <TrashIcon />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {inscricaoSelecionada && (
        <AceitarModal inscricao={inscricaoSelecionada} onClose={() => setInscricaoSelecionada(null)} />
      )}
    </div>
  );
}
