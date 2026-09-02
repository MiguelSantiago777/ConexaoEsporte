/**
 * Marca de assinatura visual do sistema: o canto de uma quadra — linha de
 * contorno, arco do círculo central e a marca do pênalti. Usada com
 * moderação em poucos pontos de maior peso (PageHeader, sidebar, tela de
 * login) — nunca como decoração repetida em cada card.
 */
export function CourtMark({ className = "w-7 h-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 28 28" className={className} fill="none" aria-hidden="true">
      <path d="M2 2 H15 M2 2 V15" className="stroke-accent" strokeWidth="2.2" strokeLinecap="round" />
      <path d="M26 9 A9 9 0 0 1 17 18" className="stroke-brand/35" strokeWidth="1.4" fill="none" />
      <circle cx="20.5" cy="20.5" r="2.1" className="fill-court" />
    </svg>
  );
}
