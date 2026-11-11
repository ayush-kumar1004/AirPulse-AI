import React, { useState, useEffect, useMemo } from "react";
import {
  Sparkles,
  MapPin,
  ChevronDown,
  Check,
  TrendingUp,
  TrendingDown,
  Wind,
  Droplets,
  Thermometer,
  CloudRain,
  ShieldAlert,
} from "lucide-react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from "recharts";
import { getPredict, getWards, getWeather } from "../api/client";

interface ForecastPoint {
  timestamp: string;
  predicted_aqi: number;
  trend: string;
  lower?: number;
  upper?: number;
}

interface FeatureImportanceDriver {
  feature: string;
  importance: number;
  description: string;
}

interface ForecastApiResponse {
  ward_id: string;
  horizon_hours: number;
  points: ForecastPoint[];
  model: string;
  top_features: FeatureImportanceDriver[];
  summary_reason?: string;
}

interface WeatherApiResponse {
  temperature?: number;
  humidity?: number;
  wind_speed?: number;
  wind_direction?: number;
  precipitation?: number;
}

const getCategoryChipClass = (aqi: number) => {
  if (aqi <= 50) return "bg-green-500/10 text-green-400 border border-green-500/20";
  if (aqi <= 100) return "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20";
  if (aqi <= 200) return "bg-yellow-500/10 text-[#EAB308] border border-yellow-500/20";
  if (aqi <= 300) return "bg-orange-500/10 text-orange-400 border border-orange-500/20";
  return "bg-red-500/10 text-[#EF4444] border border-red-500/20";
};

const getCategoryLabel = (aqi: number) => {
  if (aqi <= 50) return "GOOD";
  if (aqi <= 100) return "SATISFACTORY";
  if (aqi <= 200) return "MODERATE";
  if (aqi <= 300) return "POOR";
  return "SEVERE";
};

export default function ForecastScreen() {
  const [selectedWardId, setSelectedWardId] = useState<string>("");
  const [wardsList, setWardsList] = useState<{ id: string; name: string }[]>([]);
  const [selectedHorizon, setSelectedHorizon] = useState<number>(48);
  const [dropdownOpen, setDropdownOpen] = useState<boolean>(false);
  const [forecastData, setForecastData] = useState<ForecastApiResponse | null>(null);
  const [weatherData, setWeatherData] = useState<WeatherApiResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Load Delhi wards on mount
  useEffect(() => {
    const loadWards = async () => {
      try {
        const res = await getWards();
        const wards = (res?.features ?? []).map((f: any) => ({
          id: f.properties?.ward_id,
          name: f.properties?.ward_name ?? f.properties?.ward_id,
        }));
        setWardsList(wards);
        if (wards.length > 0) {
          setSelectedWardId((current) => current || wards[0].id);
        }
      } catch (err) {
        console.error("Error loading ward list:", err);
      }
    };
    loadWards();
  }, []);

  // Fetch real forecast and live weather whenever ward or horizon changes
  useEffect(() => {
    if (!selectedWardId) return;

    let isMounted = true;
    const loadData = async () => {
      setLoading(true);
      try {
        const [predictRes, weatherRes] = await Promise.allSettled([
          getPredict(selectedWardId, selectedHorizon),
          getWeather(selectedWardId),
        ]);

        if (isMounted) {
          if (predictRes.status === "fulfilled" && predictRes.value) {
            setForecastData(predictRes.value);
          }
          if (weatherRes.status === "fulfilled" && weatherRes.value) {
            setWeatherData(weatherRes.value);
          }
        }
      } catch (err) {
        console.error("Error fetching forecast:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadData();
    return () => {
      isMounted = false;
    };
  }, [selectedWardId, selectedHorizon]);

  // Card mouse tracking glow
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    card.style.setProperty("--mouse-x", `${x}px`);
    card.style.setProperty("--mouse-y", `${y}px`);
  };

  const activeWardName =
    wardsList.find((w) => w.id === selectedWardId)?.name || "Loading Ward…";

  const points = forecastData?.points ?? [];

  // Dynamic values at +24h, +48h, and +72h directly from the real prediction array
  const point24 = points.length >= 24 ? points[23] : points[points.length - 1];
  const point48 = points.length >= 48 ? points[47] : points[points.length - 1];
  const point72 = points.length >= 72 ? points[71] : points[points.length - 1];

  const val24 = point24?.predicted_aqi ?? 0;
  const val48 = point48?.predicted_aqi ?? 0;
  const val72 = point72?.predicted_aqi ?? 0;

  // Format Recharts data series from API response
  const chartData = useMemo(() => {
    if (!points.length) return [];
    return points.map((p) => {
      const date = new Date(p.timestamp);
      const timeStr = date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      });
      const dayStr = date.toLocaleDateString([], { weekday: "short" });
      return {
        time: `${dayStr} ${timeStr}`,
        aqi: p.predicted_aqi,
        lower: p.lower ?? Math.max(10, p.predicted_aqi - 20),
        upper: p.upper ?? p.predicted_aqi + 20,
        trend: p.trend,
      };
    });
  }, [points]);

  const topDrivers = forecastData?.top_features ?? [];
  const modelName = forecastData?.model ?? "LightGBM Regressor (Tabular)";
  const summaryReason =
    forecastData?.summary_reason ||
    "Tabular forecasting model synthesizes autoregressive lags with projected temperature, humidity, and wind vectors.";

  return (
    <div className="flex-1 w-full h-full overflow-y-auto p-6 md:p-8 space-y-8 bg-[#0F172A] text-[#dae2fd] font-sans pb-24">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Page Header Section */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-extrabold text-white tracking-tight">AQI Forecast</h1>
              <span className="px-3 py-1 bg-[#22D3EE]/10 border border-[#22D3EE]/30 rounded-full text-[10px] font-bold text-[#22D3EE] uppercase tracking-wider">
                {modelName}
              </span>
            </div>
            <p className="text-sm text-[#bbc9cd] mt-1">
              Multi-step machine learning forecast driven by real weather predictions and lag dynamics.
            </p>
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
                <span className="max-w-[140px] truncate">{activeWardName}</span>
                <ChevronDown className="w-4 h-4 text-[#bbc9cd]" />
              </button>

              {dropdownOpen && (
                <div className="absolute top-full right-0 mt-2 w-56 max-h-72 overflow-y-auto bg-[#1E293B] border border-[#3c494c]/40 rounded-xl overflow-hidden shadow-2xl z-30 custom-scrollbar">
                  {wardsList.map((ward) => (
                    <button
                      key={ward.id}
                      onClick={() => {
                        setSelectedWardId(ward.id);
                        setDropdownOpen(false);
                      }}
                      className="w-full px-4 py-2.5 text-left text-xs font-semibold hover:bg-[#22D3EE]/10 hover:text-white transition-colors flex items-center justify-between border-b border-[#3c494c]/20"
                    >
                      <span className="truncate pr-2">{ward.name}</span>
                      {selectedWardId === ward.id && (
                        <Check className="w-3.5 h-3.5 text-[#22D3EE] flex-shrink-0" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Horizon Switcher Tabs */}
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

        {/* Dynamic Forecast Chart Card */}
        <section
          onMouseMove={handleMouseMove}
          className="p-6 rounded-2xl border border-[#334155]/50 relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md"
          style={{
            background:
              "radial-gradient(1000px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.06), transparent 80%), rgba(30, 41, 59, 0.5)",
          }}
        >
          <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-4 border-b border-[#3c494c]/30 pb-4">
            <div>
              <h3 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Predictive AQI Trend (+{selectedHorizon}h)
                {loading && (
                  <span className="w-2 h-2 rounded-full bg-[#22D3EE] animate-ping" />
                )}
              </h3>
              <p className="text-xs text-[#bbc9cd] mt-0.5">
                Hourly multi-step prediction with empirical 95% confidence intervals and weather dynamics
              </p>
            </div>
            <div className="flex items-center gap-4 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider flex-wrap">
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#22d3ee] shadow-[0_0_8px_#22d3ee]" />
                LightGBM Predicted AQI
              </span>
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 bg-[#22d3ee]/20 border border-dashed border-[#22d3ee] rounded" />
                Confidence Band
              </span>
              <span className="flex items-center gap-2 text-red-400">
                <span className="w-3 h-0.5 bg-red-500" />
                Danger Threshold (300 AQI)
              </span>
            </div>
          </div>

          {/* Dynamic Recharts Chart */}
          <div className="h-[340px] w-full relative mt-4">
            {loading && !chartData.length ? (
              <div className="h-full w-full flex flex-col items-center justify-center gap-3 bg-[#0F172A]/40 rounded-xl">
                <div className="w-8 h-8 border-2 border-[#22D3EE] border-t-transparent rounded-full animate-spin" />
                <p className="text-xs text-[#bbc9cd] uppercase font-bold tracking-widest">
                  Computing LightGBM Forecast…
                </p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 15, right: 20, left: -10, bottom: 25 }}>
                  <defs>
                    <linearGradient id="confidenceBand" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22D3EE" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#22D3EE" stopOpacity={0.02} />
                    </linearGradient>
                    <linearGradient id="aqiLineGradient" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#22D3EE" />
                      <stop offset="50%" stopColor="#38BDF8" />
                      <stop offset="100%" stopColor="#818CF8" />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                  <XAxis
                    dataKey="time"
                    stroke="#94A3B8"
                    fontSize={11}
                    tickLine={false}
                    interval={Math.max(1, Math.floor(chartData.length / 8))}
                    angle={-20}
                    textAnchor="end"
                  />
                  <YAxis
                    stroke="#94A3B8"
                    fontSize={11}
                    tickLine={false}
                    domain={[0, (dataMax: number) => Math.max(350, Math.ceil(dataMax * 1.15))]}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0F172A",
                      borderColor: "#334155",
                      borderRadius: "12px",
                      color: "#F8FAFC",
                      fontSize: "12px",
                      boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
                    }}
                    formatter={(value: any, name: string) => {
                      if (name === "aqi") return [value, "Predicted AQI"];
                      if (name === "upper") return [value, "Upper Bound"];
                      if (name === "lower") return [value, "Lower Bound"];
                      return [value, name];
                    }}
                  />
                  {/* Severe Pollution Danger Reference Line */}
                  <ReferenceLine
                    y={300}
                    stroke="#EF4444"
                    strokeDasharray="6 4"
                    strokeWidth={1.5}
                    label={{
                      value: "Severe (300 AQI)",
                      fill: "#EF4444",
                      fontSize: 10,
                      position: "insideTopRight",
                    }}
                  />
                  {/* Upper Bound Area */}
                  <Area
                    type="monotone"
                    dataKey="upper"
                    stroke="none"
                    fill="url(#confidenceBand)"
                    name="upper"
                  />
                  {/* Main Predicted AQI Curve */}
                  <Line
                    type="monotone"
                    dataKey="aqi"
                    stroke="url(#aqiLineGradient)"
                    strokeWidth={3}
                    dot={{ r: 3, fill: "#22D3EE" }}
                    activeDot={{ r: 6, fill: "#38BDF8" }}
                    name="aqi"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </div>
        </section>

        {/* Summary Horizon Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: +24h */}
          <div
            onMouseMove={handleMouseMove}
            onClick={() => setSelectedHorizon(24)}
            className={`p-6 rounded-xl border flex items-center justify-between transition-all duration-300 relative overflow-hidden backdrop-blur-md cursor-pointer ${
              selectedHorizon === 24
                ? "border-[#22D3EE] bg-[#22D3EE]/10 shadow-[0_0_20px_rgba(34,211,238,0.15)]"
                : "border-[#334155]/50 bg-[#1E293B]/50 hover:border-[#22D3EE]/40"
            }`}
          >
            <div className="space-y-1">
              <p className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">+24 Hours</p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-extrabold text-white tracking-tight">{val24 || "—"}</span>
                {point24?.trend === "rising" ? (
                  <TrendingUp className="w-4 h-4 text-orange-400" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-cyan-400" />
                )}
              </div>
            </div>
            <div className="text-right">
              <span
                className={`px-3 py-1 rounded-full text-[10px] font-bold tracking-widest ${getCategoryChipClass(
                  val24
                )}`}
              >
                {getCategoryLabel(val24)}
              </span>
              <p className="mt-2 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wide">
                Trend: {point24?.trend || "Stable"}
              </p>
            </div>
          </div>

          {/* Card 2: +48h */}
          <div
            onMouseMove={handleMouseMove}
            onClick={() => setSelectedHorizon(48)}
            className={`p-6 rounded-xl border flex items-center justify-between transition-all duration-300 relative overflow-hidden backdrop-blur-md cursor-pointer ${
              selectedHorizon === 48
                ? "border-[#22D3EE] bg-[#22D3EE]/10 shadow-[0_0_20px_rgba(34,211,238,0.15)]"
                : "border-[#334155]/50 bg-[#1E293B]/50 hover:border-[#22D3EE]/40"
            }`}
          >
            <div className="space-y-1">
              <p className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">+48 Hours</p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-extrabold text-white tracking-tight">{val48 || "—"}</span>
                {point48?.trend === "rising" ? (
                  <TrendingUp className="w-4 h-4 text-red-500 animate-pulse" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-cyan-400" />
                )}
              </div>
            </div>
            <div className="text-right">
              <span
                className={`px-3 py-1 rounded-full text-[10px] font-bold tracking-widest ${getCategoryChipClass(
                  val48
                )}`}
              >
                {getCategoryLabel(val48)}
              </span>
              <p className="mt-2 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wide">
                Trend: {point48?.trend || "Stable"}
              </p>
            </div>
          </div>

          {/* Card 3: +72h */}
          <div
            onMouseMove={handleMouseMove}
            onClick={() => setSelectedHorizon(72)}
            className={`p-6 rounded-xl border flex items-center justify-between transition-all duration-300 relative overflow-hidden backdrop-blur-md cursor-pointer ${
              selectedHorizon === 72
                ? "border-[#22D3EE] bg-[#22D3EE]/10 shadow-[0_0_20px_rgba(34,211,238,0.15)]"
                : "border-[#334155]/50 bg-[#1E293B]/50 hover:border-[#22D3EE]/40"
            }`}
          >
            <div className="space-y-1">
              <p className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">+72 Hours</p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-extrabold text-white tracking-tight">{val72 || "—"}</span>
                {point72?.trend === "rising" ? (
                  <TrendingUp className="w-4 h-4 text-orange-400" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-cyan-400" />
                )}
              </div>
            </div>
            <div className="text-right">
              <span
                className={`px-3 py-1 rounded-full text-[10px] font-bold tracking-widest ${getCategoryChipClass(
                  val72
                )}`}
              >
                {getCategoryLabel(val72)}
              </span>
              <p className="mt-2 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wide">
                Trend: {point72?.trend || "Stable"}
              </p>
            </div>
          </div>
        </div>

        {/* AI Explainability & Feature Importance Panel */}
        <section
          onMouseMove={handleMouseMove}
          className="p-8 rounded-2xl border-l-4 border-l-[#22D3EE] border border-[#334155]/50 relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md shadow-inner-cyan"
          style={{
            background:
              "radial-gradient(1000px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
          }}
        >
          <div className="flex flex-col lg:flex-row gap-10 items-start">
            {/* Left Section: Model Reasoning & Top Drivers */}
            <div className="flex-1 space-y-6 w-full">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-[#22D3EE]/10 rounded-2xl flex items-center justify-center border border-[#22D3EE]/20 shadow-md">
                  <Sparkles className="w-7 h-7 text-[#22D3EE] animate-pulse" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white tracking-tight">AI Model Intelligence</h3>
                  <p className="text-xs text-[#22D3EE] font-semibold mt-0.5">
                    LightGBM Feature Attribution & Multi-Step Reasoning
                  </p>
                </div>
              </div>

              {/* Narrative Summary Quote */}
              <div className="bg-[#1E293B]/70 p-5 rounded-xl border border-[#3c494c]/40 space-y-2">
                <p className="text-[10px] font-bold text-[#22D3EE] uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-[#22D3EE]" />
                  PREDICTIVE REASONING
                </p>
                <p className="text-sm text-[#dae2fd] leading-relaxed italic font-light">
                  "{summaryReason}"
                </p>
              </div>

              {/* Top 5 Model Drivers */}
              <div className="space-y-3">
                <p className="text-[11px] font-bold text-[#bbc9cd] uppercase tracking-wider">
                  Top Drivers Influencing This Forecast (Model Feature Importance)
                </p>
                <div className="grid grid-cols-1 gap-3">
                  {topDrivers.length === 0 ? (
                    <p className="text-xs text-[#bbc9cd]/70 italic">Loading feature importances…</p>
                  ) : (
                    topDrivers.map((driver, idx) => (
                      <div
                        key={idx}
                        className="bg-[#131b2e] border border-[#3c494c]/30 rounded-xl p-3.5 space-y-2"
                      >
                        <div className="flex justify-between items-center text-xs">
                          <span className="font-bold text-white flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-[#22D3EE]/10 text-[#22D3EE] flex items-center justify-center text-[10px]">
                              {idx + 1}
                            </span>
                            {driver.feature}
                          </span>
                          <span className="font-extrabold text-[#22D3EE]">{driver.importance}% weight</span>
                        </div>
                        <div className="w-full h-1.5 bg-[#0F172A] rounded-full overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-[#22D3EE] to-[#818CF8] h-full rounded-full transition-all duration-700"
                            style={{ width: `${Math.min(100, Math.max(10, driver.importance * 2.2))}%` }}
                          />
                        </div>
                        <p className="text-[11px] text-[#bbc9cd] font-light leading-relaxed">
                          {driver.description}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Right Section: Real Live Meteorological Conditions */}
            <div className="w-full lg:w-80 flex flex-col gap-4">
              <div className="p-5 bg-[#1E293B]/40 rounded-xl border border-[#3c494c]/30 space-y-4">
                <div className="border-b border-[#3c494c]/30 pb-3">
                  <p className="text-[11px] font-bold text-white uppercase tracking-wider">
                    Current Meteorological Inputs
                  </p>
                  <p className="text-[10px] text-[#bbc9cd] mt-0.5">Live station readings feeding the model</p>
                </div>

                {/* Wind Speed */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-[#bbc9cd] flex items-center gap-1.5">
                      <Wind className="w-3.5 h-3.5 text-[#22D3EE]" /> Wind Speed
                    </span>
                    <span className="font-bold text-white">{weatherData?.wind_speed ?? "—"} km/h</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#0F172A] rounded-full overflow-hidden">
                    <div
                      className="bg-[#22D3EE] h-full rounded-full"
                      style={{
                        width: `${Math.min(100, ((weatherData?.wind_speed ?? 5) / 40) * 100)}%`,
                      }}
                    />
                  </div>
                </div>

                {/* Humidity */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-[#bbc9cd] flex items-center gap-1.5">
                      <Droplets className="w-3.5 h-3.5 text-cyan-400" /> Relative Humidity
                    </span>
                    <span className="font-bold text-white">{weatherData?.humidity ?? "—"}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#0F172A] rounded-full overflow-hidden">
                    <div
                      className="bg-cyan-400 h-full rounded-full"
                      style={{ width: `${Math.min(100, weatherData?.humidity ?? 50)}%` }}
                    />
                  </div>
                </div>

                {/* Temperature */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-[#bbc9cd] flex items-center gap-1.5">
                      <Thermometer className="w-3.5 h-3.5 text-amber-400" /> Temperature
                    </span>
                    <span className="font-bold text-white">{weatherData?.temperature ?? "—"}°C</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#0F172A] rounded-full overflow-hidden">
                    <div
                      className="bg-amber-400 h-full rounded-full"
                      style={{
                        width: `${Math.min(100, (((weatherData?.temperature ?? 25) + 5) / 50) * 100)}%`,
                      }}
                    />
                  </div>
                </div>

                {/* Precipitation */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-[#bbc9cd] flex items-center gap-1.5">
                      <CloudRain className="w-3.5 h-3.5 text-blue-400" /> Precipitation
                    </span>
                    <span className="font-bold text-white">{weatherData?.precipitation ?? 0} mm</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#0F172A] rounded-full overflow-hidden">
                    <div
                      className="bg-blue-400 h-full rounded-full"
                      style={{
                        width: `${Math.min(100, ((weatherData?.precipitation ?? 0) / 10) * 100)}%`,
                      }}
                    />
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
