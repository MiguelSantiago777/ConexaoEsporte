import { ReactNode } from "react";

export function Card({ children, title }: { children: ReactNode; title?: string }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {title && <h2 className="text-lg font-semibold mb-4 text-gray-800">{title}</h2>}
      {children}
    </div>
  );
}
