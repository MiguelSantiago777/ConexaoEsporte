import { SpinnerIcon } from "@/components/ui/icons";

export function Spinner({ label = "Carregando…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-gray-400">
      <SpinnerIcon className="w-6 h-6 text-brand" />
      <p className="text-sm">{label}</p>
    </div>
  );
}
