import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mensagemErroApi } from "@/lib/erros";
import type { InscricaoListaEspera, Modalidade, Polo, Turma } from "@/types";
import { aceitarInscricao, listarInscricoesPendentes } from "./listaEsperaService";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { PageHeader } from "@/components/ui/PageHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { Spinner } from "@/components/ui/Spinner";
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
          <p>CPF: {inscricao.documento} · WhatsApp: {inscricao.telefone_whatsapp}</p>
          <p>Email: {inscricao.email}</p>
          {inscricao.nome_responsavel && (
            <p>Responsável: {inscricao.nome_responsavel} — CPF: {inscricao.documento_responsavel ?? "—"}</p>
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
  const [inscricaoSelecionada, setInscricaoSelecionada] = useState<InscricaoListaEspera | null>(null);

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
                  <th className="py-2 pr-4 font-medium">Contato</th>
                  <th className="py-2 pr-4 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {inscricoes.map((i) => (
                  <tr key={i.id} className="border-b border-gray-50 last:border-0">
                    <td className="py-3 pr-4">
                      <div className="font-medium text-brand-dark">{i.nome_completo}</div>
                      <div className="text-xs text-gray-400">{calcularIdade(i.data_nascimento)} anos</div>
                    </td>
                    <td className="py-3 pr-4">{nomeModalidade(i.modalidade_id)}</td>
                    <td className="py-3 pr-4">{nomePolo(i.polo_id)}</td>
                    <td className="py-3 pr-4">
                      <div>{i.telefone_whatsapp}</div>
                      <div className="text-xs text-gray-400">{i.email}</div>
                    </td>
                    <td className="py-3 pr-4 text-right">
                      <Button onClick={() => setInscricaoSelecionada(i)}>Aceitar</Button>
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
