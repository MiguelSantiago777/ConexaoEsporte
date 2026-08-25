import { CSSProperties, ReactNode } from "react";

export function Card({
  children,
  title,
  subtitle,
  actions,
  className = "",
  style,
}: {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-gray-200/80 p-6 transition-shadow duration-200 ${className}`}
      style={style}
    >
      {(title || actions) && (
        <div className="flex items-start justify-between mb-4 gap-4">
          <div>
            {title && <h2 className="text-lg font-semibold text-brand-dark">{title}</h2>}
            {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
          </div>
          {actions && <div className="shrink-0">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
