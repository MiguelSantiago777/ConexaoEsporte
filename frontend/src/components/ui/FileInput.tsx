import { ChangeEvent } from "react";

interface Props {
  label: string;
  file: File | null;
  onChange: (file: File | null) => void;
  accept?: string;
}

export function FileInput({ label, file, onChange, accept }: Props) {
  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    onChange(e.target.files?.[0] ?? null);
  }

  return (
    <label className="block">
      <span className="block text-sm font-medium text-gray-700 mb-1">{label}</span>
      <input
        type="file"
        accept={accept}
        onChange={handleChange}
        className="block w-full text-sm text-gray-500 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:bg-brand-light file:text-brand-dark file:font-medium file:cursor-pointer hover:file:bg-brand/10 cursor-pointer"
      />
      {file && <span className="block text-xs text-brand-dark mt-1 truncate">✓ {file.name}</span>}
    </label>
  );
}
