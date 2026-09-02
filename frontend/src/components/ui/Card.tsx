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
      className={`bg-white rounded-xl p-5 sm:p-8 shadow-sm transition-shadow duration-200 ${className}`}
      style={style}
    >
      {(title || actions) && (
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-5 gap-3 sm:gap-4">
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
