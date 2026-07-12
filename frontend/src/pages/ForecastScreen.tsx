import React, { useState, useEffect } from "react";
import { Sparkles, MapPin, ChevronDown, Check, TrendingUp, TrendingDown, ArrowRight } from "lucide-react";
import { getPredict } from "../api/client";

interface ForecastDataPoint {
  timestamp: string;
  predicted_aqi: number;
  trend: string;
}

interface FallbackData {
  name: string;
  location: string;
  h24: number;
  h24Trend: "up" | "down";
  h48: number;
  h48Trend: "up" | "down";
  h72: number;
  h72Trend: "up" | "down";
  windVelocity: string;
  windVal: number;
  stubbleImpact: string;
  stubbleVal: number;
  humidity: number;
  primaryReason: string;
  recommendedPrep: string;
  pathConfidence: string;
  pathForecast: string;
  y24: number;
  y48: number;
  y72: number;
}

// Fallback datasets matching the Stitch design
const fallbackDatabase: Record<string, FallbackData> = {
  W02: {
    name: "Rohini",
    location: "Sector 16, Delhi NW",
    h24: 214,
    h24Trend: "up",
    h48: 268,
    h48Trend: "up",
    h72: 236,
    h72Trend: "down",
    windVelocity: "4 km/h (Low)",
    windVal: 15,
    stubbleImpact: "Moderate (12%)",
    stubbleVal: 35,
    humidity: 68,
    primaryReason: "Low wind speed combined with increased morning traffic is expected to push AQI into the Very Poor category.",
    recommendedPrep: "Increase public transport frequency and activate Stage II of GRAP.",
    pathConfidence: "M0,150 Q125,170 250,140 T500,180 T750,220 T1000,210 L1000,240 T750,250 T500,210 T250,170 T0,180 Z",
    pathForecast: "M0,165 Q125,185 250,155 T500,195 T750,235 T1000,225",
    y24: 155,
    y48: 195,
    y72: 235,
  },
  W03: {
    name: "Central",
    location: "Connaught Place, Delhi Central",
    h24: 156,
    h24Trend: "up",
    h48: 182,
    h48Trend: "up",
    h72: 145,
    h72Trend: "down",
    windVelocity: "6 km/h (Low)",
    windVal: 22,
    stubbleImpact: "Low (5%)",
    stubbleVal: 15,
    humidity: 55,
    primaryReason: "Continued commercial diesel transit trapping particulate matter in street canyons during commute hours.",
    recommendedPrep: "Restrict heavy freight vehicles during peak traffic hours and spray water in key avenues.",
    pathConfidence: "M0,130 Q125,150 250,120 T500,160 T750,200 T1000,190 L1000,220 T750,230 T500,190 T250,150 T0,160 Z",
    pathForecast: "M0,145 Q125,165 250,135 T500,175 T750,215 T1000,205",
    y24: 135,
    y48: 175,
    y72: 215,
  },
  W01: {
    name: "Dwarka",
    location: "Sector 10, Delhi SW",
    h24: 55,
    h24Trend: "up",
    h48: 62,
    h48Trend: "up",
    h72: 50,
    h72Trend: "down",
    windVelocity: "12 km/h (Moderate)",
    windVal: 45,
    stubbleImpact: "Low (2%)",
    stubbleVal: 8,
    humidity: 62,
    primaryReason: "Favorable wind velocities and low local traffic density promote good aerosol dispersion over open residential areas.",
    recommendedPrep: "Maintain routine watering of roads and green belt maintenance.",
    pathConfidence: "M0,60 Q125,80 250,50 T500,90 T750,130 T1000,120 L1000,150 T750,160 T500,120 T250,80 T0,90 Z",
    pathForecast: "M0,75 Q125,95 250,65 T500,105 T750,145 T1000,135",
    y24: 65,
    y48: 105,
    y72: 145,
  },
};

const getCategoryChipClass = (aqi: number) => {
  if (aqi <= 50) return "bg-green-500/10 text-green-400 border border-green-500/20";
  if (aqi <= 100) return "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20";
  if (aqi <= 150) return "bg-yellow-500/10 text-[#EAB308] border border-yellow-500/20";
  if (aqi <= 200) return "bg-orange-500/10 text-orange-400 border border-orange-500/20";
  return "bg-red-500/10 text-[#EF4444] border border-red-500/20";
};

const getCategoryLabel = (aqi: number) => {
  if (aqi <= 50) return "GOOD";
  if (aqi <= 100) return "MODERATE";
  if (aqi <= 150) return "UNHEALTHY (SENSITIVE)";
  if (aqi <= 200) return "POOR";
  return "VERY POOR";
};

export default function ForecastScreen() {
  const [selectedWardId, setSelectedWardId] = useState<string>("W02");
  const [selectedHorizon, setSelectedHorizon] = useState<number>(48);
  const [dropdownOpen, setDropdownOpen] = useState<boolean>(false);
  const [apiData, setApiData] = useState<ForecastDataPoint[] | null>(null);

  // Load predictions in the background
  useEffect(() => {
    const loadPredictions = async () => {
      try {
        const res = await getPredict(selectedWardId, selectedHorizon);
        if (res && res.points) {
          setApiData(res.points);
        }
      } catch (err) {
        console.error("Error loading forecast prediction details:", err);
      }
    };
    loadPredictions();
  }, [selectedWardId, selectedHorizon]);

  // Mouse move handler for tracking glow
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    card.style.setProperty("--mouse-x", `${x}px`);
    card.style.setProperty("--mouse-y", `${y}px`);
  };

  const fallback = fallbackDatabase[selectedWardId] || fallbackDatabase.W02;

  // Wards list for dropdown
  const wardsList = [
    { id: "W02", name: "Rohini" },
    { id: "W03", name: "Central" },
    { id: "W01", name: "Dwarka" },
  ];

  const activeWardName = wardsList.find((w) => w.id === selectedWardId)?.name || "Rohini";

  // Dynamic values based on backend API if available, otherwise fallbacks
  const val24 = apiData && apiData.length >= 24 ? apiData[23].predicted_aqi : fallback.h24;
  const val48 = apiData && apiData.length >= 48 ? apiData[47].predicted_aqi : fallback.h48;
  const val72 = apiData && apiData.length >= 72 ? apiData[71].predicted_aqi : fallback.h72;

  return (
    <div className="flex-1 w-full h-full overflow-y-auto p-6 md:p-8 space-y-8 bg-[#0F172A] text-[#dae2fd] font-sans pb-24">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Page Header Section */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">AQI Forecast</h1>
            <p className="text-sm text-[#bbc9cd] mt-1">Real-time predictive air quality modeling for New Delhi.</p>
          </div>

          {/* Ward Selector and Horizon Tabs */}
          <div className="flex items-center gap-4 bg-[#171f33] rounded-xl p-1.5 border border-[#3c494c]/40 shadow-lg relative z-20">
            {/* Ward Dropdown */}
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 px-4 py-2 bg-[#222a3d] rounded-lg text-white border border-[#3c494c]/40 hover:border-[#22D3EE]/50 transition-colors text-sm font-semibold"
              >
                <MapPin className="w-4 h-4 text-[#22D3EE]" />
                <span>{activeWardName}</span>
                <ChevronDown className="w-4 h-4 text-[#bbc9cd]" />
              </button>

              {dropdownOpen && (
                <div className="absolute top-full right-0 mt-2 w-40 bg-[#1E293B] border border-[#3c494c]/40 rounded-xl overflow-hidden shadow-2xl z-30">
                  {wardsList.map((ward) => (
                    <button
                      key={ward.id}
                      onClick={() => {
                        setSelectedWardId(ward.id);
                        setDropdownOpen(false);
                      }}
                      className="w-full px-4 py-2.5 text-left text-xs font-semibold hover:bg-[#22D3EE]/10 hover:text-white transition-colors flex items-center justify-between"
                    >
                      <span>{ward.name}</span>
                      {selectedWardId === ward.id && <Check className="w-3.5 h-3.5 text-[#22D3EE]" />}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Horizon Switcher tabs */}
            <div className="flex h-10 p-1 bg-[#2d3449] rounded-lg">
              {[24, 48, 72].map((hz) => {
                const isActive = selectedHorizon === hz;
                return (
                  <button
                    key={hz}
                    onClick={() => setSelectedHorizon(hz)}
                    className={`px-4 rounded-md text-xs font-bold uppercase tracking-wider transition-all duration-200 ${
                      isActive
                        ? "bg-[#22d3ee] text-[#001f25] shadow-lg shadow-[#22d3ee]/20"
                        : "text-[#bbc9cd] hover:text-white"
                    }`}
                  >
                    {hz}h
                  </button>
                );
              })}
            </div>
          </div>
        </header>

        {/* Forecast Chart Card */}
        <section
          onMouseMove={handleMouseMove}
          className="p-6 rounded-2xl border border-[#334155]/50 relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md"
          style={{
            background: "radial-gradient(1000px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.06), transparent 80%), rgba(30, 41, 59, 0.5)",
          }}
        >
          <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6 border-b border-[#3c494c]/30 pb-4">
            <div>
              <h3 className="text-xl font-bold text-white tracking-tight">Predictive AQI Trend</h3>
              <p className="text-xs text-[#bbc9cd] mt-0.5">Expected hourly particulate matter concentration (PM2.5)</p>
            </div>
            <div className="flex items-center gap-4 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#22d3ee] shadow-[0_0_8px_#22d3ee]" />
                Forecast
              </span>
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 border border-dashed border-[#bbc9cd]/60 rounded-sm" />
                Confidence Range
              </span>
            </div>
          </div>

          {/* SVG Line Chart */}
          <div className="h-[300px] w-full relative mt-6 flex items-end">
            <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 1000 300">
              {/* Danger Threshold Line at 300 AQI */}
              <line stroke="#7f1d1d" strokeDasharray="8 4" strokeWidth="1.5" x1="0" x2="1000" y1="60" y2="60" />
              <text fill="#ef4444" fontSize="10" fontWeight="bold" textAnchor="end" x="990" y="50" className="uppercase tracking-widest opacity-80">
                Danger Threshold (300 AQI)
              </text>

              {/* Confidence Shaded Area */}
              <path d={fallback.pathConfidence} fill="#22d3ee" fillOpacity="0.05" />

              {/* Line Gradients */}
              <defs>
                <linearGradient id="aqi-line-gradient" x1="0" x2="1" y1="0" y2="0">
                  <stop offset="0%" stopColor="#EAB308" />
                  <stop offset="30%" stopColor="#F97316" />
                  <stop offset="70%" stopColor="#EF4444" />
                  <stop offset="100%" stopColor="#7F1D1D" />
                </linearGradient>
              </defs>

              {/* Main Forecast Curve */}
              <path d={fallback.pathForecast} fill="none" stroke="url(#aqi-line-gradient)" strokeLinecap="round" strokeWidth="4" />

              {/* Point Markers */}
              <circle cx="250" cy={fallback.y24} fill="#F97316" r="6" />
              <circle cx="500" cy={fallback.y48} fill="#EF4444" r="6" />
              <circle cx="750" cy={fallback.y72} fill="#7F1D1D" r="6" />

              {/* Value labels */}
              <text fill="#F97316" fontSize="12" fontWeight="bold" textAnchor="middle" x="250" y={fallback.y24 - 15}>
                {val24} (+24h)
              </text>
              <text fill="#EF4444" fontSize="12" fontWeight="bold" textAnchor="middle" x="500" y={fallback.y48 - 15}>
                {val48} (+48h)
              </text>
              <text fill="#7F1D1D" fontSize="12" fontWeight="bold" textAnchor="middle" x="750" y={fallback.y72 - 15}>
                {val72} (+72h)
              </text>
            </svg>

            {/* Grid Overlay lines */}
            <div className="absolute inset-0 pointer-events-none flex justify-between items-end border-b border-[#3c494c]/20">
              <div className="h-full border-r border-[#3c494c]/10 w-0" />
              <div className="h-full border-r border-[#3c494c]/10 w-0" />
              <div className="h-full border-r border-[#3c494c]/10 w-0" />
              <div className="h-full border-r border-[#3c494c]/10 w-0" />
            </div>
          </div>
        </section>

        {/* Summary Horizon Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: +24h */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl border border-[#334155]/50 flex items-center justify-between transition-all duration-300 relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md hover:border-[#22D3EE]/30"
            style={{
              background: "radial-gradient(400px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <div className="space-y-1">
              <p className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">+24 Hours</p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-extrabold text-white tracking-tight">{val24}</span>
                <TrendingUp className="w-4 h-4 text-orange-400" />
              </div>
            </div>
            <div className="text-right">
              <span className={`px-3 py-1 rounded-full text-[10px] font-bold tracking-widest ${getCategoryChipClass(val24)}`}>
                {getCategoryLabel(val24)}
              </span>
              <p className="mt-2 text-[10px] font-bold text-orange-400 uppercase tracking-wide">Rising Trend</p>
            </div>
          </div>

          {/* Card 2: +48h (Active/Highlighted card in Stitch) */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl border border-[#22D3EE]/30 flex items-center justify-between bg-[#22D3EE]/5 relative overflow-hidden backdrop-blur-md"
            style={{
              background: "radial-gradient(400px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.12), transparent 80%), rgba(34, 211, 238, 0.05)",
            }}
          >
            <div className="space-y-1">
              <p className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">+48 Hours</p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-extrabold text-white tracking-tight">{val48}</span>
                <TrendingUp className="w-4 h-4 text-red-500 animate-pulse" />
              </div>
            </div>
            <div className="text-right">
              <span className={`px-3 py-1 rounded-full text-[10px] font-bold tracking-widest ${getCategoryChipClass(val48)}`}>
                {getCategoryLabel(val48)}
              </span>
              <p className="mt-2 text-[10px] font-bold text-[#EF4444] uppercase tracking-wide animate-pulse">Rising Trend</p>
            </div>
          </div>

          {/* Card 3: +72h */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl border border-[#334155]/50 flex items-center justify-between transition-all duration-300 relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md hover:border-[#22D3EE]/30"
            style={{
              background: "radial-gradient(400px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <div className="space-y-1">
              <p className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">+72 Hours</p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-extrabold text-white tracking-tight">{val72}</span>
                <TrendingDown className="w-4 h-4 text-cyan-400" />
              </div>
            </div>
            <div className="text-right">
              <span className={`px-3 py-1 rounded-full text-[10px] font-bold tracking-widest ${getCategoryChipClass(val72)}`}>
                {getCategoryLabel(val72)}
              </span>
              <p className="mt-2 text-[10px] font-bold text-[#22D3EE] uppercase tracking-wide">Falling Trend</p>
            </div>
          </div>
        </div>

        {/* AI Intelligence Panel */}
        <section
          onMouseMove={handleMouseMove}
          className="p-8 rounded-2xl border-l-4 border-l-[#22D3EE] border border-[#334155]/50 relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md shadow-inner-cyan"
          style={{
            background: "radial-gradient(1000px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
          }}
        >
          {/* Glowing AI Chip */}
          <div className="absolute top-4 right-4 z-10">
            <span className="flex items-center gap-1.5 px-3 py-1 bg-[#22D3EE]/10 rounded-full text-[10px] font-bold text-[#22D3EE] tracking-wide uppercase border border-[#22D3EE]/20 animate-pulse">
              <span className="w-1.5 h-1.5 bg-[#22D3EE] rounded-full"></span>
              AI Generated Insights
            </span>
          </div>

          <div className="flex flex-col md:flex-row gap-10 items-start">
            {/* Left Section: Reason & Recommendations */}
            <div className="flex-1 space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-[#22D3EE]/10 rounded-2xl flex items-center justify-center border border-[#22D3EE]/20">
                  <Sparkles className="w-7 h-7 text-[#22D3EE] animate-pulse" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white tracking-tight">AI Forecast Summary</h3>
                  <div className="flex items-center gap-2 mt-1">
                    {/* Confidence Bars */}
                    <div className="flex gap-0.5">
                      <div className="w-1 h-3 bg-[#22D3EE] rounded-full"></div>
                      <div className="w-1 h-3 bg-[#22D3EE] rounded-full"></div>
                      <div className="w-1 h-3 bg-[#22D3EE] rounded-full"></div>
                      <div className="w-1 h-3 bg-[#22D3EE]/20 rounded-full"></div>
                    </div>
                    <p className="text-xs font-bold text-[#22D3EE]">91% Confidence Rating</p>
                  </div>
                </div>
              </div>

              {/* Insight Quotes */}
              <div className="space-y-4">
                <div className="bg-[#1E293B]/40 p-5 rounded-xl border border-[#3c494c]/30">
                  <p className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider mb-2">PRIMARY REASON</p>
                  <p className="text-sm text-[#dae2fd] leading-relaxed italic font-light">
                    "{fallback.primaryReason}"
                  </p>
                </div>

                <div className="bg-[#1E293B]/40 p-5 rounded-xl border border-[#3c494c]/30">
                  <p className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider mb-2">RECOMMENDED PREPARATION</p>
                  <div className="flex items-center gap-3">
                    <span className="text-[#4ae176] font-bold text-lg">✓</span>
                    <p className="text-sm text-white font-semibold">
                      {fallback.recommendedPrep}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Section: Environmental Factors */}
            <div className="w-full md:w-1/3 flex flex-col gap-4">
              <div className="p-5 bg-[#1E293B]/20 rounded-xl border border-[#3c494c]/20 space-y-4">
                <p className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">ENVIRONMENTAL FACTORS</p>
                
                {/* Wind Velocity */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs font-medium">
                    <span>Wind Velocity</span>
                    <span className="font-bold text-[#EF4444]">{fallback.windVelocity}</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#0F172A] rounded-full overflow-hidden">
                    <div className="bg-[#EF4444] h-full" style={{ width: `${fallback.windVal}%` }} />
                  </div>
                </div>

                {/* Stubble Burning Impact */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs font-medium">
                    <span>Stubble Burning Impact</span>
                    <span className="font-bold text-[#F97316]">{fallback.stubbleImpact}</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#0F172A] rounded-full overflow-hidden">
                    <div className="bg-[#F97316] h-full" style={{ width: `${fallback.stubbleVal}%` }} />
                  </div>
                </div>

                {/* Humidity */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs font-medium">
                    <span>Humidity</span>
                    <span className="font-bold text-[#22D3EE]">{fallback.humidity}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#0F172A] rounded-full overflow-hidden">
                    <div className="bg-[#22D3EE] h-full" style={{ width: `${fallback.humidity}%` }} />
                  </div>
                </div>

              </div>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
