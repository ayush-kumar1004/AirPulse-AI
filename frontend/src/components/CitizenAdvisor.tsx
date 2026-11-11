import React, { useState, useEffect } from "react";
import { Sparkles, RefreshCw, AlertCircle, Sunrise, AlertTriangle } from "lucide-react";
import { getAdvisory } from "../api/client";

interface CitizenAdvisorProps {
  wardId?: string;
  defaultProfile?: string;
  defaultLang?: string;
}

export default function CitizenAdvisor({
  wardId = "W01",
  defaultProfile = "asthma",
  defaultLang = "en",
}: CitizenAdvisorProps) {
  const [profile, setProfile] = useState(defaultProfile);
  const [lang, setLang] = useState(defaultLang);
  const [loading, setLoading] = useState(false);
  const [advisory, setAdvisory] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchGuidance = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAdvisory(wardId, lang, profile);
      setAdvisory(data);
    } catch (err: any) {
      console.error("Advisory error:", err);
      setError("Failed to generate health advisory. Showing standard guidelines.");
      setAdvisory({
        ward_id: wardId,
        language: lang,
        aqi: 180,
        advice:
          lang === "hi"
            ? "आज वायु गुणवत्ता मध्यम से खराब श्रेणी में है। बाहर जाते समय N95 मास्क पहनें।"
            : "Air quality is moderately poor today. Sensitive individuals should wear an N95 mask outdoors.",
        best_outdoor_window: "15:00-17:00",
        worst_outdoor_window: "07:00-10:00",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGuidance();
  }, [wardId, lang, profile]);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[#006877]" />
          <h4 className="text-sm font-bold text-slate-800">AI Health Guidance</h4>
        </div>
        <button
          onClick={fetchGuidance}
          disabled={loading}
          className="p-1 rounded hover:bg-slate-100 transition-colors"
          title="Refresh Advice"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="flex flex-wrap gap-2 text-xs">
        <select
          value={profile}
          onChange={(e) => setProfile(e.target.value)}
          className="bg-slate-100 rounded-lg px-2 py-1 font-medium text-slate-700 border border-slate-200"
        >
          <option value="general public">General Public</option>
          <option value="asthma">Asthma / Sensitive</option>
          <option value="jogger">Daily Jogger</option>
          <option value="elderly">Elderly / Child</option>
        </select>

        <select
          value={lang}
          onChange={(e) => setLang(e.target.value)}
          className="bg-slate-100 rounded-lg px-2 py-1 font-medium text-slate-700 border border-slate-200"
        >
          <option value="en">English</option>
          <option value="hi">हिन्दी (Hindi)</option>
          <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
          <option value="bn">বাংলা (Bengali)</option>
        </select>
      </div>

      {loading ? (
        <div className="py-4 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
          <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#006877]" />
          <span>Generating AI advice...</span>
        </div>
      ) : advisory ? (
        <div className="space-y-3">
          <p className="text-xs text-slate-700 leading-relaxed font-normal">{advisory.advice}</p>

          <div className="grid grid-cols-2 gap-2 text-[11px] pt-2 border-t border-slate-100">
            <div className="bg-emerald-50 text-emerald-800 p-2 rounded-lg border border-emerald-200">
              <span className="font-bold flex items-center gap-1">
                <Sunrise className="w-3 h-3 text-emerald-600" /> Best Window
              </span>
              <p className="font-extrabold mt-0.5">{advisory.best_outdoor_window || "15:00-17:00"}</p>
            </div>
            <div className="bg-rose-50 text-rose-800 p-2 rounded-lg border border-rose-200">
              <span className="font-bold flex items-center gap-1">
                <AlertTriangle className="w-3 h-3 text-rose-600" /> Worst Window
              </span>
              <p className="font-extrabold mt-0.5">{advisory.worst_outdoor_window || "07:00-10:00"}</p>
            </div>
          </div>
        </div>
      ) : error ? (
        <div className="text-xs text-rose-600 flex items-center gap-1.5">
          <AlertCircle className="w-3.5 h-3.5" />
          <span>{error}</span>
        </div>
      ) : null}
    </div>
  );
}
