// TODO: Person D — Source attribution donut/bars (traffic/construction/industry/dust) + confidence.
// Data via getSourceAttribution(wardId). Show the model's `reasoning` text too (transparency is the selling point).
export default function SourceBreakdown({ wardId }: { wardId: string | null }) {
  if (!wardId) return null;
  // TODO: Person D — render % breakdown + confidence + explanation
  return <div className="rounded border p-4">TODO: Person D — Source breakdown for {wardId}</div>;
}
