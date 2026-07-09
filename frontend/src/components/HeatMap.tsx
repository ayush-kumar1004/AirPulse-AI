import React from "react";
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

// Stitch color palette helper for AQI
const getAqiColor = (aqi: number) => {
  if (aqi <= 50) return "#22C55E";       // Good
  if (aqi <= 100) return "#EAB308";      // Moderate
  if (aqi <= 150) return "#F97316";      // Poor
  if (aqi <= 200) return "#EF4444";      // Very Poor
  return "#7F1D1D";                      // Severe
};

// Fallback values for the 3 Delhi wards from Stitch design
const fallbackWardsData: Record<string, { name: string; aqi: number; source: string; defaultColor: string }> = {
  W01: { name: "Dwarka", aqi: 52, source: "dust", defaultColor: "#22C55E" },
  W02: { name: "Rohini", aqi: 241, source: "traffic", defaultColor: "#7F1D1D" },
  W03: { name: "Central", aqi: 156, source: "construction", defaultColor: "#F97316" },
};

export default function HeatMap({
  onSelectWard,
  selectedWardId = "W02",
  overlayMode = "current",
  heatmapData = [],
  predictionsMap = {},
  sourcesMap = {},
}: HeatMapProps) {
  // Exactly the 3 Delhi Wards from the approved Stitch reference screen
  const wardPolygons = [
    {
      id: "W02",
      name: "Rohini",
      d: "M200,150 L450,100 L550,350 L350,450 Z",
      labelX: 350,
      labelY: 250,
    },
    {
      id: "W03",
      name: "Central",
      d: "M450,100 L750,150 L850,400 L550,350 Z",
      labelX: 600,
      labelY: 250,
    },
    {
      id: "W01",
      name: "Dwarka",
      d: "M350,450 L550,350 L850,400 L700,750 L400,700 Z",
      labelX: 550,
      labelY: 550,
    },
  ];

  // Resolve fill and stroke styles dynamically based on overlays and selected state
  const getStyleForWard = (wardId: string) => {
    const isSelected = selectedWardId === wardId;
    const fallback = fallbackWardsData[wardId];
    
    let fillColor = fallback.defaultColor;
    let strokeColor = fallback.defaultColor;

    // 1. Resolve colors based on active Overlay Mode
    if (overlayMode === "current") {
      const realData = heatmapData?.find((h) => h.ward_id === wardId);
      const aqi = realData ? realData.aqi : fallback.aqi;
      fillColor = getAqiColor(aqi);
      strokeColor = fillColor;
    } else if (overlayMode === "predicted") {
      const realData = predictionsMap?.[wardId];
      if (realData && realData.points && realData.points.length > 0) {
        const aqi = realData.points[realData.points.length - 1].predicted_aqi;
        fillColor = getAqiColor(aqi);
      } else {
        fillColor = getAqiColor(fallback.aqi + 15);
      }
      strokeColor = fillColor;
    } else if (overlayMode === "source") {
      const realData = sourcesMap?.[wardId];
      let dominant = fallback.source;
      if (realData) {
        const sources = [
          { name: "traffic", val: realData.traffic },
          { name: "construction", val: realData.construction },
          { name: "industry", val: realData.industry },
          { name: "dust", val: realData.dust },
        ];
        sources.sort((a, b) => b.val - a.val);
        dominant = sources[0].name;
      }

      if (dominant === "traffic") fillColor = "#22d3ee";
      else if (dominant === "construction") fillColor = "#f97316";
      else if (dominant === "industry") fillColor = "#a855f7";
      else fillColor = "#78350f";
      
      strokeColor = fillColor;
    }

    // Selected state overrides border stroke
    if (isSelected) {
      strokeColor = "#22d3ee";
    }

    return {
      fill: fillColor,
      fillOpacity: isSelected ? 0.55 : 0.25,
      stroke: strokeColor,
      strokeWidth: isSelected ? 3.0 : 2.0,
    };
  };

  return (
    <div className="w-full h-full relative bg-[#0f172a] overflow-hidden flex items-center justify-center">
      {/* Grid background matching Stitch */}
      <div className="absolute inset-0 opacity-20 pointer-events-none z-0">
        <div className="w-full h-full bg-[radial-gradient(#334155_1px,transparent_1px)] [background-size:24px_24px]"></div>
      </div>

      {/* SVG Map Layout */}
      <svg
        className="absolute inset-0 w-full h-full z-10"
        viewBox="0 0 1000 800"
        preserveAspectRatio="xMidYMid slice"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Ward Polygons */}
        {wardPolygons.map((ward) => {
          const styles = getStyleForWard(ward.id);
          return (
            <g key={ward.id}>
              <path
                d={ward.d}
                className="transition-all duration-300 cursor-pointer hover:fill-opacity-50"
                fill={styles.fill}
                fillOpacity={styles.fillOpacity}
                stroke={styles.stroke}
                strokeWidth={styles.strokeWidth}
                onClick={() => onSelectWard(ward.id)}
              />
              <text
                x={ward.labelX}
                y={ward.labelY}
                className="fill-[#8aebff] font-extrabold text-[14px] pointer-events-none select-none tracking-widest uppercase"
                textAnchor="middle"
                fontFamily="Inter"
              >
                {ward.name}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Monitoring Station Markers floating on top */}
      <div className="absolute top-[20%] left-[30%] z-20 group cursor-pointer">
        <div className="w-4 h-4 bg-[#22D3EE] rounded-full shadow-[0_0_15px_#22D3EE] animate-pulse"></div>
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block bg-[#171f33] border border-[#22d3ee]/20 p-2 rounded-lg backdrop-blur-xl">
          <p className="text-[10px] text-[#22D3EE] font-bold whitespace-nowrap">STATION HQ-01</p>
          <p className="text-[10px] text-[#bbc9cd]">98% AI Confidence</p>
        </div>
      </div>

      <div className="absolute top-[45%] left-[65%] z-20 group cursor-pointer">
        <div className="w-4 h-4 bg-[#22D3EE] rounded-full shadow-[0_0_15px_#22D3EE] animate-pulse"></div>
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block bg-[#171f33] border border-[#22d3ee]/20 p-2 rounded-lg backdrop-blur-xl">
          <p className="text-[10px] text-[#22D3EE] font-bold whitespace-nowrap">STATION CN-04</p>
          <p className="text-[10px] text-[#bbc9cd]">92% AI Confidence</p>
        </div>
      </div>
    </div>
  );
}
