import { ReactNode } from "react";

interface Props {
  children: ReactNode;
  variant?: "brand" | "accent" | "gray" | "court" | "danger";
}

export function Badge({ children, variant = "gray" }: Props) {
  const variants = {
    brand: "bg-brand-light text-brand-dark ring-1 ring-inset ring-brand/10",
    accent: "bg-accent-light text-accent-dark ring-1 ring-inset ring-accent/20",
    gray: "bg-gray-100 text-gray-500 ring-1 ring-inset ring-gray-200",
    court: "bg-court-light text-court-dark ring-1 ring-inset ring-court/20",
    danger: "bg-danger-light text-danger-dark ring-1 ring-inset ring-danger/20",
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${variants[variant]}`}>
      {children}
    </span>
  );
}
