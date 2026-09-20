import { useState } from "react";
import Image from "next/image";

interface PublisherLogoProps {
  publisherName: string;
  size?: number;
  className?: string;
}

export function PublisherLogo({ publisherName, size = 32, className = "" }: PublisherLogoProps) {
  const [error, setError] = useState(false);

  // Derive a domain from publisher name for clearbit logo (heuristic)
  // E.g. "Yahoo News" -> "yahoo.com", "Financial Times" -> "ft.com"
  const getDomainHeuristic = (name: string) => {
    const lower = name.toLowerCase();
    if (lower.includes("yahoo")) return "yahoo.com";
    if (lower.includes("reuters")) return "reuters.com";
    if (lower.includes("forbes")) return "forbes.com";
    if (lower.includes("bloomberg")) return "bloomberg.com";
    if (lower.includes("financial post")) return "financialpost.com";
    if (lower.includes("financial times")) return "ft.com";
    if (lower.includes("fortune")) return "fortune.com";
    if (lower.includes("techcrunch")) return "techcrunch.com";
    if (lower.includes("the verge")) return "theverge.com";
    if (lower.includes("wsj") || lower.includes("wall street journal")) return "wsj.com";
    if (lower.includes("nyt") || lower.includes("new york times")) return "nytimes.com";
    if (lower.includes("cnbc")) return "cnbc.com";
    if (lower.includes("cnn")) return "cnn.com";
    if (lower.includes("bbc")) return "bbc.co.uk";
    if (lower.includes("rte")) return "rte.ie";
    if (lower.includes("404 media")) return "404media.co";
    if (lower.includes("pypi")) return "pypi.org";
    if (lower.includes("business insider")) return "businessinsider.com";
    if (lower.includes("al jazeera")) return "aljazeera.com";
    // Fallback: try to just remove spaces and add .com
    const stripped = lower.replace(/[^a-z0-9]/g, "");
    return `${stripped}.com`;
  };

  const domain = getDomainHeuristic(publisherName);
  
  // Clearbit Logo API is a common free logo API, or we can use Google's favicon service.
  // Using Google Favicon as it's more reliable for small sizes without auth.
  const logoUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;

  // Initials fallback
  const initials = publisherName
    .split(" ")
    .map(w => w[0])
    .filter(Boolean)
    .join("")
    .slice(0, 2)
    .toUpperCase() || "?";

  return (
    <div 
      className={`relative flex shrink-0 items-center justify-center overflow-hidden rounded-md bg-surface shadow-sm border border-border ${className}`}
      style={{ width: size, height: size }}
    >
      {!error ? (
        <Image
          src={logoUrl}
          alt={`${publisherName} logo`}
          fill
          className="object-contain p-1"
          sizes={`${size}px`}
          onError={() => setError(true)}
          unoptimized // External Google API
        />
      ) : (
        <span className="font-semibold text-muted" style={{ fontSize: size * 0.45 }}>
          {initials}
        </span>
      )}
    </div>
  );
}
