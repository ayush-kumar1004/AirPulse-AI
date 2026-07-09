import React, { useMemo } from "react";
import { MapPin, Sparkles, Bot, Sun } from "lucide-react";

interface WardDrawerProps {
  wardId: string | null;
  aqiData: {
    ward_id: string;
    ward_name: string;
    aqi: number;
    category: string;
    pm25?: number;
    pm10?: number;
    no2?: number;
    updated_at: string;
  } | null;
  weatherData: {
    temp_c: number;
    humidity: number;
    wind_kph: number;
    wind_dir: string;
    rain_mm: number;
  } | null;
  recommendations: {
    actions: { action: string; target: string; urgency: string; reason: string }[];
    inspection_priority: { site: string; ward_id: string; reason: string; priority: number }[];
  } | null;
  attributionData: {
    ward_id: string;
    traffic: number;
    construction: number;
    industry: number;
    dust: number;
    confidence: number;
    reasoning: string;
  } | null;
  forecastData: {
    ward_id: string;
    points: {
      timestamp: string;
      predicted_aqi: number;
      trend: string;
      lower?: number;
      upper?: number;
    }[];
  } | null;
  loading: boolean;
}

// Stitch design fallback database
const fallbackDatabase: Record<string, {
  name: string;
  location: string;
  aqi: number;
  category: string;
  pm25: number;
  pm10: number;
  no2: number;
  temp_c: number;
  humidity: number;
  wind_kph: number;
  wind_dir: string;
  rain_mm: number;
  traffic: number;
  construction: number;
  industry: number;
  dust: number;
  confidence: number;
  reasoning: string;
  forecastPoints: { timestamp: string; predicted_aqi: number; trend: string }[];
}> = {
  W01: {
    name: "Dwarka",
    location: "Sector 10, Delhi SW",
    aqi: 52,
    category: "Good",
    pm25: 12,
    pm10: 45,
    no2: 18,
    temp_c: 32.0,
    humidity: 62,
    wind_kph: 12.0,
    wind_dir: "E",
    rain_mm: 0.0,
    traffic: 0.30,
    construction: 0.20,
    industry: 0.10,
    dust: 0.40,
    confidence: 0.91,
    reasoning: "Open residential layouts, active green spaces, and low density of heavy industrial units maintain stable particulate dispersion.",
    forecastPoints: [
      { timestamp: "Now", predicted_aqi: 52, trend: "stable" },
      { timestamp: "+4h", predicted_aqi: 55, trend: "stable" },
      { timestamp: "+8h", predicted_aqi: 58, trend: "stable" },
      { timestamp: "+12h", predicted_aqi: 50, trend: "stable" },
      { timestamp: "+16h", predicted_aqi: 48, trend: "stable" },
      { timestamp: "+20h", predicted_aqi: 52, trend: "stable" },
      { timestamp: "+24h", predicted_aqi: 54, trend: "stable" },
    ]
  },
  W02: {
    name: "Rohini",
    location: "Sector 16, Delhi NW",
    aqi: 241,
    category: "Severe",
    pm25: 145,
    pm10: 320,
    no2: 44,
    temp_c: 34.2,
    humidity: 41,
    wind_kph: 8.0,
    wind_dir: "NW",
    rain_mm: 0.0,
    traffic: 0.45,
    construction: 0.25,
    industry: 0.20,
    dust: 0.10,
    confidence: 0.78,
    reasoning: "The current spike is driven by stagnant air trapping localized vehicular emissions, combined with bypass exhaust from neighboring freight corridors.",
    forecastPoints: [
      { timestamp: "Now", predicted_aqi: 241, trend: "up" },
      { timestamp: "+4h", predicted_aqi: 248, trend: "up" },
      { timestamp: "+8h", predicted_aqi: 255, trend: "up" },
      { timestamp: "+12h", predicted_aqi: 230, trend: "down" },
      { timestamp: "+16h", predicted_aqi: 210, trend: "down" },
      { timestamp: "+20h", predicted_aqi: 228, trend: "up" },
      { timestamp: "+24h", predicted_aqi: 241, trend: "stable" },
    ]
  },
  W03: {
    name: "Central",
    location: "Connaught Place, Delhi Central",
    aqi: 156,
    category: "Moderate",
    pm25: 68,
    pm10: 150,
    no2: 30,
    temp_c: 33.5,
    humidity: 45,
    wind_kph: 10.0,
    wind_dir: "W",
    rain_mm: 0.0,
    traffic: 0.60,
    construction: 0.15,
    industry: 0.10,
    dust: 0.15,
    confidence: 0.82,
    reasoning: "High commercial vehicular transit and street canyons trap tailpipe NO2 and diesel particulates during transit hours.",
    forecastPoints: [
      { timestamp: "Now", predicted_aqi: 156, trend: "stable" },
      { timestamp: "+4h", predicted_aqi: 165, trend: "up" },
      { timestamp: "+8h", predicted_aqi: 172, trend: "up" },
      { timestamp: "+12h", predicted_aqi: 148, trend: "down" },
      { timestamp: "+16h", predicted_aqi: 135, trend: "down" },
      { timestamp: "+20h", predicted_aqi: 149, trend: "up" },
      { timestamp: "+24h", predicted_aqi: 156, trend: "stable" },
    ]
  },
  W04: {
    name: "North Delhi",
    location: "Model Town, Delhi North",
    aqi: 88,
    category: "Moderate",
    pm25: 28,
    pm10: 85,
    no2: 22,
    temp_c: 31.8,
    humidity: 50,
    wind_kph: 9.0,
    wind_dir: "N",
    rain_mm: 0.0,
    traffic: 0.35,
    construction: 0.15,
    industry: 0.30,
    dust: 0.20,
    confidence: 0.85,
    reasoning: "Industrial emissions from northern peripheral clusters show mild transport effects under light northerly surface winds.",
    forecastPoints: [
      { timestamp: "Now", predicted_aqi: 88, trend: "stable" },
      { timestamp: "+4h", predicted_aqi: 92, trend: "up" },
      { timestamp: "+8h", predicted_aqi: 95, trend: "up" },
      { timestamp: "+12h", predicted_aqi: 84, trend: "down" },
      { timestamp: "+16h", predicted_aqi: 80, trend: "down" },
      { timestamp: "+20h", predicted_aqi: 86, trend: "up" },
      { timestamp: "+24h", predicted_aqi: 88, trend: "stable" },
    ]
  },
  W05: {
    name: "East Delhi",
    location: "Laxmi Nagar, Delhi East",
    aqi: 182,
    category: "Poor",
    pm25: 98,
    pm10: 210,
    no2: 38,
    temp_c: 34.0,
    humidity: 43,
    wind_kph: 7.0,
    wind_dir: "NW",
    rain_mm: 0.0,
    traffic: 0.40,
    construction: 0.35,
    industry: 0.10,
    dust: 0.15,
    confidence: 0.80,
    reasoning: "High residential density, street paving dust resuspension, and nearby highway infrastructure fuel localized fine particulate matter.",
    forecastPoints: [
      { timestamp: "Now", predicted_aqi: 182, trend: "up" },
      { timestamp: "+4h", predicted_aqi: 190, trend: "up" },
      { timestamp: "+8h", predicted_aqi: 195, trend: "up" },
      { timestamp: "+12h", predicted_aqi: 170, trend: "down" },
      { timestamp: "+16h", predicted_aqi: 162, trend: "down" },
      { timestamp: "+20h", predicted_aqi: 175, trend: "up" },
      { timestamp: "+24h", predicted_aqi: 182, trend: "stable" },
    ]
  },
  W06: {
    name: "South Delhi",
    location: "Greater Kailash, Delhi South",
    aqi: 110,
    category: "Moderate",
    pm25: 38,
    pm10: 112,
    no2: 24,
    temp_c: 32.5,
    humidity: 55,
    wind_kph: 11.0,
    wind_dir: "S",
    rain_mm: 0.0,
    traffic: 0.45,
    construction: 0.15,
    industry: 0.05,
    dust: 0.35,
    confidence: 0.88,
    reasoning: "Road dust resuspension and high private vehicle use drive moderate daytime PM10 concentration spikes during commute periods.",
    forecastPoints: [
      { timestamp: "Now", predicted_aqi: 110, trend: "stable" },
      { timestamp: "+4h", predicted_aqi: 115, trend: "up" },
      { timestamp: "+8h", predicted_aqi: 120, trend: "up" },
      { timestamp: "+12h", predicted_aqi: 105, trend: "down" },
      { timestamp: "+16h", predicted_aqi: 98, trend: "down" },
      { timestamp: "+20h", predicted_aqi: 108, trend: "up" },
      { timestamp: "+24h", predicted_aqi: 110, trend: "stable" },
    ]
  }
};

const getCategoryBadgeClass = (category: string) => {
  switch (category?.toLowerCase()) {
    case "good":
      return "bg-[#22C55E]/20 text-[#22C55E] border-[#22C55E]/30";
    case "satisfactory":
      return "bg-[#22D3EE]/20 text-[#22D3EE] border-[#22D3EE]/30";
    case "moderate":
      return "bg-[#EAB308]/20 text-[#EAB308] border-[#EAB308]/30";
    case "poor":
      return "bg-[#F97316]/20 text-[#F97316] border-[#F97316]/30";
    case "severe":
    case "hazardous":
      return "bg-[#7F1D1D] text-white border-[#7F1D1D]/50";
    default:
      return "bg-slate-800 text-slate-400 border-slate-700";
  }
};

export default function WardDrawer({
  wardId,
  aqiData,
  weatherData,
  attributionData,
  forecastData,
}: WardDrawerProps) {
  // Empty State
  if (!wardId) {
    return (
      <aside className="w-full h-full bg-[#1E293B]/60 backdrop-blur-md rounded-2xl p-6 border border-[#334155] text-center text-[#bbc9cd] min-h-[400px] flex items-center justify-center">
        <p className="text-sm font-medium">Select a Delhi ward on the map to begin analysis.</p>
      </aside>
    );
  }

  // Retrieve fallback values
  const fallback = fallbackDatabase[wardId] || fallbackDatabase.W02;

  // Merge values: API responses overrides Fallbacks
  const activeName = aqiData ? aqiData.ward_name : fallback.name;
  const activeLocation = fallback.location;
  const activeCategory = aqiData ? aqiData.category : fallback.category;
  const activeAqi = aqiData ? aqiData.aqi : fallback.aqi;
  const activePm25 = aqiData && aqiData.pm25 !== undefined ? aqiData.pm25 : fallback.pm25;
  const activePm10 = aqiData && aqiData.pm10 !== undefined ? aqiData.pm10 : fallback.pm10;
  const activeNo2 = aqiData && aqiData.no2 !== undefined ? aqiData.no2 : fallback.no2;

  const activeTemp = weatherData ? weatherData.temp_c : fallback.temp_c;
  const activeHumidity = weatherData ? weatherData.humidity : fallback.humidity;
  const activeWindKph = weatherData ? weatherData.wind_kph : fallback.wind_kph;
  const activeWindDir = weatherData ? weatherData.wind_dir : fallback.wind_dir;
  const activeRain = weatherData ? weatherData.rain_mm : fallback.rain_mm;

  const activeReasoning = attributionData ? attributionData.reasoning : fallback.reasoning;
  const activeConfidence = attributionData ? attributionData.confidence : fallback.confidence;
  const activeTraffic = attributionData ? attributionData.traffic : fallback.traffic;
  const activeConstruction = attributionData ? attributionData.construction : fallback.construction;
  const activeIndustry = attributionData ? attributionData.industry : fallback.industry;
  const activeDust = attributionData ? attributionData.dust : fallback.dust;

  // Format percentages helper
  const toPercent = (val: number) => Math.round(val * 100);

  // Generate SVG path for 24h forecast dynamically
  const svgPaths = useMemo(() => {
    const points = forecastData && forecastData.points && forecastData.points.length > 0 
      ? forecastData.points 
      : fallback.forecastPoints;

    const width = 200;
    const height = 80;
    // Map points to fit SVG box
    const mappedAqiValues = points.map((p: any) => p.predicted_aqi ?? p.aqi);
    const minAQI = Math.min(...mappedAqiValues);
    const maxAQI = Math.max(...mappedAqiValues);
    const range = maxAQI - minAQI || 1;

    const coords = points.map((p: any, index: number) => {
      const x = (index / (points.length - 1)) * width;
      const aqiValue = p.predicted_aqi ?? p.aqi;
      const y = height - 12 - ((aqiValue - minAQI) / range) * (height - 24);
      return { x, y };
    });

    const linePath = coords
      .map((c, i) => `${i === 0 ? "M" : "L"}${c.x.toFixed(1)},${c.y.toFixed(1)}`)
      .join(" ");

    const areaPath = `${linePath} L${width},${height} L0,${height} Z`;

    return { linePath, areaPath };
  }, [forecastData, fallback]);

  // Sources breakdown array
  const sources = [
    { label: "Traffic", val: toPercent(activeTraffic), color: "bg-[#22D3EE]" },
    { label: "Construction", val: toPercent(activeConstruction), color: "bg-[#22D3EE]/60" },
    { label: "Industry", val: toPercent(activeIndustry), color: "bg-[#22D3EE]/30" },
    { label: "Dust", val: toPercent(activeDust), color: "bg-amber-700/50" },
  ];

  return (
    <aside className="w-full h-full bg-[#1E293B] border border-[#334155] rounded-2xl overflow-y-auto p-6 flex flex-col gap-6 text-white font-sans">
      {/* Header Section */}
      <div className="space-y-2">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-white tracking-tight">{activeName}</h2>
            <div className="flex items-center gap-1 text-slate-400 mt-0.5">
              <MapPin className="w-3.5 h-3.5" />
              <span className="text-xs">{activeLocation}</span>
            </div>
          </div>
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${getCategoryBadgeClass(
              activeCategory
            )}`}
          >
            {activeCategory}
          </span>
        </div>

        <div className="flex items-baseline gap-2 mt-4">
          <span className="text-5xl font-extrabold text-[#22D3EE] tracking-tight">{activeAqi}</span>
          <span className="text-[11px] font-semibold text-slate-400 tracking-wider uppercase">US AQI</span>
        </div>
      </div>

      {/* Pollutant Grid */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-slate-800/50 p-2.5 rounded-lg border border-slate-700 text-center">
          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">PM2.5</p>
          <p className="text-base font-bold text-white mt-0.5">
            {activePm25}
          </p>
        </div>
        <div className="bg-slate-800/50 p-2.5 rounded-lg border border-slate-700 text-center">
          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">PM10</p>
          <p className="text-base font-bold text-white mt-0.5">
            {activePm10}
          </p>
        </div>
        <div className="bg-slate-800/50 p-2.5 rounded-lg border border-slate-700 text-center">
          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">NO2</p>
          <p className="text-base font-bold text-white mt-0.5">
            {activeNo2}
          </p>
        </div>
      </div>

      {/* Weather Conditions */}
      <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700 space-y-2.5">
        <div className="flex items-center gap-2 text-slate-400 border-b border-slate-700 pb-1.5">
          <Sun className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-[10px] font-bold uppercase tracking-wider">Weather Conditions</span>
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
          <div className="flex justify-between items-center">
            <span className="text-slate-400 text-[10px]">Temperature</span>
            <span className="font-semibold text-white">{activeTemp}°C</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400 text-[10px]">Humidity</span>
            <span className="font-semibold text-white">{activeHumidity}%</span>
          </div>
          <div className="flex justify-between items-center col-span-2">
            <span className="text-slate-400 text-[10px]">Wind</span>
            <span className="font-semibold text-white">
              {activeWindKph} kph ({activeWindDir})
            </span>
          </div>
          <div className="flex justify-between items-center col-span-2">
            <span className="text-slate-400 text-[10px]">Precipitation</span>
            <span className="font-semibold text-white">{activeRain} mm</span>
          </div>
        </div>
      </div>

      {/* AI Analysis & Source Attribution */}
      <div className="bg-[#22D3EE]/5 border border-[#22D3EE]/20 rounded-xl p-4 space-y-3.5">
        {/* AI Header */}
        <div className="flex items-center gap-2 text-[#22D3EE]">
          <Sparkles className="w-4 h-4" />
          <span className="text-[11px] font-bold uppercase tracking-wider">AI Source Analysis</span>
        </div>

        {/* Reasoning */}
        <p className="text-xs text-slate-400 leading-relaxed font-light">
          {activeReasoning}
        </p>

        {/* Source Breakdown bars */}
        <div className="space-y-2.5 pt-1.5 border-t border-[#22D3EE]/10">
          <div className="flex justify-between text-[10px] font-bold">
            <span className="text-slate-400">Pollutant Sources</span>
            <span className="text-[#22D3EE]">{toPercent(activeConfidence)}% Confidence</span>
          </div>

          {/* Stacked indicator bar */}
          <div className="flex h-2 rounded-full overflow-hidden bg-slate-800 border border-slate-700/50">
            <div className="bg-[#22D3EE]" style={{ width: `${toPercent(activeTraffic)}%` }} />
            <div className="bg-[#22D3EE]/60" style={{ width: `${toPercent(activeConstruction)}%` }} />
            <div className="bg-[#22D3EE]/30" style={{ width: `${toPercent(activeIndustry)}%` }} />
            <div className="bg-amber-700/50" style={{ width: `${toPercent(activeDust)}%` }} />
          </div>

          {/* Legend tags with values */}
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {sources.map((src, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${src.color}`} />
                <span className="text-[10px] text-slate-400">
                  {src.label} {src.val}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Forecast (24H Prediction) */}
      <div className="space-y-3">
        <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">24H Prediction</h3>
        <div className="h-24 w-full relative">
          <svg className="w-full h-full" viewBox="0 0 200 80">
            <path d={svgPaths.linePath} fill="none" stroke="#22D3EE" strokeWidth="2" />
            <path d={svgPaths.areaPath} fill="url(#grad)" opacity="0.2" />
            <defs>
              <linearGradient id="grad" x1="0%" x2="0%" y1="0%" y2="100%">
                <stop offset="0%" style={{ stopColor: "#22D3EE", stopOpacity: 1 }} />
                <stop offset="100%" style={{ stopColor: "#22D3EE", stopOpacity: 0 }} />
              </linearGradient>
            </defs>
          </svg>
          <div className="flex justify-between text-[10px] text-slate-400 mt-1.5">
            <span>Now</span>
            <span>+12h</span>
            <span>+24h</span>
          </div>
        </div>
      </div>

      {/* CTA Button */}
      <button className="mt-auto w-full bg-[#22D3EE] text-[#001f25] font-bold py-3 rounded-xl flex items-center justify-center gap-2 hover:brightness-110 active:scale-[0.98] transition-all shadow-[0_0_15px_rgba(34,211,238,0.2)]">
        <Bot className="w-4 h-4" />
        <span className="text-xs uppercase tracking-wider font-bold">Ask the AI about this ward</span>
      </button>
    </aside>
  );
}
