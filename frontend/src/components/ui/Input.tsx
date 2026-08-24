import { InputHTMLAttributes, forwardRef } from "react";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export const Input = forwardRef<HTMLInputElement, Props>(({ label, className = "", ...props }, ref) => (
  <label className="block">
    {label && <span className="block text-sm font-medium text-gray-700 mb-1">{label}</span>}
    <input
      ref={ref}
      className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-brand focus:border-brand outline-none ${className}`}
      {...props}
    />
  </label>
));
Input.displayName = "Input";
