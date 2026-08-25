import { InputHTMLAttributes, forwardRef } from "react";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, Props>(({ label, hint, className = "", ...props }, ref) => (
  <label className="block">
    {label && <span className="block text-sm font-medium text-gray-700 mb-1">{label}</span>}
    <input
      ref={ref}
      className={`w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm placeholder:text-gray-400 transition-all duration-150 hover:border-gray-400 focus:ring-2 focus:ring-brand/40 focus:border-brand outline-none disabled:bg-gray-100 disabled:text-gray-400 disabled:hover:border-gray-300 ${className}`}
      {...props}
    />
    {hint && <span className="block text-xs text-gray-400 mt-1">{hint}</span>}
  </label>
));
Input.displayName = "Input";
