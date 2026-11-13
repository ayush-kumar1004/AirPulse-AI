import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import {
  getWards,
  getHeatmap,
  getAQI,
  getWeather,
  getPredict,
  getSourceAttribution,
} from "../api/client";
import HeatMap from "../components/HeatMap";
import OverlayToggle, { OverlayMode } from "../components/OverlayToggle";
import Legend from "../components/Legend";
import WardDrawer from "../components/WardDrawer";

// Degrees → 16-point compass label ("315" → "NW").
const toCompass = (deg: number | null | undefined): string | null => {
  if (deg === null || deg === undefined || Number.isNaN(deg)) return null;
  const dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
  return dirs[Math.round(((deg % 360) + 360) % 360 / 22.5) % 16];
};

// The backend's WeatherResponse uses different field names than WardDrawer
// (temperature/wind_speed/wind_direction/precipitation vs temp_c/wind_kph/
// wind_dir/rain_mm). Without this mapping every weather field rendered "—"
// even when the API call succeeded.
const adaptWeather = (w: any) =>
  w
    ? {
        temp_c: w.temperature ?? null,
        humidity: w.humidity ?? null,
        wind_kph: w.wind_speed ?? null,
        wind_dir: toCompass(w.wind_direction),
        rain_mm: w.precipitation ?? null,
      }
    : null;

export default function PollutionMap() {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlWard = searchParams.get("ward");

  // Central State Management
  const [wardId, setWardId] = useState<string | null>(urlWard || null);
  const [overlayMode, setOverlayMode] = useState<OverlayMode>("current");

  // Global Datasets
  const [wardsGeoJson, setWardsGeoJson] = useState<any | null>(null);
  const [heatmapData, setHeatmapData] = useState<any[] | null>(null);
  const [predictionsMap, setPredictionsMap] = useState<Record<string, any>>({});
  const [sourcesMap, setSourcesMap] = useState<Record<string, any>>({});

  // Ward-specific Detail Datasets
  const [selectedAqiData, setSelectedAqiData] = useState<any | null>(null);
  const [selectedWeatherData, setSelectedWeatherData] = useState<any | null>(null);
  const [selectedAttributionData, setSelectedAttributionData] = useState<any | null>(null);
  const [selectedForecastData, setSelectedForecastData] = useState<any | null>(null);

  // Loading & Error States
  const [initialLoading, setInitialLoading] = useState(true);
  const [wardLoading, setWardLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initial fetch of global datasets — ONLY wards + heatmap (2 lightweight, cached calls).
  // NOTE: we deliberately do NOT bulk-fetch /api/predict + /api/source-attribution for every
  // ward here. Doing that for all 290 wards fires 580 parallel requests on page load, which
  // overwhelms the backend and trips Open-Meteo's rate limit (503s) — see diagnostic_report.md.
  // Predicted/source overlay colours are instead filled in incrementally as the user selects
  // wards (see fetchWardDetails below); HeatMap.tsx already falls back to a neutral colour for
  // any ward not yet visited.
  const fetchGlobalData = useCallback(async () => {
    try {
      setInitialLoading(true);
      setError(null);

      const [wardsRes, heatmapRes] = await Promise.all([getWards(), getHeatmap()]);

      setWardsGeoJson(wardsRes);
      setHeatmapData(heatmapRes);

      // Select requested ward from query param or the first real ward
      const targetWard = searchParams.get("ward") || wardsRes?.features?.[0]?.properties?.ward_id;
      if (targetWard) {
        setWardId((current) => current ?? targetWard);
      }
    } catch (err: any) {
      console.error("Error loading environmental map data:", err);
      setError("Failed to fetch Delhi air quality data. Please check connection and retry.");
    } finally {
      setInitialLoading(false);
    }
  }, []);

  // Fetch global map data on mount
  useEffect(() => {
    fetchGlobalData();
  }, [fetchGlobalData]);

  // Fetch ward-specific detail datasets in parallel when selected ward changes (Promise.all)
  useEffect(() => {
    if (!wardId) {
      setSelectedAqiData(null);
      setSelectedWeatherData(null);
      setSelectedAttributionData(null);
      setSelectedForecastData(null);
      return;
    }

    const fetchWardDetails = async () => {
      setWardLoading(true);
      // allSettled, not all: these endpoints fail independently, and one failure
      // must not throw away the datasets that DID load. With Promise.all a
      // single rejection blanked the entire drawer to "unavailable".
      //
      // getRecommend is deliberately NOT called here. It runs an LLM, WardDrawer
      // never rendered its result, and the free Gemini tier allows only 20
      // requests a day — so every ward click was silently burning quota on a
      // response that went straight in the bin.
      const [aqi, weather, predictVal, sourceVal] = await Promise.allSettled([
        getAQI(wardId),
        getWeather(wardId),
        getPredict(wardId, 24),
        getSourceAttribution(wardId),
      ]).then((results) =>
        results.map((r, i) => {
          if (r.status === "rejected") {
            console.error(`Ward ${wardId} detail call ${i} failed:`, r.reason);
            return null;
          }
          return r.value;
        })
      );

      setSelectedAqiData(aqi);
      setSelectedWeatherData(adaptWeather(weather));
      setSelectedForecastData(predictVal);
      setSelectedAttributionData(sourceVal);

      // Also cache into the overlay maps so the "Predicted" / "Dominant Source" map colours
      // for this ward become accurate once it's been visited, without ever bulk-fetching
      // all 290 wards at once.
      if (predictVal) setPredictionsMap((prev) => ({ ...prev, [wardId]: predictVal }));
      if (sourceVal) setSourcesMap((prev) => ({ ...prev, [wardId]: sourceVal }));
      setWardLoading(false);
    };

    fetchWardDetails();
  }, [wardId]);

  // Callback to update selected ward
  const handleSelectWard = useCallback((id: string | null) => {
    setWardId(id);
    if (id) {
      setSearchParams({ ward: id }, { replace: true });
    }
  }, [setSearchParams]);

  // Callback to update active overlay mode
  const handleOverlayChange = useCallback((mode: OverlayMode) => {
    setOverlayMode(mode);
  }, []);



  return (
    <div className="w-full h-full flex flex-row overflow-hidden text-white font-sans bg-[#0F172A]">
      {/* Left: Map Container (occupies remaining width) */}
      <div className="relative flex-1 h-full bg-[#0F172A] overflow-hidden">
        {/* Floating Controls Overlay */}
        <div className="absolute top-6 left-6 z-20">
          <OverlayToggle activeMode={overlayMode} onChange={handleOverlayChange} />
        </div>

        {/* Floating AI Confidence Badge */}
        <div className="absolute top-6 right-6 z-20">
          <div className="bg-[#1E293B]/80 backdrop-blur-xl border border-[#3c494c]/40 rounded-xl px-4 py-2 flex items-center gap-3 shadow-lg">
            <div className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#22D3EE] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#22D3EE]"></span>
            </div>
            <div>
              <p className="text-[10px] font-bold text-[#22D3EE] uppercase tracking-wider">AI Confidence</p>
              <p className="text-sm font-extrabold text-[#F8FAFC]">
                {wardId && sourcesMap[wardId]?.confidence !== undefined
                  ? `${(sourcesMap[wardId].confidence * 100).toFixed(1)}%`
                  : "—"}
              </p>
            </div>
          </div>
        </div>

        {/* Map Presentation Layer */}
        <div className="w-full h-full">
          <HeatMap
            onSelectWard={handleSelectWard}
            selectedWardId={wardId}
            overlayMode={overlayMode}
            wardsGeoJson={wardsGeoJson}
            heatmapData={heatmapData || []}
            predictionsMap={predictionsMap}
            sourcesMap={sourcesMap}
          />
        </div>

        {/* Floating Legend Overlay */}
        <div className="absolute bottom-6 left-6 z-20">
          <Legend activeMode={overlayMode} />
        </div>
      </div>

      {/* Right: Ward Detail drawer (approx. 30% width / fixed w-80) */}
      <div className="w-80 h-full border-l border-[#3c494c]/40 bg-[#1E293B] overflow-hidden flex flex-col z-20">
        <WardDrawer
          wardId={wardId}
          aqiData={selectedAqiData}
          weatherData={selectedWeatherData}
          attributionData={selectedAttributionData}
          forecastData={selectedForecastData}
          loading={wardLoading}
        />
      </div>
    </div>
  );
}
