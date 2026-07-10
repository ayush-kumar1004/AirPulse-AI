// TODO: Person D — Interactive ward heat map (Leaflet — no key needed — or Mapbox GL for polish).
// Colour wards green→yellow→red→dark-red on CPCB categories. Load polygons via getWards(),
// colours via getHeatmap(); onSelectWard(wardId) on click opens the side panel.
import { getHeatmap, getWards } from "../api/client";

export default function HeatMap({ onSelectWard }: { onSelectWard: (wardId: string) => void }) {
  // TODO: Person D — render map; useEffect(() => { getWards(); getHeatmap(); }, [])
  void getWards;
  void getHeatmap;
  return (
    <div
      className="flex h-[500px] items-center justify-center rounded border bg-slate-100 text-slate-500"
      onClick={() => onSelectWard("W01")}
    >
      TODO: Person D — Pollution Heat Map (click to select ward)
    </div>
  );
}
