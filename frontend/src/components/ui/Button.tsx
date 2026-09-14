import { ButtonHTMLAttributes } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
}

export function Button({ variant = "primary", className = "", ...props }: Props) {
  const base =
    "inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100";
  const variants = {
    primary: "bg-brand text-white shadow-sm hover:bg-brand-dark hover:shadow-md focus-visible:ring-brand/50",
    secondary:
      "bg-white border border-slate-300 text-slate-700 hover:bg-slate-300/10 hover:border-slate-400 focus-visible:ring-slate-300",
    ghost: "text-brand hover:bg-brand-light focus-visible:ring-brand/30",
    danger: "bg-danger text-white shadow-sm hover:bg-danger-dark hover:shadow-md focus-visible:ring-danger/40",
  };
  return <button className={`${base} ${variants[variant]} ${className}`} {...props} />;
}
