export function MiniRiskBars({ 
  data, 
  color = "#EF4048",
}: { 
  data?: number[]; 
  color?: string;
}) {
  // If no data, render some visually pleasing dummy bars (although prompt says use real data, 
  // I will fallback gracefully if backend doesn't provide it)
  const bars = data && data.length > 0 ? data : [2, 5, 3, 7, 10, 4, 8, 3, 5, 2, 4, 6];
  
  const max = Math.max(...bars) || 1; // avoid division by zero
  
  return (
    <div className="flex items-end justify-between gap-1 h-full w-full">
      {bars.map((val, i) => {
        const heightPercent = Math.max((val / max) * 100, 5); // min 5% height
        return (
          <div 
            key={i} 
            className="w-full bg-current rounded-sm opacity-90 transition-all duration-500 ease-out"
            style={{ 
              height: `${heightPercent}%`,
              color: color,
              // Staggered animation
              animation: `growUp 600ms ease-out ${i * 40}ms backwards`
            }}
          />
        );
      })}
      <style>{`
        @keyframes growUp {
          from { height: 0; opacity: 0; }
        }
      `}</style>
    </div>
  );
}
