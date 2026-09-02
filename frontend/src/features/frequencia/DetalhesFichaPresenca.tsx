import type { FichaChamada } from "@/types";
import { contadoresFicha } from "./statusChamada";

const MESES = [
  "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

function formatarAtualizadoEm(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString("pt-BR", { day: "2-digit", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function Linha({ label, valor }: { label: string; valor: string }) {
  return (
    <div>
      <span className="font-semibold text-gray-700">{label}: </span>
      <span className="text-gray-600">{valor}</span>
    </div>
  );
}

/** Painel "Detalhes da ficha de presença" — mesma lista de campos, na
 * mesma ordem, da referência visual do cliente. Usado tanto na tela de
 * lançamento de chamada quanto no documento impresso/exportado. */
export function DetalhesFichaPresenca({ ficha }: { ficha: FichaChamada }) {
  const { totalPresencas, pctPresencas, totalFaltasNaoMarcadas, pctFaltasNaoMarcadas } = contadoresFicha(ficha);

  return (
    <div className="text-sm space-y-1.5">
      <Linha label="Período" valor={`${MESES[ficha.mes]}/${ficha.ano}`} />
      <Linha label="Turma" valor={`${ficha.modalidade_nome} — ${ficha.horario_inicio}–${ficha.horario_fim}`} />
      <Linha label="Dias e Horários" valor={`${ficha.dias_semana.join(", ")} — ${ficha.horario_inicio}–${ficha.horario_fim}`} />
      {ficha.atualizado_em && <Linha label="Atualizada em" valor={formatarAtualizadoEm(ficha.atualizado_em)} />}
      {ficha.atualizado_por_nome && <Linha label="Atualizada por" valor={ficha.atualizado_por_nome} />}
      <Linha label="Polo" valor={ficha.polo_nome} />
      {ficha.faixa_etaria_min !== null && ficha.faixa_etaria_max !== null && (
        <Linha label="Faixa etária" valor={`De ${ficha.faixa_etaria_min} a ${ficha.faixa_etaria_max} anos`} />
      )}
      <Linha label="Impeditivos de aula" valor={String(ficha.impeditivos.length)} />
      <Linha label="Faltas justificadas" valor={String(ficha.resumo.falta_justificada)} />
      <div className="pt-1.5 mt-1.5 border-t border-gray-100 space-y-1.5">
        <Linha label="Total de Presenças" valor={`${totalPresencas} — (${pctPresencas}%)`} />
        <Linha label="Total de Faltas/Não Marcadas" valor={`${totalFaltasNaoMarcadas} — (${pctFaltasNaoMarcadas}%)`} />
      </div>
    </div>
  );
}
