import React, { useState, useEffect, useCallback } from "react";
import {
  getWards,
  getHeatmap,
  getAQI,
  getWeather,
  getRecommend,
  getPredict,
  getSourceAttribution,
} from "../api/client";
import HeatMap from "../components/HeatMap";
import OverlayToggle, { OverlayMode } from "../components/OverlayToggle";
import Legend from "../components/Legend";
import WardDrawer from "../components/WardDrawer";

export default function PollutionMap() {
  // Central State Management
  // Starts empty and is set to the first ward the API actually returns. Hardcoding an
  // id here (it used to be "W02") breaks against the real 290-ward Delhi dataset, whose
  // ids look like "CANT_1" / "NDMC_1" — every ward-detail call 500s on a ward that
  // doesn't exist.
  const [wardId, setWardId] = useState<string | null>(null);
  const [overlayMode, setOverlayMode] = useState<OverlayMode>("current");

  // Global Datasets
  const [wardsGeoJson, setWardsGeoJson] = useState<any | null>(null);
  const [heatmapData, setHeatmapData] = useState<any[] | null>(null);
  const [predictionsMap, setPredictionsMap] = useState<Record<string, any>>({});
  const [sourcesMap, setSourcesMap] = useState<Record<string, any>>({});

  // Ward-specific Detail Datasets
  const [selectedAqiData, setSelectedAqiData] = useState<any | null>(null);
  const [selectedWeatherData, setSelectedWeatherData] = useState<any | null>(null);
  const [selectedRecommendations, setSelectedRecommendations] = useState<any | null>(null);
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

      // Select the first real ward so the detail panel has something valid to show.
      const firstWardId = wardsRes?.features?.[0]?.properties?.ward_id;
      if (firstWardId) {
        setWardId((current) => current ?? firstWardId);
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
      setSelectedRecommendations(null);
      setSelectedAttributionData(null);
      setSelectedForecastData(null);
      return;
    }

    const fetchWardDetails = async () => {
      try {
        setWardLoading(true);
        // Load details, weather, recommendations, forecasts, and attributions for the specific ward
        const [aqi, weather, recommend, predictVal, sourceVal] = await Promise.all([
          getAQI(wardId),
          getWeather(wardId),
          getRecommend(wardId),
          getPredict(wardId, 24),
          getSourceAttribution(wardId),
        ]);

        setSelectedAqiData(aqi);
        setSelectedWeatherData(weather);
        setSelectedRecommendations(recommend);
        setSelectedForecastData(predictVal);
        setSelectedAttributionData(sourceVal);

        // Also cache into the overlay maps so the "Predicted" / "Dominant Source" map colours
        // for this ward become accurate once it's been visited, without ever bulk-fetching
        // all 290 wards at once.
        setPredictionsMap((prev) => ({ ...prev, [wardId]: predictVal }));
        setSourcesMap((prev) => ({ ...prev, [wardId]: sourceVal }));
      } catch (err) {
        console.error(`Error loading details for ward ${wardId}:`, err);
      } finally {
        setWardLoading(false);
      }
    };

    fetchWardDetails();
  }, [wardId]);

  // Callback to update selected ward
  const handleSelectWard = useCallback((id: string | null) => {
    setWardId(id);
  }, []);

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
                  : "94.2%"}
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
          recommendations={selectedRecommendations}
          attributionData={selectedAttributionData}
          forecastData={selectedForecastData}
          loading={wardLoading}
        />
      </div>
    </div>
  );
}
