interface Props {
  className?: string;
}

export function PencilIcon({ className = "w-4 h-4" }: Props) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path
        d="M13.5 3.5l3 3L7 16H4v-3L13.5 3.5z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function TrashIcon({ className = "w-4 h-4" }: Props) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path
        d="M4 6h12M8 6V4.5A1.5 1.5 0 019.5 3h1A1.5 1.5 0 0112 4.5V6m-6 0v9a1 1 0 001 1h6a1 1 0 001-1V6M8.5 9v5M11.5 9v5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function HomeIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M4 11.5 12 4l8 7.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M6 10v8.5a1 1 0 001 1h10a1 1 0 001-1V10" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M10 19.5V14h4v5.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function BuildingIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="5" y="3.5" width="10" height="17" rx="1" strokeLinejoin="round" />
      <path d="M9 7.5h2M9 11h2M9 14.5h2M15 11h4v9.5h-4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function TrophyIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M7 4h10v4a5 5 0 01-10 0V4z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M7 5H4v1a3 3 0 003 3M17 5h3v1a3 3 0 01-3 3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 13v3.5M9 20.5h6M9.5 20.5c0-2 .8-3 2.5-3s2.5 1 2.5 3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function UsersIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <circle cx="9" cy="8" r="3" />
      <path d="M3.5 20c.5-3.5 2.8-5.5 5.5-5.5s5 2 5.5 5.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="17" cy="8.5" r="2.4" />
      <path d="M15.5 14.8c2.1.4 3.6 2.1 4 5.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function ClipboardIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="6" y="4.5" width="12" height="16" rx="1.5" strokeLinejoin="round" />
      <path d="M9 4.5V4a1.5 1.5 0 011.5-1.5h3A1.5 1.5 0 0115 4v.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 11h6M9 14.5h6M9 18h3.5" strokeLinecap="round" />
    </svg>
  );
}

export function AcademicCapIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M12 5 3 9.5 12 14l9-4.5L12 5z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M7 11.7v4c0 1.2 2.2 2.3 5 2.3s5-1.1 5-2.3v-4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M20 9.5V15" strokeLinecap="round" />
    </svg>
  );
}

export function CalendarCheckIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="4" y="5" width="16" height="15" rx="1.5" strokeLinejoin="round" />
      <path d="M4 9.5h16M8 3v3.5M16 3v3.5" strokeLinecap="round" />
      <path d="M9 14l2 2 4-4.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function CalendarOffIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="4" y="5" width="16" height="15" rx="1.5" strokeLinejoin="round" />
      <path d="M4 9.5h16M8 3v3.5M16 3v3.5" strokeLinecap="round" />
      <path d="M7.5 12.5l9 7M16.5 12.5l-9 7" strokeLinecap="round" />
    </svg>
  );
}

export function DocumentTextIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M7 3.5h7l4 4v13a1 1 0 01-1 1H7a1 1 0 01-1-1v-16a1 1 0 011-1z" strokeLinejoin="round" />
      <path d="M14 3.5V8h4" strokeLinejoin="round" />
      <path d="M9 12.5h6M9 15.5h6M9 18.5h3.5" strokeLinecap="round" />
    </svg>
  );
}

export function KeyIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <circle cx="8" cy="14.5" r="4" />
      <path d="M11 11.5 19 3.5M16 6.5l2.5 2.5M18.5 4l1.5 1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function LogoutIcon({ className = "w-4 h-4" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M9 4H6a1.5 1.5 0 00-1.5 1.5v13A1.5 1.5 0 006 20h3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M14 8l4.5 4-4.5 4M9.5 12h9" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function CheckCircleIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
      <circle cx="12" cy="12" r="9" />
      <path d="M8.5 12.3l2.3 2.3 4.7-5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function AlertCircleIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7.5v6" strokeLinecap="round" />
      <circle cx="12" cy="16.3" r="0.9" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function InboxIcon({ className = "w-10 h-10" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4">
      <path d="M4 13l2.5-7.5A1.5 1.5 0 018 4.5h8a1.5 1.5 0 011.5 1L20 13" strokeLinecap="round" strokeLinejoin="round" />
      <path
        d="M4 13h5a.5.5 0 01.5.3l.7 1.7a1 1 0 00.9.6h1.8a1 1 0 00.9-.6l.7-1.7a.5.5 0 01.5-.3h5v5a1.5 1.5 0 01-1.5 1.5H5.5A1.5 1.5 0 014 18v-5z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function SpinnerIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={`${className} animate-spin`} viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.5" opacity="0.2" />
      <path d="M21 12a9 9 0 00-9-9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

export function IdentificationIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="3.5" y="5" width="17" height="14" rx="1.5" strokeLinejoin="round" />
      <circle cx="8.5" cy="11" r="2" />
      <path d="M5.5 16c.4-1.7 1.6-2.5 3-2.5s2.6.8 3 2.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M13.5 9.5h5M13.5 12.5h5M13.5 15.5h3" strokeLinecap="round" />
    </svg>
  );
}

export function ArchiveIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="3.5" y="4" width="17" height="4" rx="1" strokeLinejoin="round" />
      <path d="M4.5 8v10.5a1 1 0 001 1h13a1 1 0 001-1V8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9.5 12.5h5" strokeLinecap="round" />
    </svg>
  );
}

export function BoxIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M4 8l8-4.5L20 8v8l-8 4.5L4 16V8z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M4 8l8 4.5M12 12.5L20 8M12 12.5V21" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function CameraIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M4 8.5a1.5 1.5 0 011.5-1.5h2l1-2h7l1 2h2A1.5 1.5 0 0120 8.5v9a1.5 1.5 0 01-1.5 1.5h-13A1.5 1.5 0 014 17.5v-9z" strokeLinejoin="round" />
      <circle cx="12" cy="13" r="3.3" />
    </svg>
  );
}

export function ChartPieIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M12 3.5a8.5 8.5 0 108.5 8.5H12V3.5z" strokeLinejoin="round" />
      <path d="M15.5 3.9A8.51 8.51 0 0120.1 8.5H15.5V3.9z" strokeLinejoin="round" />
    </svg>
  );
}

export function ChartBarIcon({ className = "w-5 h-5" }: Props) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M5 20V10M12 20V4M19 20v-7" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M3.5 20.5h17" strokeLinecap="round" />
    </svg>
  );
}

export function CloseIcon({ className = "w-4 h-4" }: Props) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M5 5l10 10M15 5L5 15" strokeLinecap="round" />
    </svg>
  );
}
