// TODO: Person D — Screen 1 "City Dashboard": current AQI, predicted AQI, trend chart, mini heatmap.
// Modules 1, 2, 4. Data via getHeatmap, getAQI, getPredict.
import ForecastChart from "../components/ForecastChart";
import HeatMap from "../components/HeatMap";

export default function CityDashboard() {
  // TODO: Person D — city-level summary cards (avg AQI, worst ward) + mini heatmap + trend
  return (
    <div className="grid grid-cols-1 gap-4 p-4 lg:grid-cols-2">
      <HeatMap onSelectWard={() => {}} />
      <ForecastChart wardId="W01" />
    </div>
  );
}
