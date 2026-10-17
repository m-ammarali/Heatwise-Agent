type P = { className?: string };
const base = { fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

export const CheckIcon = ({ className = "w-4 h-4" }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...base} aria-hidden><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
);
export const ArrowRight = ({ className = "w-4 h-4" }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...base} aria-hidden><path d="M5 12h14M13 6l6 6-6 6" /></svg>
);
export const ArrowLeft = ({ className = "w-4 h-4" }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...base} aria-hidden><path d="M19 12H5M11 6l-6 6 6 6" /></svg>
);
export const ExternalIcon = ({ className = "w-3.5 h-3.5" }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...base} aria-hidden><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" /></svg>
);
export const CloseIcon = ({ className = "w-4 h-4" }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...base} aria-hidden><path d="M6 6l12 12M18 6L6 18" /></svg>
);
export const ChevronDown = ({ className = "w-4 h-4" }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...base} aria-hidden><path d="M6 9l6 6 6-6" /></svg>
);
export const PinIcon = ({ className = "w-4 h-4" }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...base} aria-hidden><path d="M12 21s7-6.2 7-11.5A7 7 0 0 0 5 9.5C5 14.8 12 21 12 21z" /><circle cx="12" cy="9.5" r="2.5" /></svg>
);
export const DownloadIcon = ({ className = "w-4 h-4" }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...base} aria-hidden><path d="M12 4v11M7 11l5 5 5-5M5 20h14" /></svg>
);
