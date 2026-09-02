import { useEffect, useState } from "react";

interface Fatia {
  label: string;
  value: number;
  color: string;
}

export function DonutChart({ data, size = 160, thickness = 24 }: { data: Fatia[]; size?: number; thickness?: number }) {
  const total = data.reduce((acc, d) => acc + d.value, 0);
  const raio = (size - thickness) / 2;
  const circunferencia = 2 * Math.PI * raio;

  // Começa com as fatias recolhidas (todas em stroke-dashoffset = 0, ou seja
  // "escondidas" na posição do próprio início do círculo) e revela cada uma
  // até seu offset final via transição CSS — só depois do primeiro paint,
  // pra transição realmente disparar em vez de já nascer no estado final.
  const [revelado, setRevelado] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setRevelado(true));
    return () => cancelAnimationFrame(id);
  }, []);

  let offsetAcumulado = 0;

  return (
    <div className="flex items-center gap-6 flex-wrap">
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={raio} fill="none" stroke="#e1e0d9" strokeWidth={thickness} />
          {total > 0 &&
            data
              .filter((d) => d.value > 0)
              .map((d, i) => {
                const fracao = d.value / total;
                const comprimento = fracao * circunferencia;
                const dasharray = `${comprimento} ${circunferencia - comprimento}`;
                const dashoffsetFinal = -offsetAcumulado;
                const dashoffsetEscondido = -(offsetAcumulado + comprimento);
                offsetAcumulado += comprimento;
                return (
                  <circle
                    key={d.label}
                    cx={size / 2}
                    cy={size / 2}
                    r={raio}
                    fill="none"
                    stroke={d.color}
                    strokeWidth={thickness}
                    strokeDasharray={dasharray}
                    strokeDashoffset={revelado ? dashoffsetFinal : dashoffsetEscondido}
                    style={{ transition: `stroke-dashoffset 1.6s cubic-bezier(0.16,1,0.3,1) ${i * 160}ms` }}
                  >
                    <title>{`${d.label}: ${d.value} (${Math.round(fracao * 100)}%)`}</title>
                  </circle>
                );
              })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold text-brand-dark">{total}</span>
          <span className="text-[10px] text-gray-400 uppercase tracking-wide">total</span>
        </div>
      </div>
      <ul className="space-y-1.5 text-sm min-w-[140px]">
        {data.map((d) => (
          <li key={d.label} className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: d.color }} />
            <span className="text-gray-600 truncate flex-1">{d.label}</span>
            <span className="font-medium text-gray-800">{d.value}</span>
          </li>
        ))}
        {total === 0 && <li className="text-gray-400">Sem dados ainda.</li>}
      </ul>
    </div>
  );
}
