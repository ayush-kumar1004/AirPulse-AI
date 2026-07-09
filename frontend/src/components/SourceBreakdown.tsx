import React from "react";
import { motion } from "framer-motion";

export interface SourceBreakdownProps {
  attributionData: {
    ward_id: string;
    traffic: number;
    construction: number;
    industry: number;
    dust: number;
    confidence: number;
    reasoning: string;
  } | null;
  loading: boolean;
}

const SourceBreakdownPresentational = ({ attributionData, loading }: SourceBreakdownProps) => {
  if (loading || !attributionData) {
    return (
      <div className="bg-[#1E293B] rounded-xl p-6 border border-[#334155] space-y-4 animate-pulse">
        <div className="h-4 w-1/3 bg-slate-800 rounded" />
        <div className="space-y-3">
          <div className="h-8 bg-slate-800 rounded" />
          <div className="h-8 bg-slate-800 rounded" />
          <div className="h-8 bg-slate-800 rounded" />
          <div className="h-8 bg-slate-800 rounded" />
        </div>
      </div>
    );
  }

  // Format percentage helper
  const toPercent = (val: number) => Math.round(val * 100);

  const sources = [
    { label: "Traffic Attribution", val: attributionData.traffic, color: "bg-[#22d3ee]", text: "text-[#22d3ee]" },
    { label: "Construction Dust", val: attributionData.construction, color: "bg-[#f97316]", text: "text-[#f97316]" },
    { label: "Industrial Operations", val: attributionData.industry, color: "bg-[#a855f7]", text: "text-[#a855f7]" },
    { label: "Road & Soil Dust", val: attributionData.dust, color: "bg-[#78350f]", text: "text-amber-700" },
  ];

  return (
    <div className="bg-[#1E293B] rounded-xl p-6 border border-[#334155] space-y-5 text-white font-sans">
      {/* Title + Confidence Score */}
      <div className="flex justify-between items-center border-b border-[#334155] pb-3">
        <h4 className="text-[11px] font-bold text-[#bbc9cd] tracking-wider uppercase">
          AI Source Attribution
        </h4>
        <div className="flex items-center gap-1.5 bg-[#0F172A] border border-[#334155] px-2 py-0.5 rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-[#22D3EE] animate-pulse" />
          <span className="text-[10px] text-[#94A3B8] font-bold">
            CONFIDENCE: {toPercent(attributionData.confidence)}%
          </span>
        </div>
      </div>

      {/* Stacked Progress Bars */}
      <div className="space-y-4">
        {sources.map((src, i) => {
          const percent = toPercent(src.val);
          return (
            <div key={i} className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold text-[#bbc9cd]">
                <span>{src.label}</span>
                <span className={src.text}>{percent}%</span>
              </div>
              <div className="h-2 w-full bg-[#0F172A] rounded-full overflow-hidden border border-[#334155]/20">
                <motion.div
                  className={`h-full ${src.color} rounded-full`}
                  initial={{ width: 0 }}
                  animate={{ width: `${percent}%` }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Model Reasoning */}
      {attributionData.reasoning && (
        <div className="bg-[#0F172A] border border-[#334155] rounded-xl p-4 text-xs leading-relaxed space-y-2">
          <span className="text-[10px] font-bold text-[#94A3B8] block uppercase tracking-wider">
            Model Explanation
          </span>
          <p className="text-[#bbc9cd]/85 font-light">
            {attributionData.reasoning}
          </p>
        </div>
      )}
    </div>
  );
};

export const SourceBreakdown = React.memo(SourceBreakdownPresentational);
export default SourceBreakdown;
