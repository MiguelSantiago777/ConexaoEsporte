import { ButtonHTMLAttributes } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
}

export function Button({ variant = "primary", className = "", ...props }: Props) {
  const base = "px-4 py-2 rounded-md font-medium transition disabled:opacity-50 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-brand text-white hover:bg-brand-dark",
    secondary: "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50",
    ghost: "text-brand hover:bg-brand-light",
  };
  return <button className={`${base} ${variants[variant]} ${className}`} {...props} />;
}
