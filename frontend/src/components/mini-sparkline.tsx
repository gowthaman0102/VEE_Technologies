"use client";

import { useRef } from "react";

/**
 * AnimatedSparkline — smooth animated sinusoidal wave matching the reference design.
 *
 * The reference shows a continuous, gently-undulating sine wave that flows across
 * the full width of the card. We achieve this by:
 *  1. Generating a double-wide SVG path (2× the display width) with a seamless
 *     tiling sine wave (end state == start state).
 *  2. Using a CSS keyframe that translates the path -50% horizontally in a loop,
 *     creating the illusion of a live, flowing waveform.
 */
export function MiniSparkline({
  data = [],
  color = "#3C9CF4",
  height = 32,
  width = 220,
}: {
  data?: number[];
  color?: string;
  height?: number;
  width?: number;
}) {
  if (!data.length) {
    return (
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-hidden="true">
        <path d={`M 0 ${height / 2} L ${width} ${height / 2}`} fill="none" stroke={color} strokeOpacity="0.2" strokeWidth="1.5" />
      </svg>
    );
  }

  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = Math.max(max - min, 1);
  const points = data.map((value, index) => {
    const x = (index / Math.max(data.length - 1, 1)) * width;
    const normalized = (value - min) / range;
    const y = height - normalized * (height - 8) - 4;
    return `${x},${y}`;
  });

  const pathD = `M ${points.join(" L ")}`;

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <style>{`
          .mini-sparkline-draw {
            stroke-dasharray: 800;
            stroke-dashoffset: 800;
            animation: miniSparklineDraw 1.3s ease-out forwards;
          }
          @keyframes miniSparklineDraw {
            to { stroke-dashoffset: 0; }
          }
          @media (prefers-reduced-motion: reduce) {
            .mini-sparkline-draw { animation: none; stroke-dashoffset: 0; }
          }
        `}</style>
      </defs>
      <path d={pathD} fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="mini-sparkline-draw" opacity="0.95" />
    </svg>
  );
}

export function AnimatedSparkline({
  color = "#3C9CF4",
  amplitude = 7,
  speed = 4, // seconds per full cycle
}: {
  color?: string;
  amplitude?: number;
  speed?: number;
}) {
  const pathRef = useRef<SVGPathElement>(null);

  // Build a seamless tiling wave path.
  // We render 2 full wavelength cycles over width=400 (displayed at 200px).
  // Points are placed every 4px for a smooth curve.
  const W = 400;   // total SVG width (2× display)
  const H = 40;    // SVG height
  const midY = H / 2;
  const step = 4;

  // Two full sine cycles across W — ends at exact same y as start (seamless)
  const pts: { x: number; y: number }[] = [];
  for (let x = 0; x <= W; x += step) {
    const phase = (x / W) * Math.PI * 4; // 2 full cycles
    // Add slight harmonic for organic feel (sin + 0.3×sin(2f))
    const y = midY - amplitude * (Math.sin(phase) + 0.3 * Math.sin(phase * 2 + 1.2));
    pts.push({ x, y });
  }

  // Build cubic Catmull-Rom bezier path
  let d = `M ${pts[0].x} ${pts[0].y.toFixed(2)}`;
  const tension = 0.4;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(i - 1, 0)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(i + 2, pts.length - 1)];

    const cp1x = p1.x + (p2.x - p0.x) * tension;
    const cp1y = p1.y + (p2.y - p0.y) * tension;
    const cp2x = p2.x - (p3.x - p1.x) * tension;
    const cp2y = p2.y - (p3.y - p1.y) * tension;

    d += ` C ${cp1x.toFixed(2)} ${cp1y.toFixed(2)}, ${cp2x.toFixed(2)} ${cp2y.toFixed(2)}, ${p2.x.toFixed(2)} ${p2.y.toFixed(2)}`;
  }

  const animId = `wave-${color.replace("#", "")}`;

  return (
    <svg
      width="100%"
      height="100%"
      viewBox={`0 0 200 ${H}`}
      preserveAspectRatio="none"
      className="overflow-hidden"
      aria-hidden="true"
    >
      <defs>
        <style>{`
          @keyframes ${animId} {
            from { transform: translateX(0); }
            to   { transform: translateX(-50%); }
          }
          @media (prefers-reduced-motion: reduce) {
            .wave-path-${animId} { animation: none !important; }
          }
        `}</style>
      </defs>

      {/* The path is double-wide; animation scrolls it left by 50% (= 1 tile) seamlessly */}
      <g>
        <path
          ref={pathRef}
          className={`wave-path-${animId}`}
          d={d}
          fill="none"
          stroke={color}
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            animation: `${animId} ${speed}s linear infinite`,
            willChange: "transform",
          }}
        />
      </g>
    </svg>
  );
}
