// TODO: Person D — Screen 2 "Pollution Map": full interactive ward map + overlay toggle
// (current AQI / predicted +24h / dominant source). Modules 1, 4. Click ward -> side panel.
import { useState } from "react";
import ForecastChart from "../components/ForecastChart";
import HeatMap from "../components/HeatMap";
import SourceBreakdown from "../components/SourceBreakdown";
import WardPanel from "../components/WardPanel";

export default function PollutionMap() {
  const [ward, setWard] = useState<string | null>(null);
  return (
    <div className="grid grid-cols-1 gap-4 p-4 lg:grid-cols-3">
      <div className="lg:col-span-2">
        {/* TODO: Person D — overlay toggle: current AQI | predicted +24h | dominant source */}
        <HeatMap onSelectWard={setWard} />
      </div>
      <div className="space-y-4">
        <WardPanel wardId={ward} />
        <SourceBreakdown wardId={ward} />
        <ForecastChart wardId={ward} />
      </div>
    </div>
  );
}
