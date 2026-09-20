/**
 * KPI Icons matching the reference design:
 * - Total Articles: document/news icon (blue)
 * - Processed Intelligence: radial gear/radar icon (violet)
 * - Monitored Companies: office building with lock icon (purple)
 */

export function KpiArticleIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden="true">
      {/* Outer rounded rect */}
      <rect x="8" y="4" width="32" height="40" rx="5" stroke="currentColor" strokeWidth="3" />
      {/* Top header band inside doc */}
      <rect x="14" y="10" width="20" height="9" rx="2" fill="currentColor" opacity="0.25" />
      {/* Text lines */}
      <line x1="14" y1="26" x2="34" y2="26" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="14" y1="32" x2="34" y2="32" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="14" y1="38" x2="26" y2="38" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

export function KpiIntelligenceIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden="true">
      {/* Outer circle */}
      <circle cx="24" cy="24" r="19" stroke="currentColor" strokeWidth="3" />
      {/* Middle circle */}
      <circle cx="24" cy="24" r="12" stroke="currentColor" strokeWidth="2.5" strokeDasharray="4 3" />
      {/* Inner solid circle */}
      <circle cx="24" cy="24" r="5" fill="currentColor" />
      {/* 4 antenna spokes at N/E/S/W */}
      <line x1="24" y1="5" x2="24" y2="12" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="24" y1="36" x2="24" y2="43" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="5" y1="24" x2="12" y2="24" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="36" y1="24" x2="43" y2="24" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

export function KpiCompanyIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden="true">
      {/* Building left wing */}
      <rect x="4" y="18" width="14" height="26" rx="2" stroke="currentColor" strokeWidth="2.5" />
      {/* Building right wing */}
      <rect x="30" y="18" width="14" height="26" rx="2" stroke="currentColor" strokeWidth="2.5" />
      {/* Windows left */}
      <rect x="8" y="22" width="4" height="4" rx="1" fill="currentColor" opacity="0.4" />
      <rect x="8" y="30" width="4" height="4" rx="1" fill="currentColor" opacity="0.4" />
      {/* Windows right */}
      <rect x="36" y="22" width="4" height="4" rx="1" fill="currentColor" opacity="0.4" />
      <rect x="36" y="30" width="4" height="4" rx="1" fill="currentColor" opacity="0.4" />
      {/* Center lock body */}
      <rect x="17" y="26" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="2.5" />
      {/* Lock shackle arc */}
      <path d="M19 26 C19 21 29 21 29 26" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" fill="none" />
      {/* Keyhole */}
      <circle cx="24" cy="31" r="1.5" fill="currentColor" />
    </svg>
  );
}

export function KpiHighRiskIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden="true">
      {/* Outer triangle */}
      <path d="M24 4 L44 40 L4 40 Z" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      {/* Inner exclamation mark */}
      <line x1="24" y1="16" x2="24" y2="28" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" />
      <circle cx="24" cy="34" r="2.5" fill="currentColor" />
    </svg>
  );
}

export function KpiCriticalRiskIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden="true">
      {/* Shield shape */}
      <path d="M24 4 L6 10 V22 C6 32 14 41 24 44 C34 41 42 32 42 22 V10 Z" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      {/* Inner danger circle */}
      <circle cx="24" cy="22" r="7" stroke="currentColor" strokeWidth="2.5" strokeDasharray="4 2" />
      <circle cx="24" cy="22" r="3" fill="currentColor" />
    </svg>
  );
}
