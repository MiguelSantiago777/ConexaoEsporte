import type { StatusDia } from "@/types";
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
