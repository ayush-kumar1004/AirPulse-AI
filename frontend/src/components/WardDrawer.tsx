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

// No fake fallback data lives here any more. When an endpoint fails we show "—"
// and an explicit "unavailable" label, so a broken backend looks broken instead of
// quietly rendering invented numbers (this component used to show Rohini's AQI of
// 241 for every ward whose data failed to load).
const DASH = "—";

const num = (val: number | null | undefined, digits = 0): string =>
  val === null || val === undefined || Number.isNaN(val) ? DASH : val.toFixed(digits);

const pct = (val: number | null | undefined): string =>
  val === null || val === undefined || Number.isNaN(val) ? DASH : `${Math.round(val * 100)}%`;

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

  // Real values only. Anything the API did not return stays null and renders as "—".
  const activeName = aqiData?.ward_name ?? wardId;
  const activeCategory = aqiData?.category ?? "Unavailable";
  const activeAqi = aqiData?.aqi ?? null;
  const activePm25 = aqiData?.pm25 ?? null;
  const activePm10 = aqiData?.pm10 ?? null;
  const activeNo2 = aqiData?.no2 ?? null;

  const activeTemp = weatherData?.temp_c ?? null;
  const activeHumidity = weatherData?.humidity ?? null;
  const activeWindKph = weatherData?.wind_kph ?? null;
  const activeWindDir = weatherData?.wind_dir ?? null;
  const activeRain = weatherData?.rain_mm ?? null;

  const activeConfidence = attributionData?.confidence ?? null;
  const activeTraffic = attributionData?.traffic ?? null;
  const activeConstruction = attributionData?.construction ?? null;
  const activeIndustry = attributionData?.industry ?? null;
  const activeDust = attributionData?.dust ?? null;

  const forecastPoints = forecastData?.points ?? [];
  const hasForecast = forecastPoints.length > 1;

  // Generate SVG path for the 24h forecast. Empty when there is nothing to plot.
  const svgPaths = useMemo(() => {
    const points = forecastPoints;
    if (points.length < 2) return { linePath: "", areaPath: "" };

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
  }, [forecastPoints]);

  // Sources breakdown array
  const sources = [
    { label: "Traffic", val: activeTraffic, color: "bg-[#22D3EE]" },
    { label: "Construction", val: activeConstruction, color: "bg-[#22D3EE]/60" },
    { label: "Industry", val: activeIndustry, color: "bg-[#22D3EE]/30" },
    { label: "Dust", val: activeDust, color: "bg-amber-700/50" },
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
              <span className="text-xs">Ward {wardId}</span>
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
          <span className="text-5xl font-extrabold text-[#22D3EE] tracking-tight">{num(activeAqi)}</span>
          <span className="text-[11px] font-semibold text-slate-400 tracking-wider uppercase">US AQI</span>
        </div>
        {!aqiData && (
          <p className="text-[11px] text-amber-400/90">
            Live air quality data could not be loaded for this ward.
          </p>
        )}
      </div>

      {/* Pollutant Grid */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-slate-800/50 p-2.5 rounded-lg border border-slate-700 text-center">
          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">PM2.5</p>
          <p className="text-base font-bold text-white mt-0.5">
            {num(activePm25, 1)}
          </p>
        </div>
        <div className="bg-slate-800/50 p-2.5 rounded-lg border border-slate-700 text-center">
          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">PM10</p>
          <p className="text-base font-bold text-white mt-0.5">
            {num(activePm10, 1)}
          </p>
        </div>
        <div className="bg-slate-800/50 p-2.5 rounded-lg border border-slate-700 text-center">
          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">NO2</p>
          <p className="text-base font-bold text-white mt-0.5">
            {num(activeNo2, 1)}
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
            <span className="font-semibold text-white">{num(activeTemp, 1)}°C</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400 text-[10px]">Humidity</span>
            <span className="font-semibold text-white">{num(activeHumidity)}%</span>
          </div>
          <div className="flex justify-between items-center col-span-2">
            <span className="text-slate-400 text-[10px]">Wind</span>
            <span className="font-semibold text-white">
              {num(activeWindKph, 1)} kph ({activeWindDir ?? DASH})
            </span>
          </div>
          <div className="flex justify-between items-center col-span-2">
            <span className="text-slate-400 text-[10px]">Precipitation</span>
            <span className="font-semibold text-white">{num(activeRain, 1)} mm</span>
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
          {attributionData
            ? attributionData.reasoning
            : "Source analysis is unavailable for this ward right now."}
        </p>

        {/* Source Breakdown bars */}
        <div className="space-y-2.5 pt-1.5 border-t border-[#22D3EE]/10">
          <div className="flex justify-between text-[10px] font-bold">
            <span className="text-slate-400">Pollutant Sources</span>
            <span className="text-[#22D3EE]">{pct(activeConfidence)} Confidence</span>
          </div>

          {/* Stacked indicator bar — stays empty when there is no attribution data */}
          <div className="flex h-2 rounded-full overflow-hidden bg-slate-800 border border-slate-700/50">
            {sources.map((src, i) => (
              <div
                key={i}
                className={src.color}
                style={{ width: `${Math.round((src.val ?? 0) * 100)}%` }}
              />
            ))}
          </div>

          {/* Legend tags with values */}
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {sources.map((src, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${src.color}`} />
                <span className="text-[10px] text-slate-400">
                  {src.label} {pct(src.val)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Forecast (24H Prediction) */}
      <div className="space-y-3">
        <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">24H Prediction</h3>
        {!hasForecast ? (
          <div className="h-24 w-full flex items-center justify-center rounded-lg border border-slate-700 bg-slate-800/40">
            <p className="text-[11px] text-slate-400">Forecast unavailable</p>
          </div>
        ) : (
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
        )}
      </div>

      {/* CTA Button */}
      <button className="mt-auto w-full bg-[#22D3EE] text-[#001f25] font-bold py-3 rounded-xl flex items-center justify-center gap-2 hover:brightness-110 active:scale-[0.98] transition-all shadow-[0_0_15px_rgba(34,211,238,0.2)]">
        <Bot className="w-4 h-4" />
        <span className="text-xs uppercase tracking-wider font-bold">Ask the AI about this ward</span>
      </button>
    </aside>
  );
}
