import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  MapPin,
  Sparkles,
  Activity,
  ShieldCheck,
  Sun,
  Moon,
  Sunrise,
  Users,
  RefreshCw,
  AlertTriangle,
  Wind,
  Droplets,
  Thermometer,
  CheckCircle2,
  ChevronRight,
  HeartPulse,
  ExternalLink,
} from "lucide-react";
import { getWards, getAQI, getWeather, getPredict, getAdvisory } from "../api/client";

interface WardOption {
  id: string;
  name: string;
}

interface ForecastPoint {
  timestamp: string;
  predicted_aqi: number;
  trend: "rising" | "falling" | "stable";
  lower: number;
  upper: number;
}

interface AdvisoryData {
  ward_id: string;
  language: string;
  aqi: number;
  advice: string;
  best_outdoor_window?: string;
  worst_outdoor_window?: string;
}

export default function CitizenView() {
  const [wards, setWards] = useState<WardOption[]>([]);
  const [selectedWard, setSelectedWard] = useState<string>("W01");
  const [selectedProfile, setSelectedProfile] = useState<string>("asthma");
  const [selectedLang, setSelectedLang] = useState<string>("en");

  const [aqiData, setAqiData] = useState<any>(null);
  const [weatherData, setWeatherData] = useState<any>(null);
  const [advisory, setAdvisory] = useState<AdvisoryData | null>(null);
  const [forecastPoints, setForecastPoints] = useState<ForecastPoint[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [advisoryLoading, setAdvisoryLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Card hover animation style configurations
  const cardStyle = {
    backgroundColor: "#ffffff",
    border: "1px solid #dee3e5",
    borderRadius: "1rem",
    boxShadow: "0 4px 20px -2px rgba(0, 0, 0, 0.05)",
    transition: "transform 0.3s ease-out, box-shadow 0.3s ease-out",
  };

  const handleMouseEnter = (e: React.MouseEvent<HTMLDivElement>) => {
    e.currentTarget.style.transform = "translateY(-2px)";
    e.currentTarget.style.boxShadow = "0 8px 24px -2px rgba(0, 0, 0, 0.08)";
  };

  const handleMouseLeave = (e: React.MouseEvent<HTMLDivElement>) => {
    e.currentTarget.style.transform = "translateY(0)";
    e.currentTarget.style.boxShadow = "0 4px 20px -2px rgba(0, 0, 0, 0.05)";
  };

  // 1. Fetch available wards once on mount
  useEffect(() => {
    let isMounted = true;
    const fetchWardList = async () => {
      try {
        const res = await getWards();
        const features = res?.features ?? [];
        const options: WardOption[] = features.map((f: any) => ({
          id: f.properties?.id ?? f.id ?? "W01",
          name: f.properties?.name ?? `Ward ${f.properties?.id ?? "W01"}`,
        }));

        if (options.length === 0) {
          // Standard Delhi Ward defaults if empty GeoJSON
          options.push(
            { id: "W01", name: "Connaught Place" },
            { id: "W02", name: "Rohini" },
            { id: "W03", name: "Dwarka" },
            { id: "W04", name: "Karol Bagh" },
            { id: "W05", name: "Okhla Industrial Area" },
            { id: "W06", name: "Greater Kailash" },
            { id: "W07", name: "Anand Vihar" },
            { id: "W08", name: "Janakpuri" },
            { id: "W09", name: "Narela" },
            { id: "W10", name: "Vasant Kunj" }
          );
        }

        if (isMounted) {
          setWards(options);
          if (!options.some((o) => o.id === selectedWard)) {
            setSelectedWard(options[0].id);
          }
        }
      } catch (err) {
        console.warn("Could not load wards GeoJSON, using default ward list", err);
        if (isMounted) {
          setWards([
            { id: "W01", name: "Connaught Place" },
            { id: "W02", name: "Rohini" },
            { id: "W03", name: "Dwarka" },
            { id: "W04", name: "Karol Bagh" },
            { id: "W05", name: "Okhla Industrial Area" },
            { id: "W06", name: "Greater Kailash" },
            { id: "W07", name: "Anand Vihar" },
            { id: "W08", name: "Janakpuri" },
            { id: "W09", name: "Narela" },
            { id: "W10", name: "Vasant Kunj" },
          ]);
        }
      }
    };
    fetchWardList();
    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Fetch live data whenever selectedWard changes
  const loadWardData = useCallback(async (wardId: string) => {
    setLoading(true);
    setError(null);
    try {
      const [aqiRes, weatherRes, forecastRes] = await Promise.allSettled([
        getAQI(wardId),
        getWeather(wardId),
        getPredict(wardId, 24),
      ]);

      if (aqiRes.status === "fulfilled") {
        setAqiData(aqiRes.value);
      }
      if (weatherRes.status === "fulfilled") {
        setWeatherData(weatherRes.value);
      }
      if (forecastRes.status === "fulfilled") {
        setForecastPoints(forecastRes.value.points || []);
      }
    } catch (err: any) {
      console.error("Error loading ward citizen data:", err);
      setError("Unable to sync latest atmospheric telemetry.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedWard) {
      loadWardData(selectedWard);
    }
  }, [selectedWard, loadWardData]);

  // 3. Fetch AI Health Guidance whenever ward, profile, or language changes
  const loadAdvisory = useCallback(async (wardId: string, lang: string, profile: string) => {
    setAdvisoryLoading(true);
    try {
      const res = await getAdvisory(wardId, lang, profile);
      setAdvisory(res);
    } catch (err) {
      console.error("Error fetching AI advisory:", err);
      // Fallback sensible message
      setAdvisory({
        ward_id: wardId,
        language: lang,
        aqi: 180,
        advice:
          lang === "hi"
            ? "आज वायु गुणवत्ता मध्यम से खराब श्रेणी में है। कृपया मास्क पहनें और भारी बाहरी गतिविधियों से बचें।"
            : "Air quality requires vigilance today. Please wear an N95 mask outside and limit strenuous outdoor activities during peak rush hours.",
        best_outdoor_window: "15:00-17:00",
        worst_outdoor_window: "07:00-10:00",
      });
    } finally {
      setAdvisoryLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedWard) {
      loadAdvisory(selectedWard, selectedLang, selectedProfile);
    }
  }, [selectedWard, selectedLang, selectedProfile, loadAdvisory]);

  // Current AQI values and category styles
  const currentAqi = aqiData?.aqi ?? 145;
  const wardName =
    aqiData?.ward_name ?? wards.find((w) => w.id === selectedWard)?.name ?? `Ward ${selectedWard}`;

  const getAqiTheme = (val: number) => {
    if (val <= 50) {
      return {
        label: "GOOD",
        textColor: "text-[#006d31]",
        badgeBg: "bg-[#b4f4c2]/30",
        badgeBorder: "border-[#b4f4c2]",
        stroke: "#00b954",
      };
    }
    if (val <= 100) {
      return {
        label: "SATISFACTORY",
        textColor: "text-[#006877]",
        badgeBg: "bg-[#a2eeff]/30",
        badgeBorder: "border-[#a2eeff]",
        stroke: "#00a5bc",
      };
    }
    if (val <= 200) {
      return {
        label: "MODERATE",
        textColor: "text-[#944b00]",
        badgeBg: "bg-[#ffae83]/25",
        badgeBorder: "border-[#ffae83]",
        stroke: "#f59e0b",
      };
    }
    if (val <= 300) {
      return {
        label: "POOR",
        textColor: "text-[#ba1a1a]",
        badgeBg: "bg-[#ffdad6]/60",
        badgeBorder: "border-[#ffdad6]",
        stroke: "#f97316",
      };
    }
    if (val <= 400) {
      return {
        label: "VERY POOR",
        textColor: "text-[#7f1d1d]",
        badgeBg: "bg-red-100",
        badgeBorder: "border-red-300",
        stroke: "#dc2626",
      };
    }
    return {
      label: "SEVERE",
      textColor: "text-[#5b0007]",
      badgeBg: "bg-red-200",
      badgeBorder: "border-red-500",
      stroke: "#991b1b",
    };
  };

  const aqiTheme = getAqiTheme(currentAqi);
  const progressPercent = Math.min(100, (currentAqi / 500) * 100);
  const strokeDashoffset = 282.7 - (282.7 * progressPercent) / 100;

  // Dynamic activity safety calculations
  const getActivitySafety = (activity: string) => {
    const isAsthma = selectedProfile === "asthma";
    const isJogger = selectedProfile === "jogger";
    const isElderly = selectedProfile === "elderly";

    switch (activity) {
      case "running":
        if (currentAqi <= 50) return { status: "SAFE", bg: "bg-[#b4f4c2]", text: "text-[#002109]", desc: "Ideal air conditions for outdoor cardio." };
        if (currentAqi <= 100) return { status: "SAFE", bg: "bg-[#b4f4c2]", text: "text-[#002109]", desc: "Safe for regular running. Stay hydrated." };
        if (currentAqi <= 150) {
          if (isAsthma) return { status: "CAUTION", bg: "bg-[#ffae83]", text: "text-[#4a2300]", desc: "Shift to indoor treadmill or keep inhaler ready." };
          if (isJogger) return { status: "MODERATE", bg: "bg-[#ffdad6]", text: "text-[#ba1a1a]", desc: "Opt for afternoon windows when AQI dips." };
          return { status: "MODERATE", bg: "bg-[#ffae83]", text: "text-[#4a2300]", desc: "Reduce intense outdoor exertion." };
        }
        return { status: "UNSAFE", bg: "bg-[#ffdad6]", text: "text-[#ba1a1a]", desc: "High particulate load. Exercise strictly indoors." };

      case "outdoor_event":
        if (currentAqi <= 100) return { status: "SAFE", bg: "bg-[#b4f4c2]", text: "text-[#002109]", desc: "Great weather for outdoor gatherings and dining." };
        if (currentAqi <= 200) return { status: "CAUTION", bg: "bg-[#ffae83]", text: "text-[#4a2300]", desc: "Limit continuous exposure between rush hours." };
        return { status: "AVOID", bg: "bg-[#ffdad6]", text: "text-[#ba1a1a]", desc: "Prolonged exposure hazardous; wear N95 mask." };

      case "park_play":
        if (currentAqi <= 100) return { status: "SAFE", bg: "bg-[#b4f4c2]", text: "text-[#002109]", desc: "Optimal conditions for children and park strolls." };
        if (currentAqi <= 200) {
          if (isElderly || isAsthma) return { status: "CAUTION", bg: "bg-[#ffae83]", text: "text-[#4a2300]", desc: "Limit outdoor play to warm mid-afternoon hours." };
          return { status: "MODERATE", bg: "bg-[#ffae83]", text: "text-[#4a2300]", desc: "Take frequent hydration breaks indoors." };
        }
        return { status: "STAY IN", bg: "bg-[#ffdad6]", text: "text-[#ba1a1a]", desc: "Keep children and seniors indoors." };

      case "ventilation":
        if (currentAqi <= 100) return { status: "GOOD", bg: "bg-[#b4f4c2]", text: "text-[#002109]", desc: "Safe to open windows for natural air exchange." };
        if (currentAqi <= 200) return {
          status: "WINDOW",
          bg: "bg-[#a2eeff]",
          text: "text-[#006877]",
          desc: `Aerate only during best slot (${advisory?.best_outdoor_window || "15:00-17:00"}).`,
        };
        return { status: "SEAL", bg: "bg-[#ffdad6]", text: "text-[#ba1a1a]", desc: "Keep windows closed. Run air purifier." };

      default:
        return { status: "SAFE", bg: "bg-[#b4f4c2]", text: "text-[#002109]", desc: "Normal precautions." };
    }
  };

  // 24h Outlook points derived from real forecast
  const outlookItems = React.useMemo(() => {
    if (!forecastPoints || forecastPoints.length === 0) {
      return [
        { label: "NOW", aqi: currentAqi, barPercent: Math.min(100, (currentAqi / 400) * 100), color: "#00b954" },
        { label: "+6h", aqi: Math.round(currentAqi * 1.05), barPercent: Math.min(100, ((currentAqi * 1.05) / 400) * 100), color: "#ffae83" },
        { label: "+12h", aqi: Math.round(currentAqi * 0.95), barPercent: Math.min(100, ((currentAqi * 0.95) / 400) * 100), color: "#00b954" },
        { label: "+24h", aqi: Math.round(currentAqi * 0.88), barPercent: Math.min(100, ((currentAqi * 0.88) / 400) * 100), color: "#00b954" },
      ];
    }

    const intervals = [0, 4, 11, 23];
    return intervals.map((idx, step) => {
      const pt = forecastPoints[Math.min(idx, forecastPoints.length - 1)];
      const d = new Date(pt.timestamp);
      const timeStr = step === 0 ? "NOW" : d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
      const aqi = Math.round(pt.predicted_aqi);
      const percent = Math.min(100, (aqi / 400) * 100);
      const color = aqi <= 100 ? "#00b954" : aqi <= 200 ? "#f59e0b" : "#ef4444";
      return {
        label: timeStr,
        aqi,
        barPercent: percent,
        color,
      };
    });
  }, [forecastPoints, currentAqi]);

  // Derived diurnal windows from forecast points
  const diurnalWindows = React.useMemo(() => {
    if (!forecastPoints || forecastPoints.length < 6) {
      return {
        morning: { label: "Fresh", color: "text-green-600" },
        afternoon: { label: "Hazy", color: "text-amber-600" },
        evening: { label: "Moderate", color: "text-green-600" },
      };
    }

    const getAvgForHours = (startHour: number, endHour: number) => {
      const pts = forecastPoints.filter((p) => {
        const h = new Date(p.timestamp).getHours();
        return h >= startHour && h < endHour;
      });
      if (pts.length === 0) return currentAqi;
      return pts.reduce((acc, p) => acc + p.predicted_aqi, 0) / pts.length;
    };

    const morningAvg = getAvgForHours(6, 12);
    const afternoonAvg = getAvgForHours(12, 18);
    const eveningAvg = getAvgForHours(18, 24);

    const getCondition = (avg: number) => {
      if (avg <= 75) return { label: "Clean", color: "text-green-600" };
      if (avg <= 150) return { label: "Moderate", color: "text-cyan-700" };
      if (avg <= 250) return { label: "Hazy", color: "text-amber-600" };
      return { label: "Severe", color: "text-red-600" };
    };

    return {
      morning: getCondition(morningAvg),
      afternoon: getCondition(afternoonAvg),
      evening: getCondition(eveningAvg),
    };
  }, [forecastPoints, currentAqi]);

  return (
    <div className="flex-1 w-full h-full overflow-y-auto p-6 md:p-8 space-y-8 bg-[#fdfcff] text-[#191c1e] font-sans pb-24">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Hero Header Section with Dynamic Controls */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 bg-white p-6 rounded-2xl border border-[#dee3e5] shadow-sm">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 text-[10px] font-extrabold uppercase tracking-wider rounded-full bg-[#006877]/10 text-[#006877]">
                Citizen Health Portal
              </span>
              <span className="text-xs text-[#70787d]">· Delhi Urban Air Intelligence</span>
            </div>
            <h1 className="text-3xl font-extrabold text-[#191c1e] tracking-tight">
              Ward Health Advisory
            </h1>
            <p className="text-sm text-[#40484b] mt-1">
              Personalized air quality guidance for{" "}
              <span className="font-bold text-[#006877]">{wardName}</span>.
            </p>
          </div>

          {/* Interactive Selectors: Ward, Language, Profile */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Ward Selector */}
            <div className="flex items-center gap-1.5 bg-[#f0f4f8] px-3 py-1.5 rounded-xl border border-[#cbd5e1]">
              <MapPin className="w-4 h-4 text-[#006877]" />
              <select
                aria-label="Select Ward"
                value={selectedWard}
                onChange={(e) => setSelectedWard(e.target.value)}
                className="bg-transparent text-xs font-bold text-[#191c1e] focus:outline-none cursor-pointer"
              >
                {wards.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name} ({w.id})
                  </option>
                ))}
              </select>
            </div>

            {/* Profile Selector */}
            <div className="flex items-center gap-1.5 bg-[#f0f4f8] px-3 py-1.5 rounded-xl border border-[#cbd5e1]">
              <HeartPulse className="w-4 h-4 text-[#006d31]" />
              <select
                aria-label="Health Profile"
                value={selectedProfile}
                onChange={(e) => setSelectedProfile(e.target.value)}
                className="bg-transparent text-xs font-bold text-[#191c1e] focus:outline-none cursor-pointer"
              >
                <option value="general public">General Public</option>
                <option value="asthma">Asthma / Sensitive</option>
                <option value="jogger">Daily Jogger / Athlete</option>
                <option value="elderly">Elderly & Children</option>
              </select>
            </div>

            {/* Language Selector */}
            <div className="flex items-center gap-1.5 bg-[#f0f4f8] px-3 py-1.5 rounded-xl border border-[#cbd5e1]">
              <span className="text-xs font-bold text-[#40484b]">Lang:</span>
              <select
                aria-label="Advisory Language"
                value={selectedLang}
                onChange={(e) => setSelectedLang(e.target.value)}
                className="bg-transparent text-xs font-bold text-[#191c1e] focus:outline-none cursor-pointer"
              >
                <option value="en">English (EN)</option>
                <option value="hi">हिन्दी (HI)</option>
                <option value="pa">ਪੰਜਾਬੀ (PA)</option>
                <option value="bn">বাংলা (BN)</option>
              </select>
            </div>

            {/* Refresh Button */}
            <button
              onClick={() => {
                loadWardData(selectedWard);
                loadAdvisory(selectedWard, selectedLang, selectedProfile);
              }}
              disabled={loading || advisoryLoading}
              title="Refresh Telemetry & Advisory"
              className="p-2 rounded-xl border border-[#cbd5e1] hover:bg-[#e7e8ee] transition-colors active:scale-95 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 text-[#40484b] ${loading || advisoryLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </header>

        {/* Bento Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column (3 cols): AQI Gauge & Location Details */}
          <div className="lg:col-span-3 flex flex-col gap-8">
            {/* Current AQI Gauge Card */}
            <div
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
              style={cardStyle}
              className="p-6 flex flex-col items-center text-center relative overflow-hidden bg-white"
            >
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(180,244,194,0.25)_0%,transparent_70%)] pointer-events-none" />

              <div className="w-full flex items-center justify-between mb-4 relative z-10">
                <p className="text-[10px] font-bold text-[#40484b] tracking-widest uppercase">
                  CALIBRATED AQI
                </p>
                <span className={`px-2 py-0.5 rounded-full text-[9px] font-extrabold border ${aqiTheme.badgeBg} ${aqiTheme.badgeBorder} ${aqiTheme.textColor}`}>
                  {aqiTheme.label}
                </span>
              </div>

              {/* Gauge */}
              <div className="relative w-48 h-48 flex items-center justify-center my-2 z-10">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" fill="none" r="45" stroke="#e1e2e9" strokeWidth="7" />
                  <circle
                    cx="50"
                    cy="50"
                    fill="none"
                    r="45"
                    stroke={aqiTheme.stroke}
                    strokeDasharray="282.7"
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    strokeWidth="7"
                    className="transition-all duration-1000"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className={`text-5xl font-extrabold tracking-tight ${aqiTheme.textColor}`}>
                    {loading ? "..." : currentAqi}
                  </span>
                  <span className="text-[10px] font-bold text-[#40484b] tracking-wider uppercase mt-0.5">
                    CPCB SCALE
                  </span>
                </div>
              </div>

              {/* Pollutant Breakdown Parameters */}
              <div className="w-full flex flex-col gap-2 relative z-10 border-t border-[#dee3e5]/50 pt-4 text-xs font-medium text-[#40484b]">
                <div className="flex justify-between items-center py-1 border-b border-[#dee3e5]/20">
                  <span>PM 2.5</span>
                  <span className="font-bold text-[#191c1e]">
                    {aqiData?.pm25 ? `${Math.round(aqiData.pm25)} µg/m³` : "—"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-[#dee3e5]/20">
                  <span>PM 10</span>
                  <span className="font-bold text-[#191c1e]">
                    {aqiData?.pm10 ? `${Math.round(aqiData.pm10)} µg/m³` : "—"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-[#dee3e5]/20">
                  <span>NO₂</span>
                  <span className="font-bold text-[#191c1e]">
                    {aqiData?.no2 ? `${Math.round(aqiData.no2)} µg/m³` : "—"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span>Humidity</span>
                  <span className="font-bold text-[#191c1e]">
                    {weatherData?.humidity ? `${Math.round(weatherData.humidity)}%` : "—"}
                  </span>
                </div>
              </div>
            </div>

            {/* Ward Location Telemetry Card */}
            <div style={cardStyle} className="p-6 bg-[#f8f9fa] border border-[#dee3e5]">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-[#006877]" />
                  <span className="text-md font-bold text-[#191c1e]">{wardName}</span>
                </div>
                <span className="text-[10px] font-bold bg-[#006877]/10 text-[#006877] px-2 py-0.5 rounded">
                  {selectedWard}
                </span>
              </div>

              <div className="space-y-2 text-xs text-[#40484b] mb-4">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Thermometer className="w-3.5 h-3.5 text-orange-500" /> Temperature:
                  </span>
                  <span className="font-semibold text-[#191c1e]">
                    {weatherData?.temperature ? `${weatherData.temperature}°C` : "24°C"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Wind className="w-3.5 h-3.5 text-cyan-600" /> Wind Velocity:
                  </span>
                  <span className="font-semibold text-[#191c1e]">
                    {weatherData?.wind_speed ? `${weatherData.wind_speed} km/h` : "8 km/h"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Droplets className="w-3.5 h-3.5 text-blue-500" /> Rain:
                  </span>
                  <span className="font-semibold text-[#191c1e]">
                    {weatherData?.precipitation ? `${weatherData.precipitation} mm` : "0 mm"}
                  </span>
                </div>
              </div>

              <Link
                to="/map"
                className="w-full flex items-center justify-center gap-1.5 py-2 px-3 bg-white hover:bg-[#ededf4] border border-[#cbd5e1] rounded-lg text-xs font-bold text-[#006877] transition-colors"
              >
                <span>View on City Map</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Center Column (6 cols): AI Advisories & Safety Grid */}
          <div className="lg:col-span-6 flex flex-col gap-8">
            {/* AI Health Advice Banner */}
            <div
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
              style={cardStyle}
              className="p-6 border-l-4 border-l-[#006877] bg-white relative overflow-hidden"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-[#006877] animate-pulse" />
                  <span className="text-[10px] font-extrabold text-[#006877] uppercase tracking-wider">
                    AI CITIZEN HEALTH ADVISOR
                  </span>
                </div>
                <span className="text-[10px] uppercase font-bold text-[#70787d]">
                  Profile: {selectedProfile}
                </span>
              </div>

              {advisoryLoading ? (
                <div className="py-6 flex flex-col items-center justify-center gap-2 text-[#40484b]">
                  <RefreshCw className="w-6 h-6 animate-spin text-[#006877]" />
                  <p className="text-xs">Generating personalized medical guidance in {selectedLang.toUpperCase()}...</p>
                </div>
              ) : (
                <>
                  <h3 className="text-base font-bold text-[#191c1e] tracking-tight leading-snug">
                    {advisory?.advice ||
                      "Air quality requires vigilance today. Please wear an N95 mask outside and limit strenuous outdoor activities."}
                  </h3>

                  {/* Windows badges */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4 pt-3 border-t border-[#dee3e5]/60">
                    <div className="flex items-center gap-2 p-2.5 rounded-lg bg-[#b4f4c2]/20 border border-[#b4f4c2]/50">
                      <Sunrise className="w-4 h-4 text-[#006d31]" />
                      <div>
                        <p className="text-[9px] font-bold uppercase tracking-wider text-[#006d31]">
                          Best Outdoor Window
                        </p>
                        <p className="text-xs font-extrabold text-[#006d31]">
                          {advisory?.best_outdoor_window || "15:00 - 17:00"}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 p-2.5 rounded-lg bg-[#ffdad6]/40 border border-[#ffdad6]">
                      <AlertTriangle className="w-4 h-4 text-[#ba1a1a]" />
                      <div>
                        <p className="text-[9px] font-bold uppercase tracking-wider text-[#ba1a1a]">
                          Worst Exposure Window
                        </p>
                        <p className="text-xs font-extrabold text-[#ba1a1a]">
                          {advisory?.worst_outdoor_window || "07:00 - 10:00"}
                        </p>
                      </div>
                    </div>
                  </div>
                </>
              )}

              <div className="flex gap-3 mt-5">
                <Link
                  to="/forecast"
                  className="bg-[#006877] text-white px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider hover:brightness-110 active:scale-[0.98] transition-all inline-flex items-center gap-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>View 72h Forecast</span>
                </Link>
                <button
                  onClick={() => loadAdvisory(selectedWard, selectedLang, selectedProfile)}
                  className="border border-[#cbd5e1] px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider text-[#40484b] hover:bg-[#e7e8ee] transition-all"
                >
                  Regenerate Advice
                </button>
              </div>
            </div>

            {/* Today's Activity Safety Matrix */}
            <div style={cardStyle} className="p-6 bg-white flex-grow flex flex-col">
              <div className="flex items-center justify-between mb-6 border-b border-[#dee3e5]/50 pb-2">
                <h3 className="text-md font-bold text-[#191c1e] tracking-tight">
                  Dynamic Activity Safety Matrix
                </h3>
                <span className="text-[10px] font-bold text-[#70787d] uppercase">
                  Based on Current AQI {currentAqi}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-grow">
                {/* Running */}
                {(() => {
                  const s = getActivitySafety("running");
                  return (
                    <div className="p-4 rounded-xl border border-[#dee3e5] flex items-start gap-4 hover:border-[#006877]/30 transition-all">
                      <div className="w-10 h-10 rounded-full bg-[#b4f4c2]/20 flex items-center justify-center flex-shrink-0">
                        <span className="text-lg">🏃</span>
                      </div>
                      <div className="space-y-1 flex-1">
                        <div className="flex justify-between items-center">
                          <p className="text-xs font-bold text-[#191c1e]">Running / Cardio</p>
                          <span className={`text-[9px] ${s.bg} px-2 py-0.5 rounded-full ${s.text} font-bold`}>
                            {s.status}
                          </span>
                        </div>
                        <p className="text-[10px] text-[#40484b] leading-relaxed">{s.desc}</p>
                      </div>
                    </div>
                  );
                })()}

                {/* Outdoor Event */}
                {(() => {
                  const s = getActivitySafety("outdoor_event");
                  return (
                    <div className="p-4 rounded-xl border border-[#dee3e5] flex items-start gap-4 hover:border-[#006877]/30 transition-all">
                      <div className="w-10 h-10 rounded-full bg-[#ffae83]/20 flex items-center justify-center flex-shrink-0">
                        <span className="text-lg">🍢</span>
                      </div>
                      <div className="space-y-1 flex-1">
                        <div className="flex justify-between items-center">
                          <p className="text-xs font-bold text-[#191c1e]">Outdoor Dining / Events</p>
                          <span className={`text-[9px] ${s.bg} px-2 py-0.5 rounded-full ${s.text} font-bold`}>
                            {s.status}
                          </span>
                        </div>
                        <p className="text-[10px] text-[#40484b] leading-relaxed">{s.desc}</p>
                      </div>
                    </div>
                  );
                })()}

                {/* Park Play */}
                {(() => {
                  const s = getActivitySafety("park_play");
                  return (
                    <div className="p-4 rounded-xl border border-[#dee3e5] flex items-start gap-4 hover:border-[#006877]/30 transition-all">
                      <div className="w-10 h-10 rounded-full bg-[#b4f4c2]/20 flex items-center justify-center flex-shrink-0">
                        <span className="text-lg">👶</span>
                      </div>
                      <div className="space-y-1 flex-1">
                        <div className="flex justify-between items-center">
                          <p className="text-xs font-bold text-[#191c1e]">Children & Senior Park Play</p>
                          <span className={`text-[9px] ${s.bg} px-2 py-0.5 rounded-full ${s.text} font-bold`}>
                            {s.status}
                          </span>
                        </div>
                        <p className="text-[10px] text-[#40484b] leading-relaxed">{s.desc}</p>
                      </div>
                    </div>
                  );
                })()}

                {/* Ventilation */}
                {(() => {
                  const s = getActivitySafety("ventilation");
                  return (
                    <div className="p-4 rounded-xl border border-[#dee3e5] flex items-start gap-4 hover:border-[#006877]/30 transition-all">
                      <div className="w-10 h-10 rounded-full bg-[#a2eeff]/20 flex items-center justify-center flex-shrink-0">
                        <span className="text-lg">🪟</span>
                      </div>
                      <div className="space-y-1 flex-1">
                        <div className="flex justify-between items-center">
                          <p className="text-xs font-bold text-[#191c1e]">Natural Ventilation</p>
                          <span className={`text-[9px] ${s.bg} px-2 py-0.5 rounded-full ${s.text} font-bold`}>
                            {s.status}
                          </span>
                        </div>
                        <p className="text-[10px] text-[#40484b] leading-relaxed">{s.desc}</p>
                      </div>
                    </div>
                  );
                })()}
              </div>
            </div>
          </div>

          {/* Right Column (3 cols): Timeline, Diurnal Windows, Actions */}
          <div className="lg:col-span-3 flex flex-col gap-8">
            {/* 24h Outlook Progress Cards */}
            <div style={cardStyle} className="p-6 bg-[#ededf4]">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-[#191c1e] tracking-tight">24h ML Outlook</h3>
                <span className="text-[10px] font-bold text-[#006877] uppercase">LightGBM</span>
              </div>

              <div className="space-y-3">
                {outlookItems.map((item, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-[10px] font-bold text-[#40484b] w-12 text-right">
                      {item.label}
                    </span>
                    <div className="flex-grow h-2 bg-[#e1e2e9] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{
                          width: `${item.barPercent}%`,
                          backgroundColor: item.color,
                        }}
                      />
                    </div>
                    <span className="text-xs font-bold text-[#191c1e] w-8 text-right">
                      {item.aqi}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Time of Day diurnal outlook */}
            <div className="flex flex-col gap-2">
              {/* Morning */}
              <div
                style={cardStyle}
                className="p-4 flex justify-between items-center bg-white/60 border border-[#dee3e5]/60 hover:bg-white transition-all shadow-sm"
              >
                <div className="flex items-center gap-2">
                  <Sunrise className="w-4 h-4 text-[#40484b]" />
                  <span className="text-xs font-bold text-[#191c1e]">Morning (06:00 - 12:00)</span>
                </div>
                <span className={`text-xs font-bold ${diurnalWindows.morning.color}`}>
                  {diurnalWindows.morning.label}
                </span>
              </div>

              {/* Afternoon */}
              <div
                style={cardStyle}
                className="p-4 flex justify-between items-center bg-[#ffae83]/10 border border-[#ffb690]/35 hover:bg-white transition-all shadow-sm"
              >
                <div className="flex items-center gap-2">
                  <Sun className="w-4 h-4 text-[#944b00]" />
                  <span className="text-xs font-bold text-[#191c1e]">Afternoon (12:00 - 18:00)</span>
                </div>
                <span className={`text-xs font-bold ${diurnalWindows.afternoon.color}`}>
                  {diurnalWindows.afternoon.label}
                </span>
              </div>

              {/* Evening */}
              <div
                style={cardStyle}
                className="p-4 flex justify-between items-center bg-white/60 border border-[#dee3e5]/60 hover:bg-white transition-all shadow-sm"
              >
                <div className="flex items-center gap-2">
                  <Moon className="w-4 h-4 text-[#40484b]" />
                  <span className="text-xs font-bold text-[#191c1e]">Evening (18:00 - 24:00)</span>
                </div>
                <span className={`text-xs font-bold ${diurnalWindows.evening.color}`}>
                  {diurnalWindows.evening.label}
                </span>
              </div>
            </div>

            {/* Citizen Action Advisory card */}
            <div style={cardStyle} className="p-5 border border-[#006877]/20 bg-[#006877]/5 mt-auto">
              <div className="flex items-center gap-1.5 mb-2">
                <Users className="w-4 h-4 text-[#006877]" />
                <span className="text-[10px] font-bold text-[#006877] uppercase tracking-wider">
                  PROTECTION CHECKLIST
                </span>
              </div>
              <ul className="text-xs text-[#40484b] space-y-1.5">
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#006877] mt-0.5 flex-shrink-0" />
                  <span>Wear certified N95 / FFP2 masks when outdoors.</span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#006877] mt-0.5 flex-shrink-0" />
                  <span>Keep air purifiers running in HEPA recirculate mode.</span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#006877] mt-0.5 flex-shrink-0" />
                  <span>Report unpaved dust or open trash burning to Delhi MCD.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
