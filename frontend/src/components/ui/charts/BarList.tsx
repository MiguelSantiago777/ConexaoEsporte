interface Item {
  label: string;
  value: number;
}

export function BarList({ data, color = "#00417d" }: { data: Item[]; color?: string }) {
  const maximo = Math.max(1, ...data.map((d) => d.value));

  if (data.length === 0) {
    return <p className="text-sm text-gray-400">Sem dados ainda.</p>;
  }

  return (
    <ul className="space-y-3">
      {data.map((d) => (
        <li key={d.label}>
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-gray-600 truncate pr-2">{d.label}</span>
            <span className="font-semibold text-gray-800 shrink-0">{d.value}</span>
          </div>
          <div className="h-2.5 rounded-full bg-gray-100 overflow-hidden" title={`${d.label}: ${d.value}`}>
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${(d.value / maximo) * 100}%`, backgroundColor: color }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}
