import type { FichaChamada, StatusDia } from "@/types";
import { AlertCircleIcon, CalendarOffIcon, CheckCircleIcon, CloseIcon } from "@/components/ui/icons";

export const STATUS_ESTILO: Record<StatusDia, { icon: JSX.Element; className: string; titulo: string }> = {
  PRESENTE: { icon: <CheckCircleIcon className="w-5 h-5" />, className: "text-accent-dark", titulo: "Presente" },
  FALTA: { icon: <CloseIcon className="w-5 h-5" />, className: "text-red-500", titulo: "Falta" },
  FALTA_JUSTIFICADA: {
    icon: <AlertCircleIcon className="w-5 h-5" />,
    className: "text-blue-500",
    titulo: "Falta justificada",
  },
  IMPEDITIVO: {
    icon: <CalendarOffIcon className="w-5 h-5" />,
    className: "text-amber-500",
    titulo: "Impeditivo de aula",
  },
  SEM_MARCACAO: { icon: <span className="text-gray-300">—</span>, className: "", titulo: "Sem marcação" },
};

export function diaCurto(iso: string) {
  return iso.slice(8, 10);
}

export function dataBR(iso: string) {
  return `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}`;
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
