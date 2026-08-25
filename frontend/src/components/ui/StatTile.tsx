import { staggerStyle } from "@/lib/animation";

interface Props {
  label: string;
  value: string | number;
  sublabel?: string;
  /** Posição no grid — anima em cascata (cada tile atrasa um pouco mais). */
  staggerIndex?: number;
}

export function StatTile({ label, value, sublabel, staggerIndex }: Props) {
  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-gray-200/80 p-5 transition-shadow duration-200 hover:shadow-md ${
        staggerIndex !== undefined ? "animate-fade-in-up" : ""
      }`}
      style={staggerIndex !== undefined ? staggerStyle(staggerIndex) : undefined}
    >
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</div>
      <div className="text-2xl font-bold text-brand-dark mt-1">{value}</div>
      {sublabel && <div className="text-xs text-gray-400 mt-0.5">{sublabel}</div>}
    </div>
  );
}
