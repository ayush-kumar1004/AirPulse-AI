// TODO: Person D — Selected-ward summary card: AQI, category, PM2.5/PM10, weather, recommendations.
// Data via getAQI, getWeather, getRecommend.
export default function WardPanel({ wardId }: { wardId: string | null }) {
  if (!wardId) return <div className="rounded border p-4 text-slate-500">Select a ward on the map.</div>;
  // TODO: Person D — fetch + render ward detail
  return <div className="rounded border p-4">TODO: Person D — Ward panel for {wardId}</div>;
}
