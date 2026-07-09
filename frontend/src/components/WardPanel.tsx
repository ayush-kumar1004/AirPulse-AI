import React from "react";

export interface WardPanelProps {
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
  loading: boolean;
}

const getCategoryColor = (category: string) => {
  switch (category?.toLowerCase()) {
    case "good":
      return "bg-[#4ae176]/10 text-[#4ae176] border-[#4ae176]/20";
    case "satisfactory":
      return "bg-[#22D3EE]/10 text-[#22D3EE] border-[#22D3EE]/20";
    case "moderate":
      return "bg-[#ffae83]/10 text-[#ffae83] border-[#ffae83]/20";
    case "poor":
      return "bg-[#f97316]/10 text-[#f97316] border-[#f97316]/20";
    case "severe":
      return "bg-[#93000a]/10 text-[#ffb4ab] border-[#93000a]/20";
    default:
      return "bg-slate-800 text-slate-400 border-slate-700";
  }
};

const WardPanelPresentational = ({
  wardId,
  aqiData,
  weatherData,
  recommendations,
  loading,
}: WardPanelProps) => {
  // Empty State
  if (!wardId) {
    return (
      <div className="bg-[#1E293B]/60 backdrop-blur-md rounded-xl p-6 border border-[#334155] text-center text-[#bbc9cd] h-fit">
        <p className="text-sm font-medium">Select a Delhi ward on the map to begin analysis.</p>
      </div>
    );
  }

  // Loading Skeleton
  if (loading || !aqiData) {
    return (
      <div className="bg-[#1E293B] rounded-xl p-6 border border-[#334155] space-y-6 animate-pulse">
        <div className="h-6 w-1/2 bg-slate-800 rounded" />
        <div className="flex gap-4 items-center">
          <div className="h-16 w-16 bg-slate-800 rounded-lg" />
          <div className="space-y-2 flex-1">
            <div className="h-4 w-1/3 bg-slate-800 rounded" />
            <div className="h-4 w-1/2 bg-slate-800 rounded" />
          </div>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div className="h-12 bg-slate-800 rounded" />
          <div className="h-12 bg-slate-800 rounded" />
          <div className="h-12 bg-slate-800 rounded" />
        </div>
        <div className="space-y-2">
          <div className="h-4 w-1/3 bg-slate-800 rounded" />
          <div className="h-12 bg-slate-800 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#1E293B] rounded-xl p-6 border border-[#334155] space-y-6 text-white font-sans">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#334155] pb-4">
        <div>
          <h3 className="text-lg font-bold uppercase tracking-wide text-white">
            {aqiData.ward_name}
          </h3>
          <p className="text-xs text-[#bbc9cd]/60">Ward ID: {aqiData.ward_id}</p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider border ${getCategoryColor(
            aqiData.category
          )}`}
        >
          {aqiData.category}
        </span>
      </div>

      {/* AQI Breakdown */}
      <div className="flex gap-6 items-center">
        <div className="text-center bg-[#0F172A] border border-[#334155] rounded-xl p-4 min-w-[90px] shadow-lg">
          <span className="text-[10px] font-bold text-[#94A3B8] block uppercase tracking-wider">
            AQI
          </span>
          <span className="text-3xl font-extrabold text-[#22D3EE]">
            {aqiData.aqi}
          </span>
        </div>

        <div className="grid grid-cols-3 gap-3 flex-1">
          <div className="text-center bg-[#0F172A]/50 rounded-lg p-2 border border-[#334155]/40">
            <span className="text-[10px] text-[#bbc9cd] block">PM2.5</span>
            <span className="text-sm font-semibold text-white">
              {aqiData.pm25 !== undefined ? `${aqiData.pm25} µg/m³` : "N/A"}
            </span>
          </div>
          <div className="text-center bg-[#0F172A]/50 rounded-lg p-2 border border-[#334155]/40">
            <span className="text-[10px] text-[#bbc9cd] block">PM10</span>
            <span className="text-sm font-semibold text-white">
              {aqiData.pm10 !== undefined ? `${aqiData.pm10} µg/m³` : "N/A"}
            </span>
          </div>
          <div className="text-center bg-[#0F172A]/50 rounded-lg p-2 border border-[#334155]/40">
            <span className="text-[10px] text-[#bbc9cd] block">NO₂</span>
            <span className="text-sm font-semibold text-white">
              {aqiData.no2 !== undefined ? `${aqiData.no2} µg/m³` : "N/A"}
            </span>
          </div>
        </div>
      </div>

      {/* Weather */}
      {weatherData && (
        <div className="bg-[#0F172A] rounded-xl p-4 border border-[#334155] space-y-3">
          <h4 className="text-[11px] font-bold text-[#bbc9cd] tracking-wider uppercase">
            Weather Conditions
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            <div>
              <span className="text-[#bbc9cd]/60 block">Temp</span>
              <span className="font-semibold">{weatherData.temp_c}°C</span>
            </div>
            <div>
              <span className="text-[#bbc9cd]/60 block">Humidity</span>
              <span className="font-semibold">{weatherData.humidity}%</span>
            </div>
            <div>
              <span className="text-[#bbc9cd]/60 block">Wind</span>
              <span className="font-semibold">
                {weatherData.wind_kph} kph ({weatherData.wind_dir})
              </span>
            </div>
            <div>
              <span className="text-[#bbc9cd]/60 block">Rain</span>
              <span className="font-semibold">{weatherData.rain_mm} mm</span>
            </div>
          </div>
        </div>
      )}

      {/* AI Recommendations */}
      {recommendations && recommendations.actions && (
        <div className="space-y-3">
          <h4 className="text-[11px] font-bold text-[#22D3EE] tracking-wider uppercase">
            AI Interventions
          </h4>
          <div className="space-y-2">
            {recommendations.actions.length === 0 ? (
              <p className="text-xs text-[#bbc9cd]/70 italic">No interventions recommended.</p>
            ) : (
              recommendations.actions.map((act, i) => (
                <div
                  key={i}
                  className="bg-[#0F172A]/50 border border-[#334155]/60 rounded-xl p-3 text-xs space-y-1"
                >
                  <div className="flex justify-between items-start gap-2">
                    <span className="font-semibold text-white">{act.action}</span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border ${
                        act.urgency === "high"
                          ? "bg-red-500/10 text-red-400 border-red-500/20"
                          : act.urgency === "medium"
                          ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                          : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                      }`}
                    >
                      {act.urgency}
                    </span>
                  </div>
                  <p className="text-[#bbc9cd]/70 text-[11px] leading-relaxed">
                    {act.reason}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export const WardPanel = React.memo(WardPanelPresentational);
export default WardPanel;
