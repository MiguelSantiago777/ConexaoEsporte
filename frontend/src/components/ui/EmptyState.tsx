import { InboxIcon } from "@/components/ui/icons";

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-center">
      <InboxIcon className="w-10 h-10 text-gray-300" />
      <p className="text-sm text-gray-400">{message}</p>
    </div>
  );
}
