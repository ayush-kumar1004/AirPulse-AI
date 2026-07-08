// TODO: Person D — Screen 3 "Forecast": 24/48/72hr charts + trend lines. Module 2. Data via getPredict.
import { useState } from "react";
import ForecastChart from "../components/ForecastChart";

export default function ForecastScreen() {
  const [ward] = useState("W01");
  // TODO: Person D — ward selector + horizon toggle (24/48/72) driving ForecastChart
  return (
    <div className="p-4">
      <h1 className="mb-4 text-xl font-bold">AQI Forecast</h1>
      <ForecastChart wardId={ward} />
    </div>
  );
}
