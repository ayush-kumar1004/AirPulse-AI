import React from "react";
import { motion } from "framer-motion";

export type OverlayMode = "current" | "predicted" | "source";

interface OverlayToggleProps {
  activeMode: OverlayMode;
  onChange: (mode: OverlayMode) => void;
}

export default function OverlayToggle({ activeMode, onChange }: OverlayToggleProps) {
  const modes: { id: OverlayMode; label: string }[] = [
    { id: "current", label: "Current AQI" },
    { id: "predicted", label: "Predicted +24h" },
    { id: "source", label: "Dominant Source" },
  ];

  return (
    <div className="flex bg-[#1E293B]/60 backdrop-blur-xl rounded-xl p-1 border border-[#334155] shadow-2xl relative z-10 w-fit">
      {modes.map((mode) => {
        const isActive = activeMode === mode.id;
        return (
          <button
            key={mode.id}
            onClick={() => onChange(mode.id)}
            className={`relative px-5 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-colors duration-200 focus:outline-none ${
              isActive ? "text-[#001f25] z-10" : "text-[#94A3B8] hover:text-white"
            }`}
          >
            {isActive && (
              <motion.div
                layoutId="activeOverlayTab"
                className="absolute inset-0 bg-[#22D3EE] rounded-lg shadow-lg -z-10"
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            )}
            {mode.label}
          </button>
        );
      })}
    </div>
  );
}
