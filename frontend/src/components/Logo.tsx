export default function Logo({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
      <rect width="32" height="32" rx="7" fill="#0f1b3d" />
      <path d="M13.5 8a2.5 2.5 0 0 1 5 0v9.1a4.6 4.6 0 1 1-5 0z" fill="none" stroke="#fff" strokeWidth="1.7" strokeLinejoin="round" />
      <rect x="15.2" y="12" width="1.6" height="8.5" rx="0.8" fill="#ef8a1f" />
      <circle cx="16" cy="21" r="2.2" fill="#ef8a1f" />
    </svg>
  );
}
