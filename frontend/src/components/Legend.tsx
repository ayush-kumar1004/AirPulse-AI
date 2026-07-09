import React from "react";
import { OverlayMode } from "./OverlayToggle";

interface LegendProps {
  activeMode: OverlayMode;
}

export default function Legend({ activeMode }: LegendProps) {
  const isSourceMode = activeMode === "source";

  return (
    <div className="bg-[#1E293B]/60 backdrop-blur-xl rounded-xl p-4 border border-[#334155] shadow-2xl w-72 z-10 text-white font-sans">
      <div className="flex items-center mb-3">
        <span className="text-[11px] font-bold text-[#94A3B8] tracking-widest uppercase">
          {isSourceMode ? "Dominant Source Legend" : "CPCB AQI Scale"}
        </span>
      </div>

      {isSourceMode ? (
        <div className="space-y-2">
          <div className="grid grid-cols-2 gap-2 text-xs font-semibold text-[#bbc9cd]">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#22d3ee] shadow-[0_0_8px_#22d3ee]" />
              <span>Traffic</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#f97316] shadow-[0_0_8px_#f97316]" />
              <span>Construction</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#a855f7] shadow-[0_0_8px_#a855f7]" />
              <span>Industry</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#78350f] shadow-[0_0_8px_#78350f]" />
              <span>Dust</span>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <div className="flex gap-1 h-3 w-full rounded-full overflow-hidden mb-3">
            <div className="flex-1 bg-[#4ae176]" title="Good" />
            <div className="flex-1 bg-[#22D3EE]" title="Satisfactory" />
            <div className="flex-1 bg-[#ffae83]" title="Moderate" />
            <div className="flex-1 bg-[#f97316]" title="Poor" />
            <div className="flex-1 bg-[#93000a]" title="Severe" />
            <div className="flex-1 bg-[#450a0a]" title="Hazardous" />
          </div>
          <div className="flex justify-between text-[10px] font-extrabold text-[#bbc9cd] uppercase tracking-tighter">
            <span>Good</span>
            <span>Moderate</span>
            <span>Severe</span>
          </div>
        </div>
      )}
    </div>
  );
}
