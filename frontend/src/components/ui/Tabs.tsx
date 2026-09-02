import { ReactNode } from "react";

interface Aba {
  id: string;
  label: string;
}

export function Tabs({
  abas,
  ativa,
  onChange,
  children,
}: {
  abas: Aba[];
  ativa: string;
  onChange: (id: string) => void;
  children: ReactNode;
}) {
  return (
    <div>
      <div className="flex gap-1 mb-4 overflow-x-auto">
        {abas.map((aba) => (
          <button
            key={aba.id}
            type="button"
            onClick={() => onChange(aba.id)}
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
              ativa === aba.id
                ? "border-brand text-brand-dark"
                : "border-transparent text-gray-500 hover:text-brand-dark"
            }`}
          >
            {aba.label}
          </button>
        ))}
      </div>
      {children}
    </div>
  );
}
