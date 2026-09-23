import type { ReactNode } from "react";

type CosmicHeroVariant = "article-settings" | "intelligence" | "risk" | "analytics" | "search";

type CosmicPageHeroProps = {
  variant: CosmicHeroVariant;
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
  status?: ReactNode;
  rangeControl?: ReactNode;
  imageSrc?: string;
};

function HeroVisual({ variant, imageSrc }: { variant: CosmicHeroVariant; imageSrc?: string }) {
  const visualSrc = imageSrc ?? "/hero-globe.png";

  return (
    <div className={`cosmic-hero-visual cosmic-hero-visual-${variant}`} aria-hidden="true">
      <img src={visualSrc} alt="" className="cosmic-hero-image" />
      <div className="cosmic-hero-bg cosmic-hero-bg-anim" />
      <div className="cosmic-hero-bg cosmic-hero-lines-anim" />
      <svg className="cosmic-hero-network" viewBox="0 0 700 300" fill="none">
        <g className="cosmic-hero-network-paths" stroke="#C5A8FF" strokeWidth="1.5" strokeLinecap="round" opacity="0.7">
          <path d="M84 228C178 152 211 232 300 170S425 53 511 125 605 151 685 61" strokeDasharray="7 13" />
          <path d="M38 113C132 80 177 125 251 91S382 59 448 106 555 239 676 188" strokeDasharray="3 17" />
          <path d="M130 281C205 218 261 250 326 215S439 168 503 206 593 239 665 218" strokeDasharray="2 22" />
        </g>
        <g className="cosmic-hero-network-nodes" fill="#E5D8FF">
          <circle cx="84" cy="228" r="4" /><circle cx="300" cy="170" r="4" /><circle cx="511" cy="125" r="5" /><circle cx="685" cy="61" r="4" />
          <circle cx="251" cy="91" r="3" /><circle cx="448" cy="106" r="4" /><circle cx="676" cy="188" r="4" />
        </g>
        <g className="cosmic-hero-network-particles" fill="#FFFFFF">
          <circle cx="176" cy="166" r="2.5" /><circle cx="370" cy="72" r="2" /><circle cx="577" cy="219" r="2.5" /><circle cx="625" cy="102" r="2" />
        </g>
        <g className="cosmic-hero-network-orbits" stroke="#E5D8FF" strokeWidth="1" opacity="0.45">
          <ellipse cx="522" cy="153" rx="142" ry="42" transform="rotate(-18 522 153)" />
          <ellipse cx="522" cy="153" rx="118" ry="28" transform="rotate(24 522 153)" />
        </g>
      </svg>
      <div className="cosmic-hero-shimmer" />
      <div className="cosmic-hero-overlay" />
    </div>
  );
}

export function CosmicPageHero({ variant, eyebrow, title, description, action, status, rangeControl, imageSrc }: CosmicPageHeroProps) {
  return (
    <header className="cosmic-page-hero">
      <HeroVisual variant={variant} imageSrc={imageSrc} />
      <div className="cosmic-page-hero-content">
        <div className="cosmic-page-hero-copy">
          <span className="cosmic-page-hero-accent" />
          <div>
            <p className="cosmic-page-hero-context">NEAR REAL-TIME MONITORING</p>
            <p className="cosmic-page-hero-command">Intelligence Command Center</p>
            <p className="cosmic-page-hero-eyebrow">{eyebrow}</p>
            <h1>{title}</h1>
            <p className="cosmic-page-hero-description">{description}</p>
          </div>
        </div>
        <div className="cosmic-page-hero-controls">
          {rangeControl && <div className="cosmic-page-hero-range">{rangeControl}</div>}
          {status && <div className="cosmic-page-hero-status">{status}</div>}
          {action && <div className="cosmic-page-hero-action">{action}</div>}
        </div>
      </div>
    </header>
  );
}