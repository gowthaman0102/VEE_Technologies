import { useEffect, useRef, useState } from "react";
import { ShieldAlert, AlertTriangle } from "lucide-react";
import { MiniRiskBars } from "./mini-risk-bars";

const HIGHLIGHT_DURATION_MS = 900;

export function RiskOverviewCard({
  label,
  value,
  level,
  trend,
  onOpen,
  chartData,
}: {
  label: string;
  value: string | number;
  level: "high" | "critical";
  trend?: string;
  onOpen?: () => void;
  chartData?: number[];
}) {
  const prevValueRef = useRef<string | number | null>(null);
  const [isHighlighted, setIsHighlighted] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (prevValueRef.current === null) {
      prevValueRef.current = value;
      return;
    }
    if (prevValueRef.current !== value) {
      prevValueRef.current = value;
      if (timerRef.current) clearTimeout(timerRef.current);
      setIsHighlighted(true);
      timerRef.current = setTimeout(() => setIsHighlighted(false), HIGHLIGHT_DURATION_MS);
    }
  }, [value]);

  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current); }, []);

  const config = {
    high: {
      bg: "bg-surface",
      border: "border-border",
      icon: AlertTriangle,
      iconColor: "text-critical",
      iconBg: "bg-critical",
      textColor: "text-text",
      valueColor: "text-text",
      highlightClass: "ring-2 ring-critical/30",
    },
    critical: {
      bg: "bg-surface",
      border: "border-border",
      icon: ShieldAlert,
      iconColor: "text-medium",
      iconBg: "bg-medium",
      textColor: "text-text",
      valueColor: "text-text",
      highlightClass: "ring-2 ring-medium/30",
    },
  }[level];

  const Icon = config.icon;
  const Component = onOpen ? "button" : "div";
  const buttonProps = onOpen ? { 
    onClick: onOpen, 
    type: "button" as const,
    "aria-label": `View details for ${label}` 
  } : {};

  return (
    <Component
      {...buttonProps}
      className={[
        "relative flex h-full w-full flex-col justify-between overflow-hidden rounded-[14px] border p-[18px] text-left transition-all duration-200 shadow-[0_3px_12px_rgba(23,54,76,0.03)]",
        config.bg,
        config.border,
        onOpen ? "cursor-pointer hover:shadow-[0_4px_16px_rgba(23,54,76,0.06)] hover:-translate-y-[2px]" : "",
        isHighlighted ? config.highlightClass : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="flex h-full w-full">
        {/* Left: Icon block */}
        <div className={`flex h-[56px] w-[56px] shrink-0 items-center justify-center rounded-[12px] ${config.iconBg} text-white`}>
          <Icon size={26} strokeWidth={2.2} />
        </div>
        
        {/* Middle: Content */}
        <div className="ml-4 flex flex-1 flex-col justify-between">
          <div className="flex items-start justify-between">
            <p className="text-[14px] font-semibold text-text">{label}</p>
          </div>
          
          <div className="flex items-end justify-between mt-1">
            <p
              key={String(value)}
              className={[
                "text-[34px] font-bold leading-none tracking-tight",
                config.valueColor || config.textColor,
                "transition-transform duration-300 ease-out",
                isHighlighted ? "scale-[1.05]" : "scale-100",
                "motion-reduce:scale-100 motion-reduce:transition-none",
              ].join(" ")}
            >
              {value}
            </p>
          </div>
        </div>
      </div>
    </Component>
  );
}
