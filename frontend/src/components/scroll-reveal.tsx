"use client";

import { useEffect, useRef, useState } from "react";

type Direction = "up" | "down" | "left" | "right" | "fade" | "scale";

interface ScrollRevealProps {
  children: React.ReactNode;
  /** Extra Tailwind/CSS classes on the wrapper */
  className?: string;
  /** Delay in ms before the transition starts */
  delay?: number;
  /** Animation direction */
  direction?: Direction;
  /** Fraction of element that must be visible to trigger (0–1) */
  threshold?: number;
  /** If true the animation only plays once (no replay on scroll-back) */
  once?: boolean;
  /** Duration in ms */
  duration?: number;
}

const HIDDEN: Record<Direction, string> = {
  up:    "opacity-0 translate-y-10",
  down:  "opacity-0 -translate-y-10",
  left:  "opacity-0 translate-x-10",
  right: "opacity-0 -translate-x-10",
  fade:  "opacity-0",
  scale: "opacity-0 scale-90",
};

const VISIBLE: Record<Direction, string> = {
  up:    "opacity-100 translate-y-0",
  down:  "opacity-100 translate-y-0",
  left:  "opacity-100 translate-x-0",
  right: "opacity-100 translate-x-0",
  fade:  "opacity-100",
  scale: "opacity-100 scale-100",
};

/**
 * Wraps children in a div that animates into view when scrolled into the
 * viewport. By default the animation repeats each time the element re-enters
 * (scroll away → scroll back → animates again). Set `once` to stop after first.
 */
export function ScrollReveal({
  children,
  className = "",
  delay = 0,
  direction = "up",
  threshold = 0.12,
  once = false,
  duration = 650,
}: ScrollRevealProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);
  const hasAnimated = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          hasAnimated.current = true;
          if (once) observer.disconnect();
        } else {
          // Only reset if not in "once" mode
          if (!once) setInView(false);
        }
      },
      { threshold },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold, once]);

  return (
    <div
      ref={ref}
      className={`
        transform-gpu will-change-transform
        transition-[opacity,transform]
        ${inView ? VISIBLE[direction] : HIDDEN[direction]}
        ${className}
      `}
      style={{
        transitionDuration: `${duration}ms`,
        transitionDelay: inView ? `${delay}ms` : "0ms",
        transitionTimingFunction: "cubic-bezier(0.22, 1, 0.36, 1)",
      }}
    >
      {children}
    </div>
  );
}
