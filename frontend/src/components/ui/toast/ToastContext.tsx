import { createContext, ReactNode, useCallback, useContext, useRef, useState } from "react";
import { AlertCircleIcon, CheckCircleIcon, CloseIcon } from "@/components/ui/icons";

type ToastVariant = "success" | "error" | "warning";

interface ToastItem {
  id: number;
  variant: ToastVariant;
  message: string;
}

interface ToastApi {
  success: (message: string) => void;
  error: (message: string) => void;
  warning: (message: string) => void;
}

const ToastContext = createContext<ToastApi | undefined>(undefined);

const DURATION_MS = 4500;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(0);

  const remove = useCallback((id: number) => {
    setToasts((atual) => atual.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (variant: ToastVariant, message: string) => {
      const id = nextId.current++;
      setToasts((atual) => [...atual, { id, variant, message }]);
      window.setTimeout(() => remove(id), DURATION_MS);
    },
    [remove]
  );

  const api: ToastApi = {
    success: (message) => push("success", message),
    error: (message) => push("error", message),
    warning: (message) => push("warning", message),
  };

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div
        aria-live="polite"
        className="fixed top-4 right-4 z-[100] w-full max-w-sm space-y-2 pointer-events-none"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className="animate-toast-in pointer-events-auto flex items-start gap-3 bg-white rounded-xl shadow-lg border border-gray-200/80 p-4"
          >
            {t.variant === "success" && <CheckCircleIcon className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />}
            {t.variant === "warning" && <AlertCircleIcon className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />}
            {t.variant === "error" && <AlertCircleIcon className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />}
            <p className="text-sm text-gray-700 flex-1 leading-snug">{t.message}</p>
            <button
              type="button"
              onClick={() => remove(t.id)}
              className="text-gray-400 hover:text-gray-600 shrink-0"
              aria-label="Fechar notificação"
            >
              <CloseIcon />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast deve ser usado dentro de <ToastProvider>");
  return ctx;
}
