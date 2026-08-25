import { SelectHTMLAttributes, forwardRef } from "react";

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
}

export const Select = forwardRef<HTMLSelectElement, Props>(({ label, className = "", children, ...props }, ref) => (
  <label className="block">
    {label && <span className="block text-sm font-medium text-gray-700 mb-1">{label}</span>}
    <select
      ref={ref}
      className={`w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-900 transition-all duration-150 hover:border-gray-400 focus:ring-2 focus:ring-brand/40 focus:border-brand outline-none disabled:bg-gray-100 disabled:text-gray-400 disabled:hover:border-gray-300 ${className}`}
      {...props}
    >
      {children}
    </select>
  </label>
));
Select.displayName = "Select";
