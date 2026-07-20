import React, { useRef, useEffect, useCallback, useMemo, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { OverlayMode } from "./OverlayToggle";

export interface HeatMapProps {
  onSelectWard: (wardId: string | null) => void;
  selectedWardId?: string | null;
  overlayMode?: OverlayMode;
  wardsGeoJson?: any;
  heatmapData?: any[];
  predictionsMap?: Record<string, any>;
  sourcesMap?: Record<string, any>;
}

// ── Colour helpers (unchanged from original) ──────────────────────────
const getAqiColor = (aqi: number): string => {
  if (aqi <= 50) return "#22C55E";   // Good
  if (aqi <= 100) return "#EAB308";  // Moderate
  if (aqi <= 150) return "#F97316";  // Poor
  if (aqi <= 200) return "#EF4444";  // Very Poor
  return "#7F1D1D";                  // Severe
};

const getSourceColor = (dominant: string): string => {
  if (dominant === "traffic") return "#22d3ee";
  if (dominant === "construction") return "#f97316";
  if (dominant === "industry") return "#a855f7";
  return "#78350f"; // dust / default
};

// ── Compute centroid of a GeoJSON polygon ─────────────────────────────
function computeCentroid(coordinates: number[][][]): [number, number] {
  const ring = coordinates[0]; // outer ring
  let sumLng = 0;
  let sumLat = 0;
  // Exclude the closing vertex (same as first)
  const len = ring.length > 1 ? ring.length - 1 : ring.length;
  for (let i = 0; i < len; i++) {
    sumLng += ring[i][0];
    sumLat += ring[i][1];
  }
  return [sumLng / len, sumLat / len];
}

// ── Build a point FeatureCollection for labels from ward polygons ─────
function buildLabelPoints(geoJson: any): GeoJSON.FeatureCollection {
  const features = (geoJson?.features || []).map((f: any) => {
    const centroid = computeCentroid(f.geometry.coordinates);
    return {
      type: "Feature" as const,
      properties: { ...f.properties },
      geometry: { type: "Point" as const, coordinates: centroid },
    };
  });
  return { type: "FeatureCollection", features };
}

// ── Resolve fill colour for a single ward ─────────────────────────────
function resolveWardColor(
  wardId: string,
  overlayMode: OverlayMode,
  heatmapData: any[],
  predictionsMap: Record<string, any>,
  sourcesMap: Record<string, any>
): string {
  if (overlayMode === "current") {
    const entry = heatmapData?.find((h) => h.ward_id === wardId);
    return getAqiColor(entry?.aqi ?? 150);
  }

  if (overlayMode === "predicted") {
    const pred = predictionsMap?.[wardId];
    if (pred?.points?.length) {
      return getAqiColor(pred.points[pred.points.length - 1].predicted_aqi);
    }
    return getAqiColor(150);
  }

  // source mode
  const src = sourcesMap?.[wardId];
  if (src) {
    const sources = [
      { name: "traffic", val: src.traffic },
      { name: "construction", val: src.construction },
      { name: "industry", val: src.industry },
      { name: "dust", val: src.dust },
    ];
    sources.sort((a, b) => b.val - a.val);
    return getSourceColor(sources[0].name);
  }
  return getSourceColor("dust");
}

// ── Build MapLibre data-driven fill-color expression ──────────────────
function buildFillColorExpression(
  geoJson: any,
  overlayMode: OverlayMode,
  heatmapData: any[],
  predictionsMap: Record<string, any>,
  sourcesMap: Record<string, any>
): maplibregl.ExpressionSpecification {
  const features = geoJson?.features || [];
  const cases: (string | maplibregl.ExpressionSpecification)[] = [];

  for (const f of features) {
    const wid = f.properties.ward_id;
    const color = resolveWardColor(wid, overlayMode, heatmapData, predictionsMap, sourcesMap);
    cases.push(wid, color);
  }

  return ["match", ["get", "ward_id"], ...cases, "#334155"] as any;
}

// ── Map style ─────────────────────────────────────────────────────────
const DARK_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";
const DELHI_CENTER: [number, number] = [77.18, 28.68];
const DEFAULT_ZOOM = 10.5;

// ── Layer IDs ─────────────────────────────────────────────────────────
const SRC_WARDS = "wards-source";
const SRC_LABELS = "wards-labels-source";
const LYR_FILL = "wards-fill";
const LYR_LINE = "wards-line";
const LYR_SELECTED = "wards-selected-line";
const LYR_LABELS = "wards-labels";

// ══════════════════════════════════════════════════════════════════════
// Component
// ══════════════════════════════════════════════════════════════════════
const HeatMap = React.memo(function HeatMap({
  onSelectWard,
  selectedWardId = null,
  overlayMode = "current",
  wardsGeoJson,
  heatmapData = [],
  predictionsMap = {},
  sourcesMap = {},
}: HeatMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const hoveredWardRef = useRef<string | null>(null);
  const [mapReady, setMapReady] = useState(false);

  // ── Colour expression ────────────────────────────────────────────
  const fillColorExpr = useMemo(() => {
    if (!wardsGeoJson?.features?.length) return null;
    return buildFillColorExpression(wardsGeoJson, overlayMode, heatmapData, predictionsMap, sourcesMap);
  }, [wardsGeoJson, overlayMode, heatmapData, predictionsMap, sourcesMap]);

  // ── Initialize map (once) ────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: DARK_STYLE,
      center: DELHI_CENTER,
      zoom: DEFAULT_ZOOM,
      attributionControl: false,
      maxZoom: 16,
      minZoom: 8,
    });

    // Add minimal attribution bottom-right
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
    // Navigation controls
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    map.on("load", () => {
      setMapReady(true);
    });

    mapRef.current = map;

    return () => {
      mapRef.current = null;
      map.remove();
    };
  }, []);

  // ── Add / update sources and layers when GeoJSON arrives ─────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !wardsGeoJson?.features?.length) return;

    // If source already exists, just update data
    const existingSource = map.getSource(SRC_WARDS) as maplibregl.GeoJSONSource | undefined;
    if (existingSource) {
      existingSource.setData(wardsGeoJson);
      // Also update labels
      const labelSource = map.getSource(SRC_LABELS) as maplibregl.GeoJSONSource | undefined;
      labelSource?.setData(buildLabelPoints(wardsGeoJson));
      return;
    }

    // ── Add ward polygon source ────────────────────────────────────
    map.addSource(SRC_WARDS, {
      type: "geojson",
      data: wardsGeoJson,
      promoteId: "ward_id",
    });

    // ── Fill layer ─────────────────────────────────────────────────
    map.addLayer({
      id: LYR_FILL,
      type: "fill",
      source: SRC_WARDS,
      paint: {
        "fill-color": fillColorExpr || "#334155",
        "fill-opacity": [
          "case",
          ["boolean", ["feature-state", "hover"], false],
          0.55,
          0.3,
        ],
      },
    });

    // ── Default border line ────────────────────────────────────────
    map.addLayer({
      id: LYR_LINE,
      type: "line",
      source: SRC_WARDS,
      paint: {
        "line-color": [
          "case",
          ["boolean", ["feature-state", "hover"], false],
          "#8aebff",
          "#475569",
        ],
        "line-width": 1.5,
        "line-opacity": 0.8,
      },
    });

    // ── Selected ward highlight line ───────────────────────────────
    map.addLayer({
      id: LYR_SELECTED,
      type: "line",
      source: SRC_WARDS,
      paint: {
        "line-color": "#22d3ee",
        "line-width": 3,
        "line-opacity": 1,
      },
      filter: selectedWardId
        ? ["==", ["get", "ward_id"], selectedWardId]
        : ["==", ["get", "ward_id"], ""],
    });

    // ── Label points source & layer ────────────────────────────────
    map.addSource(SRC_LABELS, {
      type: "geojson",
      data: buildLabelPoints(wardsGeoJson),
    });

    map.addLayer({
      id: LYR_LABELS,
      type: "symbol",
      source: SRC_LABELS,
      layout: {
        "text-field": ["get", "ward_name"],
        "text-font": ["Open Sans Bold"],
        "text-size": 12,
        "text-transform": "uppercase",
        "text-letter-spacing": 0.15,
        "text-allow-overlap": false,
        "text-ignore-placement": false,
      },
      paint: {
        "text-color": "#8aebff",
        "text-halo-color": "rgba(15, 23, 42, 0.85)",
        "text-halo-width": 2,
      },
    });

    // ── Hover interaction ──────────────────────────────────────────
    map.on("mousemove", LYR_FILL, (e) => {
      if (!e.features?.length) return;
      const wid = e.features[0].properties?.ward_id;
      if (hoveredWardRef.current && hoveredWardRef.current !== wid) {
        map.setFeatureState({ source: SRC_WARDS, id: hoveredWardRef.current }, { hover: false });
      }
      if (wid) {
        hoveredWardRef.current = wid;
        map.setFeatureState({ source: SRC_WARDS, id: wid }, { hover: true });
        map.getCanvas().style.cursor = "pointer";
      }
    });

    map.on("mouseleave", LYR_FILL, () => {
      if (hoveredWardRef.current) {
        map.setFeatureState({ source: SRC_WARDS, id: hoveredWardRef.current }, { hover: false });
        hoveredWardRef.current = null;
      }
      map.getCanvas().style.cursor = "";
    });

    // ── Click interaction ──────────────────────────────────────────
    map.on("click", LYR_FILL, (e) => {
      if (!e.features?.length) return;
      const wid = e.features[0].properties?.ward_id;
      if (wid) onSelectWard(wid);
    });

    // ── Fit bounds to GeoJSON ──────────────────────────────────────
    try {
      const bounds = new maplibregl.LngLatBounds();
      for (const f of wardsGeoJson.features) {
        for (const ring of f.geometry.coordinates) {
          for (const coord of ring) {
            bounds.extend(coord as [number, number]);
          }
        }
      }
      map.fitBounds(bounds, { padding: 60, maxZoom: 13, duration: 800 });
    } catch {
      // fallback — stay at default center/zoom
    }
  }, [mapReady, wardsGeoJson]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Update fill colours when overlay data changes ────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !fillColorExpr) return;
    if (!map.getLayer(LYR_FILL)) return;

    map.setPaintProperty(LYR_FILL, "fill-color", fillColorExpr);
  }, [fillColorExpr, mapReady]);

  // ── Update selected ward filter ──────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;
    if (!map.getLayer(LYR_SELECTED)) return;

    map.setFilter(
      LYR_SELECTED,
      selectedWardId
        ? ["==", ["get", "ward_id"], selectedWardId]
        : ["==", ["get", "ward_id"], ""]
    );

    // Also boost opacity on selected ward fill
    if (map.getLayer(LYR_FILL)) {
      map.setPaintProperty(LYR_FILL, "fill-opacity", [
        "case",
        ["==", ["get", "ward_id"], selectedWardId || ""],
        0.55,
        ["boolean", ["feature-state", "hover"], false],
        0.5,
        0.3,
      ]);
    }
  }, [selectedWardId, mapReady]);

  // ── Resize observer for responsive container ─────────────────────
  useEffect(() => {
    const map = mapRef.current;
    const container = containerRef.current;
    if (!map || !container) return;

    const observer = new ResizeObserver(() => {
      map.resize();
    });
    observer.observe(container);

    return () => observer.disconnect();
  }, []);

  return (
    <div className="w-full h-full relative bg-[#0f172a] overflow-hidden">
      {/* MapLibre container */}
      <div ref={containerRef} className="absolute inset-0 w-full h-full" />

      {/* Loading state while GeoJSON hasn't arrived */}
      {!wardsGeoJson && (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-[#0f172a]/80 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-[#22D3EE] border-t-transparent rounded-full animate-spin" />
            <p className="text-xs font-bold text-[#94A3B8] uppercase tracking-widest">
              Loading ward data…
            </p>
          </div>
        </div>
      )}
    </div>
  );
});

export default HeatMap;
