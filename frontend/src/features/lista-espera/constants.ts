export const CANAIS_COMO_CONHECEU = [
  "Instagram", "Facebook", "WhatsApp", "Indicação de amigo ou família", "Panfleto ou evento", "Outro",
];

export const TURNOS = [
  { valor: "MANHA", label: "Manhã" },
  { valor: "TARDE", label: "Tarde" },
] as const;

export function turnoLabel(turno: string | null | undefined): string {
  return TURNOS.find((t) => t.valor === turno)?.label ?? "—";
}
