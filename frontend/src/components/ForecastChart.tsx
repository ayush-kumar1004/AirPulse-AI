// TODO: Person D — 24/48/72h AQI forecast line chart (recharts). Data via getPredict(wardId, horizon).
export default function ForecastChart({ wardId }: { wardId: string | null }) {
  if (!wardId) return null;
  // TODO: Person D — recharts LineChart with confidence band (lower/upper)
  return <div className="rounded border p-4">TODO: Person D — Forecast chart for {wardId}</div>;
}
