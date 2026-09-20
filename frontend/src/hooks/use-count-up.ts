"use client";

import { useEffect, useState } from "react";

export function useCountUp(endValue: number, durationMs: number = 400) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    // If reduced motion is preferred, jump straight to the end
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReducedMotion || endValue === 0) {
      const timeoutId = setTimeout(() => setCount(endValue), 0);
      return () => clearTimeout(timeoutId);
    }

    let startTime: number | null = null;
    let animationFrameId: number;

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = timestamp - startTime;
      
      // Easing function (easeOutExpo)
      const easeOut = progress === durationMs ? 1 : 1 - Math.pow(2, -10 * progress / durationMs);
      
      if (progress < durationMs) {
        setCount(Math.round(endValue * easeOut));
        animationFrameId = requestAnimationFrame(animate);
      } else {
        setCount(endValue);
      }
    };

    animationFrameId = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(animationFrameId);
  }, [endValue, durationMs]);

  return count;
}
