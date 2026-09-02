import { CourtMark } from "./CourtMark";

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="flex items-start gap-3.5">
      <CourtMark className="w-8 h-8 mt-1 shrink-0" />
      <div>
        <h1 className="text-2xl font-bold text-brand-dark">{title}</h1>
        {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
}
