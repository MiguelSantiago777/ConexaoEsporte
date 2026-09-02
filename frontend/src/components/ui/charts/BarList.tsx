import { useEffect, useState } from "react";

interface Item {
  label: string;
  value: number;
}

export function BarList({ data, color = "#00417d" }: { data: Item[]; color?: string }) {
  const maximo = Math.max(1, ...data.map((d) => d.value));

  // Nasce com toda barra em 0% e cresce até a largura final via transição
  // CSS, uma tecla depois da outra — só depois do primeiro paint, senão a
  // transição não dispara (já nasceria no estado final).
  const [revelado, setRevelado] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setRevelado(true));
    return () => cancelAnimationFrame(id);
  }, []);

  if (data.length === 0) {
    return <p className="text-sm text-gray-400">Sem dados ainda.</p>;
  }

  return (
    <ul className="space-y-4">
      {data.map((d, i) => (
        <li key={d.label}>
          <div className="flex items-center justify-between gap-3 text-sm mb-1.5">
            <span className="text-gray-600 truncate">{d.label}</span>
            <span className="font-mono tabular-nums text-xs font-semibold text-brand-dark bg-brand-light rounded-full px-2 py-0.5 shrink-0">
              {d.value}
            </span>
          </div>
          <div className="h-2.5 rounded-full bg-gray-100 overflow-hidden mr-1" title={`${d.label}: ${d.value}`}>
            <div
              className="h-full rounded-full"
              style={{
                width: revelado ? `${(d.value / maximo) * 100}%` : "0%",
                backgroundColor: color,
                transition: `width 1.6s cubic-bezier(0.16,1,0.3,1) ${i * 130}ms`,
              }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}
