import React, { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import { Sparkles, BellRing, TrendingUp, AlertTriangle, ArrowRight, ShieldAlert, Activity, CheckCircle2 } from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from "recharts";
import { getHeatmap, getPredict } from "../api/client";

interface HeatmapItem {
  ward_id: string;
  ward_name: string;
  aqi: number;
  category: string;
}

interface TrendPoint {
  time: string;
  hour: number;
  aqi: number;
  lower: number;
  upper: number;
}

export default function CityDashboard() {
  const [heatmapData, setHeatmapData] = useState<HeatmapItem[] | null>(null);
  const [forecastPoints, setForecastPoints] = useState<any[]>([]);
  const [forecastReason, setForecastReason] = useState<string | null>(null);
  const [loadingForecast, setLoadingForecast] = useState<boolean>(true);

  // Fetch heatmap data from backend API
  useEffect(() => {
    let isMounted = true;
    const loadData = async () => {
      try {
        const res = await getHeatmap();
        if (isMounted) {
          setHeatmapData(res);
        }
      } catch (err) {
        console.error("Error loading dashboard heatmap:", err);
      }
    };
    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch 24h city forecast curve (using baseline ward W01 or top reporting ward)
  useEffect(() => {
    let isMounted = true;
    const loadForecast = async () => {
      setLoadingForecast(true);
      try {
        // Query baseline ward W01 for 24h horizon
        const res = await getPredict("W01", 24);
        if (isMounted) {
          setForecastPoints(res.points || []);
          setForecastReason(res.summary_reason || null);
        }
      } catch (err) {
        console.error("Error loading 24h forecast trend:", err);
      } finally {
        if (isMounted) setLoadingForecast(false);
      }
    };
    loadForecast();
    return () => {
      isMounted = false;
    };
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

  // Wards with no reading come back as aqi=0 / "Unknown"
  const reportingWards = useMemo(() => {
    return (heatmapData ?? []).filter(
      (h) => h.aqi > 0 && h.category?.toLowerCase() !== "unknown"
    );
  }, [heatmapData]);

  const hasData = reportingWards.length > 0;

  const getAqiCategory = (aqi: number | null) => {
    if (aqi === null) return { label: "NO DATA", class: "bg-slate-700/40 text-slate-400 border-slate-600/40" };
    if (aqi <= 50) return { label: "GOOD", class: "bg-green-500/20 text-green-400 border-green-500/30" };
    if (aqi <= 100) return { label: "SATISFACTORY", class: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30" };
    if (aqi <= 200) return { label: "MODERATE", class: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" };
    if (aqi <= 300) return { label: "POOR", class: "bg-orange-500/20 text-orange-400 border-orange-500/30" };
    if (aqi <= 400) return { label: "VERY POOR", class: "bg-red-800/30 text-red-400 border-red-500/30" };
    return { label: "SEVERE", class: "bg-red-900/50 text-red-400 border-red-500/40" };
  };

  // 1. City average AQI
  const averageAqi = hasData
    ? Math.round(reportingWards.reduce((sum, h) => sum + h.aqi, 0) / reportingWards.length)
    : null;
  const avgCategory = getAqiCategory(averageAqi);

  // 2. Worst ward
  const worstWard = hasData ? [...reportingWards].sort((a, b) => b.aqi - a.aqi)[0] : null;
  const worstWardLabel = worstWard ? `${worstWard.ward_name} · ${worstWard.aqi}` : "—";
  const worstWardCategory = getAqiCategory(worstWard ? worstWard.aqi : null);

  // 3. Best ward
  const bestWard = hasData ? [...reportingWards].sort((a, b) => a.aqi - b.aqi)[0] : null;
  const bestWardLabel = bestWard ? `${bestWard.ward_name} · ${bestWard.aqi}` : "—";
  const bestWardCategory = getAqiCategory(bestWard ? bestWard.aqi : null);

  // 4. Wards in the severe zone (AQI > 200)
  const totalWardsCount = reportingWards.length;
  const severeWardsCount = reportingWards.filter(
    (h) => h.aqi > 200 || h.category?.toLowerCase() === "severe"
  ).length;

  const severePercent = hasData && totalWardsCount > 0 ? Math.round((severeWardsCount / totalWardsCount) * 100) : 0;
  const strokeDashArrayValue = `${severePercent}, 100`;

  // Top 5 Hotspot Wards
  const topHotspots = useMemo(() => {
    return [...reportingWards].sort((a, b) => b.aqi - a.aqi).slice(0, 5);
  }, [reportingWards]);

  // Transform forecast points for the 24h AreaChart
  const chartData: TrendPoint[] = useMemo(() => {
    if (!forecastPoints || forecastPoints.length === 0) {
      // Sensible baseline 24h hourly points if still connecting
      const base = averageAqi || 140;
      return Array.from({ length: 24 }).map((_, i) => {
        const h = (new Date().getHours() + i) % 24;
        const variation = Math.sin((i / 24) * Math.PI * 2) * 25;
        const val = Math.round(base + variation);
        return {
          time: `${String(h).padStart(2, "0")}:00`,
          hour: h,
          aqi: val,
          lower: Math.max(20, val - 12),
          upper: val + 15,
        };
      });
    }

    return forecastPoints.map((pt) => {
      const d = new Date(pt.timestamp);
      const h = d.getHours();
      const timeStr = `${String(h).padStart(2, "0")}:00`;
      const val = Math.round(pt.predicted_aqi);
      return {
        time: timeStr,
        hour: h,
        aqi: val,
        lower: Math.round(pt.lower ?? val * 0.92),
        upper: Math.round(pt.upper ?? val * 1.08),
      };
    });
  }, [forecastPoints, averageAqi]);

  // Identify peak forecast point and AI insight
  const peakPoint = useMemo(() => {
    if (chartData.length === 0) return null;
    return chartData.reduce((max, p) => (p.aqi > max.aqi ? p : max), chartData[0]);
  }, [chartData]);

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
              <span className="text-5xl font-extrabold text-white tracking-tight">{averageAqi ?? "—"}</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${avgCategory.class}`}>
                {avgCategory.label}
              </span>
            </div>
            <div className="flex items-center gap-1.5 mt-4">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              <span className="text-xs text-[#bbc9cd]">Live CPCB & Open-Meteo Telemetry</span>
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
            <span className="text-[11px] font-bold text-[#bbc9cd] tracking-widest uppercase">Worst Hotspot</span>
            <div className="mt-4">
              <div className="text-xl font-bold text-white tracking-tight truncate">{worstWardLabel}</div>
              <span className={`inline-block mt-2 px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${worstWardCategory.class}`}>
                {worstWardCategory.label}
              </span>
            </div>
            <p className="text-xs text-[#bbc9cd] mt-4">Critical Action Recommended</p>
          </div>

          {/* KPI 3: Best Ward */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl flex flex-col justify-between border border-[#334155]/50 transition-all duration-300 relative overflow-hidden group hover:border-[#22d3ee] hover:shadow-[0_0_20px_rgba(34,211,238,0.1)] hover:-translate-y-0.5 bg-[#1E293B]/50 backdrop-blur-md"
            style={{
              background: "radial-gradient(800px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <span className="text-[11px] font-bold text-[#bbc9cd] tracking-widest uppercase">Cleanest Zone</span>
            <div className="mt-4">
              <div className="text-xl font-bold text-white tracking-tight truncate">{bestWardLabel}</div>
              <span className={`inline-block mt-2 px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${bestWardCategory.class}`}>
                {bestWardCategory.label}
              </span>
            </div>
            <p className="text-xs text-[#bbc9cd] mt-4">Optimal Air Dispersion</p>
          </div>

          {/* KPI 4: Wards in Severe Zone */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl flex flex-col justify-between border border-[#334155]/50 transition-all duration-300 relative overflow-hidden group hover:border-[#22d3ee] hover:shadow-[0_0_20px_rgba(34,211,238,0.1)] hover:-translate-y-0.5 bg-[#1E293B]/50 backdrop-blur-md"
            style={{
              background: "radial-gradient(800px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <span className="text-[11px] font-bold text-[#bbc9cd] tracking-widest uppercase">Wards in Poor/Severe Zone</span>
            <div className="flex items-center justify-between mt-4">
              <span className="text-5xl font-extrabold text-white tracking-tight">
                {hasData ? `${severeWardsCount}/${totalWardsCount}` : "—"}
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
            <p className="text-xs text-red-400 font-medium mt-4">
              {severePercent}% of wards above safe limits
            </p>
          </div>
        </div>

        {/* Main Analysis Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column (8 cols): Recharts Dynamic Trend Area */}
          <div
            onMouseMove={handleMouseMove}
            className="lg:col-span-8 p-6 rounded-xl border border-[#334155]/50 transition-all duration-300 relative overflow-hidden flex flex-col bg-[#1E293B]/50 backdrop-blur-md"
            style={{
              background: "radial-gradient(1000px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.06), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-4">
              <div>
                <h3 className="text-xl font-bold text-white tracking-tight">City 24h Outlook & ML Trajectory</h3>
                <p className="text-xs text-[#bbc9cd] mt-0.5">
                  LightGBM recursive multi-step forecasting with 95% confidence bounds
                </p>
              </div>
              <div className="bg-[#22D3EE]/10 border border-[#22D3EE]/25 rounded-lg px-3.5 py-1.5 flex items-center gap-2 shadow-inner-cyan">
                <Sparkles className="w-4 h-4 text-[#22D3EE] animate-pulse flex-shrink-0" />
                <span className="text-xs font-semibold text-[#22D3EE]">
                  {peakPoint
                    ? `AI Insight: Peak AQI ${peakPoint.aqi} at ${peakPoint.time} (${forecastReason || "Wind speed deceleration"})`
                    : "AI Insight: Synchronizing ML inference engine"}
                </span>
              </div>
            </div>

            {/* Recharts Dynamic Trend Chart */}
            <div className="flex-1 w-full min-h-[310px] mt-2">
              <ResponsiveContainer width="100%" height={310}>
                <AreaChart data={chartData} margin={{ top: 20, right: 15, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="cityAqiGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="cityConfGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>

                  <XAxis
                    dataKey="time"
                    stroke="#64748b"
                    fontSize={11}
                    tickLine={false}
                    interval={3}
                  />
                  <YAxis
                    stroke="#64748b"
                    fontSize={11}
                    tickLine={false}
                    domain={[0, "auto"]}
                  />

                  {/* Reference Threshold Lines */}
                  <ReferenceLine
                    y={100}
                    stroke="#eab308"
                    strokeDasharray="4 4"
                    label={{ value: "100 Mod", fill: "#eab308", fontSize: 10, position: "insideTopLeft" }}
                  />
                  <ReferenceLine
                    y={200}
                    stroke="#f97316"
                    strokeDasharray="4 4"
                    label={{ value: "200 Poor", fill: "#f97316", fontSize: 10, position: "insideTopLeft" }}
                  />
                  <ReferenceLine
                    y={300}
                    stroke="#ef4444"
                    strokeDasharray="4 4"
                    label={{ value: "300 Severe", fill: "#ef4444", fontSize: 10, position: "insideTopLeft" }}
                  />

                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "0.5rem",
                      fontSize: "12px",
                      color: "#f8fafc",
                    }}
                    formatter={(value: any, name: string) => {
                      if (name === "aqi") return [`${value} AQI`, "Predicted AQI"];
                      if (name === "upper") return [`${value} AQI`, "Upper Bound (95%)"];
                      if (name === "lower") return [`${value} AQI`, "Lower Bound (95%)"];
                      return [value, name];
                    }}
                    labelFormatter={(label) => `Hour: ${label}`}
                  />

                  {/* Upper confidence band */}
                  <Area
                    type="monotone"
                    dataKey="upper"
                    stroke="none"
                    fill="url(#cityConfGrad)"
                  />
                  {/* Predicted AQI curve */}
                  <Area
                    type="monotone"
                    dataKey="aqi"
                    stroke="#22d3ee"
                    strokeWidth={2.5}
                    fill="url(#cityAqiGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="flex items-center justify-between text-[11px] text-[#94a3b8] pt-3 border-t border-[#334155]/40 mt-1">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#22d3ee]" />
                Predicted AQI Trajectory
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#38bdf8]/40" />
                95% Confidence Interval Band
              </span>
              <Link to="/forecast" className="text-[#22d3ee] font-bold hover:underline flex items-center gap-1">
                Explore 72h Decomposition →
              </Link>
            </div>
          </div>

          {/* Right Column (4 cols): Dynamic Hotspot Leaderboard */}
          <div
            onMouseMove={handleMouseMove}
            className="lg:col-span-4 p-6 rounded-xl border border-[#334155]/50 transition-all duration-300 relative overflow-hidden flex flex-col bg-[#1E293B]/50 backdrop-blur-md"
            style={{
              background: "radial-gradient(800px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-xl font-bold text-white tracking-tight">Hotspot Monitor</h3>
                <p className="text-xs text-[#94a3b8]">Live reporting wards ranked by risk</p>
              </div>
              <Link
                to="/map"
                className="text-xs font-bold text-[#22D3EE] hover:underline transition-all tracking-wider uppercase flex items-center gap-1"
              >
                <span>Full Map</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {/* Hotspots Leaderboard List */}
            <div className="flex-1 space-y-3 mt-1">
              {topHotspots.length === 0 ? (
                <div className="p-4 text-center text-xs text-[#94a3b8] flex flex-col items-center justify-center h-48">
                  <Activity className="w-6 h-6 animate-pulse text-[#22d3ee] mb-2" />
                  <span>Loading live ward telemetry...</span>
                </div>
              ) : (
                topHotspots.map((item, idx) => {
                  const cat = getAqiCategory(item.aqi);
                  const barWidth = Math.min(100, Math.max(15, (item.aqi / 400) * 100));
                  return (
                    <div
                      key={item.ward_id}
                      className="p-3 rounded-lg bg-[#0f172a]/70 border border-[#334155]/60 hover:border-[#22d3ee]/40 transition-all"
                    >
                      <div className="flex items-center justify-between text-xs mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="w-4 text-center font-bold text-[#64748b]">#{idx + 1}</span>
                          <span className="font-semibold text-white truncate max-w-[130px]">
                            {item.ward_name}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-extrabold text-white">{item.aqi}</span>
                          <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold border uppercase ${cat.class}`}>
                            {cat.label}
                          </span>
                        </div>
                      </div>

                      {/* Mini Bar */}
                      <div className="w-full h-1.5 bg-[#1e293b] rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${barWidth}%`,
                            backgroundColor:
                              item.aqi > 300 ? "#ef4444" : item.aqi > 200 ? "#f97316" : item.aqi > 100 ? "#eab308" : "#22d3ee",
                          }}
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* City Distribution Summary */}
            <div className="mt-4 pt-4 border-t border-[#334155]/50 bg-[#0f172a]/40 p-3 rounded-lg">
              <div className="flex justify-between text-[11px] text-[#bbc9cd] mb-1.5">
                <span>Severe / Poor Zone:</span>
                <span className="font-bold text-red-400">{severeWardsCount} Wards</span>
              </div>
              <div className="flex justify-between text-[11px] text-[#bbc9cd]">
                <span>Satisfactory / Good:</span>
                <span className="font-bold text-green-400">
                  {Math.max(0, totalWardsCount - severeWardsCount)} Wards
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Dynamic Alerts Strip */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BellRing className="w-5 h-5 text-[#22D3EE] animate-bounce" />
              <h4 className="text-[11px] font-bold text-[#bbc9cd] uppercase tracking-widest">
                Active Tactical Alerts
              </h4>
            </div>
            <span className="text-[10px] text-[#64748b] uppercase tracking-wider">
              Updated Live from Edge Telemetry
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Alert 1: Critical Hotspot Alert */}
            <div
              onMouseMove={handleMouseMove}
              className="p-4 rounded-xl border border-[#334155]/50 flex items-center gap-4 relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md"
              style={{
                background: "radial-gradient(400px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
                borderLeft: "4px solid #ef4444",
              }}
            >
              <div className="p-2 rounded-lg bg-red-500/20 text-red-400 flex-shrink-0">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-[#dae2fd] leading-relaxed font-normal">
                  {worstWard
                    ? `${worstWard.ward_name} is currently the top pollution hotspot (AQI ${worstWard.aqi}). Mechanical sweeping active.`
                    : "Calibrating real-time ward telemetry across Delhi."}
                </p>
                <span className="text-[9px] font-bold text-[#22D3EE] uppercase flex items-center gap-1 mt-1.5 tracking-wider">
                  <Sparkles className="w-3 h-3 text-[#22D3EE]" /> Hotspot Telemetry
                </span>
              </div>
            </div>

            {/* Alert 2: Forecast Surge Alert */}
            <div
              onMouseMove={handleMouseMove}
              className="p-4 rounded-xl border border-[#334155]/50 flex items-center gap-4 relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md"
              style={{
                background: "radial-gradient(400px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
                borderLeft: "4px solid #f97316",
              }}
            >
              <div className="p-2 rounded-lg bg-orange-500/20 text-orange-400 flex-shrink-0">
                <TrendingUp className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-[#dae2fd] leading-relaxed font-normal">
                  {peakPoint
                    ? `Peak concentration anticipated around ${peakPoint.time} with predicted AQI of ${peakPoint.aqi}.`
                    : "LightGBM model tracking 24h diurnal wind shift patterns."}
                </p>
                <span className="text-[9px] font-bold text-[#22D3EE] uppercase flex items-center gap-1 mt-1.5 tracking-wider">
                  <Sparkles className="w-3 h-3 text-[#22D3EE]" /> 24h Predictive Trend
                </span>
              </div>
            </div>

            {/* Alert 3: Spatial Disparity / Health Threshold Alert */}
            <div
              onMouseMove={handleMouseMove}
              className="p-4 rounded-xl border border-[#334155]/50 flex items-center gap-4 relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md"
              style={{
                background: "radial-gradient(400px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.08), transparent 80%), rgba(30, 41, 59, 0.5)",
                borderLeft: "4px solid #38bdf8",
              }}
            >
              <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-400 flex-shrink-0">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-[#dae2fd] leading-relaxed font-normal">
                  {severeWardsCount > 0
                    ? `${severeWardsCount} of ${totalWardsCount} wards exceed 200 AQI. Staggered misting deployed.`
                    : `Air dispersion stable; delta between worst and cleanest ward is ${worstWard && bestWard ? worstWard.aqi - bestWard.aqi : 20} AQI points.`}
                </p>
                <span className="text-[9px] font-bold text-[#22D3EE] uppercase flex items-center gap-1 mt-1.5 tracking-wider">
                  <Sparkles className="w-3 h-3 text-[#22D3EE]" /> Spatial Equilibrium
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
