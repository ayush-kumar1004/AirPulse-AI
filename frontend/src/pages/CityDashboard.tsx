import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Sparkles, BellRing, TrendingUp } from "lucide-react";
import { getHeatmap } from "../api/client";

interface HeatmapItem {
  ward_id: string;
  ward_name: string;
  aqi: number;
  category: string;
}

export default function CityDashboard() {
  const [heatmapData, setHeatmapData] = useState<HeatmapItem[] | null>(null);

  // Fetch heatmap data from backend API
  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await getHeatmap();
        setHeatmapData(res);
      } catch (err) {
        console.error("Error loading dashboard heatmap:", err);
      }
    };
    loadData();
  }, []);

  // Mouse move handler for tracking glow
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    card.style.setProperty("--mouse-x", `${x}px`);
    card.style.setProperty("--mouse-y", `${y}px`);
  };

  // 1. Calculate City Average AQI (fallback to 196)
  const averageAqi = heatmapData && heatmapData.length > 0
    ? Math.round(heatmapData.reduce((sum, h) => sum + h.aqi, 0) / heatmapData.length)
    : 196;

  const getAqiCategory = (aqi: number) => {
    if (aqi <= 50) return { label: "GOOD", class: "bg-green-500/20 text-green-400 border-green-500/30" };
    if (aqi <= 100) return { label: "SATISFACTORY", class: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30" };
    if (aqi <= 150) return { label: "MODERATE", class: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" };
    if (aqi <= 200) return { label: "POOR", class: "bg-orange-500/20 text-orange-400 border-orange-500/30" };
    return { label: "SEVERE", class: "bg-red-900/40 text-red-400 border-red-500/30" };
  };

  const avgCategory = getAqiCategory(averageAqi);

  // 2. Worst Ward Details (fallback to Rohini · 241)
  const worstWard = heatmapData && heatmapData.length > 0
    ? [...heatmapData].sort((a, b) => b.aqi - a.aqi)[0]
    : null;

  const worstWardLabel = worstWard
    ? `${worstWard.ward_name} · ${worstWard.aqi}`
    : "Rohini · 241";
  
  const worstWardCategory = getAqiCategory(worstWard ? worstWard.aqi : 241);

  // 3. Best Ward Details (fallback to Vasant Kunj · 88)
  const bestWard = heatmapData && heatmapData.length > 0
    ? [...heatmapData].sort((a, b) => a.aqi - b.aqi)[0]
    : null;

  const bestWardLabel = bestWard
    ? `${bestWard.ward_name} · ${bestWard.aqi}`
    : "Vasant Kunj · 88";

  const bestWardCategory = getAqiCategory(bestWard ? bestWard.aqi : 88);

  // 4. Wards in Severe Zone (fallback to 6/24)
  const totalWardsCount = heatmapData ? heatmapData.length : 24;
  const severeWardsCount = heatmapData
    ? heatmapData.filter((h) => h.aqi > 200 || h.category?.toLowerCase() === "severe").length
    : 6;

  // Percentage for severe radial circle
  const severePercent = Math.round((severeWardsCount / totalWardsCount) * 100);
  const strokeDashArrayValue = `${severePercent}, 100`;

  return (
    <div className="flex-1 w-full h-full overflow-y-auto p-6 md:p-8 space-y-8 bg-[#0F172A] text-[#dae2fd] font-sans pb-24">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* KPI Grid Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* KPI 1: City Average AQI */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl flex flex-col justify-between border border-[#334155]/50 transition-all duration-300 relative overflow-hidden group hover:border-[#22d3ee] hover:shadow-[0_0_20px_rgba(34,211,238,0.1)] hover:-translate-y-0.5 bg-[#1E293B]/50 backdrop-blur-md"
            style={{
              background: "radial-gradient(800px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <span className="text-[11px] font-bold text-[#bbc9cd] tracking-widest uppercase">City Average AQI</span>
            <div className="flex items-baseline gap-3 mt-4">
              <span className="text-5xl font-extrabold text-white tracking-tight">{averageAqi}</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${avgCategory.class}`}>
                {avgCategory.label}
              </span>
            </div>
            <div className="flex items-center gap-1 mt-4">
              <TrendingUp className="w-4 h-4 text-orange-400" />
              <span className="text-xs text-[#bbc9cd]">+12 vs yesterday</span>
            </div>
          </div>

          {/* KPI 2: Worst Ward */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl flex flex-col justify-between border border-[#334155]/50 transition-all duration-300 relative overflow-hidden group hover:border-[#22d3ee] hover:shadow-[0_0_20px_rgba(34,211,238,0.1)] hover:-translate-y-0.5 bg-[#1E293B]/50 backdrop-blur-md"
            style={{
              background: "radial-gradient(800px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <span className="text-[11px] font-bold text-[#bbc9cd] tracking-widest uppercase">Worst Ward</span>
            <div className="mt-4">
              <div className="text-xl font-bold text-white tracking-tight">{worstWardLabel}</div>
              <span className={`inline-block mt-2 px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${worstWardCategory.class}`}>
                {worstWardCategory.label}
              </span>
            </div>
            <p className="text-xs text-[#bbc9cd] mt-4">Station #22B Active</p>
          </div>

          {/* KPI 3: Best Ward */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl flex flex-col justify-between border border-[#334155]/50 transition-all duration-300 relative overflow-hidden group hover:border-[#22d3ee] hover:shadow-[0_0_20px_rgba(34,211,238,0.1)] hover:-translate-y-0.5 bg-[#1E293B]/50 backdrop-blur-md"
            style={{
              background: "radial-gradient(800px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <span className="text-[11px] font-bold text-[#bbc9cd] tracking-widest uppercase">Best Ward</span>
            <div className="mt-4">
              <div className="text-xl font-bold text-white tracking-tight">{bestWardLabel}</div>
              <span className={`inline-block mt-2 px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${bestWardCategory.class}`}>
                {bestWardCategory.label}
              </span>
            </div>
            <p className="text-xs text-[#bbc9cd] mt-4">Residential Zone</p>
          </div>

          {/* KPI 4: Wards in Severe Zone */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl flex flex-col justify-between border border-[#334155]/50 transition-all duration-300 relative overflow-hidden group hover:border-[#22d3ee] hover:shadow-[0_0_20px_rgba(34,211,238,0.1)] hover:-translate-y-0.5 bg-[#1E293B]/50 backdrop-blur-md"
            style={{
              background: "radial-gradient(800px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <span className="text-[11px] font-bold text-[#bbc9cd] tracking-widest uppercase">Wards in Severe Zone</span>
            <div className="flex items-center justify-between mt-4">
              <span className="text-5xl font-extrabold text-white tracking-tight">
                {severeWardsCount}/{totalWardsCount}
              </span>
              <div className="relative w-12 h-12">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" fill="none" r="16" stroke="#334155" strokeWidth="3" />
                  <circle
                    cx="18"
                    cy="18"
                    fill="none"
                    r="16"
                    stroke="#ef4444"
                    strokeDasharray={strokeDashArrayValue}
                    strokeLinecap="round"
                    strokeWidth="3"
                  />
                </svg>
              </div>
            </div>
            <p className="text-xs text-red-400 font-medium mt-4">Critical Intervention Needed</p>
          </div>
        </div>

        {/* Main Analysis Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column (8 cols): Trend Chart Area */}
          <div
            onMouseMove={handleMouseMove}
            className="lg:col-span-8 p-6 rounded-xl border border-[#334155]/50 transition-all duration-300 relative overflow-hidden flex flex-col bg-[#1E293B]/50 backdrop-blur-md"
            style={{
              background: "radial-gradient(1000px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.06), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6">
              <div>
                <h3 className="text-xl font-bold text-white tracking-tight">City Trend — last 24h</h3>
                <p className="text-xs text-[#bbc9cd] mt-0.5">Averaged across all calibrated sensor points</p>
              </div>
              <div className="bg-[#22D3EE]/10 border border-[#22D3EE]/25 rounded-lg px-4 py-2 flex items-center gap-2 shadow-inner-cyan">
                <Sparkles className="w-4 h-4 text-[#22D3EE] animate-pulse" />
                <span className="text-xs font-semibold text-[#22D3EE]">
                  AI Insight: PM2.5 peak at 11:00 PM (Wind Shift)
                </span>
              </div>
            </div>

            {/* Custom SVG Trend Chart */}
            <div className="flex-1 w-full min-h-[300px] relative mt-6 flex items-end">
              <div className="absolute inset-0 bg-gradient-to-t from-[#22d3ee]/10 to-transparent rounded-b-xl" />
              <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 1000 300">
                {/* AQI Zone Guide Lines */}
                <line stroke="#334155" strokeDasharray="6 6" x1="0" x2="1000" y1="200" y2="200" />
                <text fill="#859397" fontSize="10" fontWeight="bold" x="10" y="192" className="uppercase tracking-wider">
                  100 Moderate
                </text>
                <line stroke="#334155" strokeDasharray="6 6" x1="0" x2="1000" y1="100" y2="100" />
                <text fill="#859397" fontSize="10" fontWeight="bold" x="10" y="92" className="uppercase tracking-wider">
                  200 Severe
                </text>

                {/* Trend line (Solid historical + Dotted forecast) */}
                <path d="M0,220 Q150,240 300,180 T600,200 T750,150" fill="none" stroke="#22d3ee" strokeWidth="3" />
                <path d="M750,150 Q850,120 1000,50" fill="none" stroke="#22d3ee" strokeDasharray="8 6" strokeWidth="3" />
              </svg>

              {/* Time markers */}
              <div className="absolute bottom-0 left-0 w-full flex justify-between px-2 text-[10px] text-[#bbc9cd] font-bold uppercase py-2.5 border-t border-[#3c494c]/20 bg-[#0F172A]/30">
                <span>09:00 AM</span>
                <span>03:00 PM</span>
                <span>09:00 PM</span>
                <span>03:00 AM</span>
                <span className="text-[#22D3EE]">Forecast +24h</span>
              </div>
            </div>
          </div>

          {/* Right Column (4 cols): Mini Heatmap */}
          <div
            onMouseMove={handleMouseMove}
            className="lg:col-span-4 p-6 rounded-xl border border-[#334155]/50 transition-all duration-300 relative overflow-hidden flex flex-col bg-[#1E293B]/50 backdrop-blur-md"
            style={{
              background: "radial-gradient(800px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-white tracking-tight">Mini Heat Map</h3>
              <Link to="/map" className="text-xs font-bold text-[#22D3EE] hover:underline transition-all tracking-wider uppercase">
                View full map →
              </Link>
            </div>

            <div className="flex-1 rounded-lg border border-[#3c494c]/40 relative group overflow-hidden bg-[#131b2e] min-h-[300px]">
              <div
                className="absolute inset-0 bg-cover bg-center transition-transform duration-700 group-hover:scale-110 opacity-30 mix-blend-luminosity"
                style={{
                  backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuBX9fFxEGypy7tkbE5H097mvQ5Zgnil7wjtDsqXDeWQwKhLDACVS_n08kR3jA8kd-rO1mQpflh1G1PO6gCvSoMJfpoEUV-oa8KagA58HqQ3AKj5rTsRF7bJaIkNIeiTlUNoNHPOHVHLVV1mleWGfDJxY0djJNGMsGWOI51y-ibOjP_aCyBozfEO4QMX_TA6arJpmOVferMU9IYp-OaQuZOSNrhoA9whh0LevF8SrV8pJkR8PvKEZnEwkm4BnmwsVm-Avy3gagzD_oR3')",
                }}
              />
              {/* Stylized Heat Overlays */}
              <div className="absolute top-1/4 left-1/3 w-28 h-28 bg-red-500/40 blur-2xl rounded-full animate-pulse"></div>
              <div className="absolute bottom-1/4 right-1/4 w-36 h-36 bg-orange-500/30 blur-2xl rounded-full"></div>
              <div className="absolute top-1/2 left-1/2 w-20 h-20 bg-[#4ae176]/30 blur-2xl rounded-full"></div>

              {/* Map HUD */}
              <div className="absolute bottom-3 left-3 right-3 bg-[#1E293B]/90 backdrop-blur-md p-3 rounded border border-[#3c494c]/40">
                <div className="flex items-center justify-between text-[10px] font-bold text-[#bbc9cd] tracking-wider uppercase">
                  <span>AQI 0</span>
                  <div className="flex-1 mx-2.5 h-1.5 rounded-full bg-gradient-to-r from-green-500 via-orange-500 to-red-600"></div>
                  <span>AQI 500</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Alerts Strip */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <BellRing className="w-5 h-5 text-[#22D3EE] animate-bounce" />
            <h4 className="text-[11px] font-bold text-[#bbc9cd] uppercase tracking-widest">Top Alerts</h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Alert 1 */}
            <div
              onMouseMove={handleMouseMove}
              className="p-4 rounded-xl border border-[#334155]/50 flex items-center gap-4 relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md border-left-3 border-l-[#ef4444]"
              style={{
                background: "radial-gradient(400px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
                borderLeftWidth: "3px",
              }}
            >
              <div className="w-1 h-12 bg-red-600 rounded-full" />
              <div className="flex-1">
                <p className="text-xs text-[#dae2fd] leading-relaxed font-light">
                  Rohini forecast to hit SEVERE in 18h
                </p>
                <span className="text-[9px] font-bold text-[#22D3EE] uppercase flex items-center gap-1 mt-1 tracking-wider">
                  <Sparkles className="w-3 h-3 text-[#22D3EE]" /> Predictive Alert
                </span>
              </div>
            </div>

            {/* Alert 2 */}
            <div
              onMouseMove={handleMouseMove}
              className="p-4 rounded-xl border border-[#334155]/50 flex items-center gap-4 relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md border-left-3 border-l-orange-500"
              style={{
                background: "radial-gradient(400px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
                borderLeftWidth: "3px",
              }}
            >
              <div className="w-1 h-12 bg-orange-500 rounded-full" />
              <div className="flex-1">
                <p className="text-xs text-[#dae2fd] leading-relaxed font-light">
                  Industrial zone particulate surge detected
                </p>
                <span className="text-[9px] font-bold text-[#22D3EE] uppercase flex items-center gap-1 mt-1 tracking-wider">
                  <Sparkles className="w-3 h-3 text-[#22D3EE]" /> Sensor Correction
                </span>
              </div>
            </div>

            {/* Alert 3 */}
            <div
              onMouseMove={handleMouseMove}
              className="p-4 rounded-xl border border-[#334155]/50 flex items-center gap-4 relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md border-left-3 border-l-amber-600"
              style={{
                background: "radial-gradient(400px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
                borderLeftWidth: "3px",
              }}
            >
              <div className="w-1 h-12 bg-amber-600 rounded-full" />
              <div className="flex-1">
                <p className="text-xs text-[#dae2fd] leading-relaxed font-light">
                  Sudden drop in wind speed over South Delhi
                </p>
                <span className="text-[9px] font-bold text-[#22D3EE] uppercase flex items-center gap-1 mt-1 tracking-wider">
                  <Sparkles className="w-3 h-3 text-[#22D3EE]" /> Weather Impact
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
