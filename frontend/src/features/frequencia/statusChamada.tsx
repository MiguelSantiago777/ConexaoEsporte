import type { ComponentType } from "react";
import type { FichaChamada, StatusDia } from "@/types";
import { CheckIcon, CloseIcon, ExclamationIcon } from "@/components/ui/icons";

function badge(bg: string, Icon: ComponentType<{ className?: string }>) {
  return (
    <span className={`inline-flex items-center justify-center w-5 h-5 rounded-full ${bg} text-white shrink-0`}>
      <Icon className="w-3 h-3" />
    </span>
  );
}

/** Badge circular preenchido por status — mesma linguagem visual da
 * referência do cliente (círculo colorido com o glifo branco dentro). */
export const STATUS_ESTILO: Record<StatusDia, { icon: JSX.Element; className: string; titulo: string }> = {
  PRESENTE: { icon: badge("bg-emerald-500", CheckIcon), className: "text-emerald-600", titulo: "Presente" },
  FALTA: { icon: badge("bg-red-500", CloseIcon), className: "text-red-600", titulo: "Falta" },
  FALTA_JUSTIFICADA: { icon: badge("bg-blue-500", CheckIcon), className: "text-blue-600", titulo: "Falta justificada" },
  IMPEDITIVO: { icon: badge("bg-amber-500", ExclamationIcon), className: "text-amber-600", titulo: "Impeditivo de aula" },
  SEM_MARCACAO: { icon: badge("bg-gray-300", ExclamationIcon), className: "text-gray-400", titulo: "Sem marcação" },
};

export function diaCurto(iso: string) {
  return iso.slice(8, 10);
}

export function dataBR(iso: string) {
  return `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}`;
}

/** Totais e percentuais mostrados no painel "Detalhes da ficha de
 * presença" — Total de Presenças e Total de Faltas/Não Marcadas, cada um
 * com o percentual sobre os dias efetivamente letivos (exclui os dias com
 * impeditivo de aula, que não contam nem como presença nem como falta). */
export function contadoresFicha(ficha: FichaChamada) {
  const { presenca, falta, falta_justificada, sem_marcacao } = ficha.resumo;
  const totalAvaliado = presenca + falta + falta_justificada + sem_marcacao;
  const totalFaltasNaoMarcadas = falta + sem_marcacao;
  const pct = (n: number) => (totalAvaliado > 0 ? Math.round((100 * n) / totalAvaliado) : 0);
  return {
    totalPresencas: presenca,
    pctPresencas: pct(presenca),
    totalFaltasNaoMarcadas,
    pctFaltasNaoMarcadas: pct(totalFaltasNaoMarcadas),
  };
}

/** Monta as abas da planilha Excel da Ficha de Chamada — uma linha por
 * beneficiário com uma coluna por data (texto do status), impeditivos do
 * mês numa aba própria e o resumo geral de marcações na última aba. */
export function fichaChamadaParaAbas(ficha: FichaChamada) {
  const linhas = ficha.linhas.map((linha, i) => {
    const base: Record<string, string | number> = {
      "Nº": i + 1,
      Beneficiário: linha.nome,
      Idade: linha.idade ?? "—",
      "Freq. (%)": linha.frequencia_pct,
    };
    ficha.datas.forEach((d) => {
      base[dataBR(d)] = STATUS_ESTILO[linha.status_por_data[d]].titulo;
    });
    return base;
  });

  const abas = [{ nome: "Chamada", linhas }];

  if (ficha.impeditivos.length > 0) {
    abas.push({
      nome: "Impeditivos",
      linhas: ficha.impeditivos.map((imp) => ({ Data: dataBR(imp.data), Justificativa: imp.justificativa })),
    });
  }

  if (ficha.justificativas.length > 0) {
    abas.push({
      nome: "Justificativas",
      linhas: ficha.justificativas.map((j) => ({
        Beneficiário: j.beneficiario_nome, Data: dataBR(j.data), Justificativa: j.justificativa,
      })),
    });
  }

  abas.push({
    nome: "Resumo",
    linhas: [
      { Marcação: "Presença", Quantidade: ficha.resumo.presenca },
      { Marcação: "Falta", Quantidade: ficha.resumo.falta },
      { Marcação: "Falta justificada", Quantidade: ficha.resumo.falta_justificada },
      { Marcação: "Impeditivo", Quantidade: ficha.resumo.impeditivo },
      { Marcação: "Sem marcação", Quantidade: ficha.resumo.sem_marcacao },
    ],
  });

  return abas;
}
