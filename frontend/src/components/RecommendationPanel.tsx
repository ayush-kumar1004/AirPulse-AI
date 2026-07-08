// TODO: Person D — Government action list + inspection priority table. Data via getRecommend(wardId).
// Render each action as {action, target, urgency, reason}; urgency drives the colour chip.
export default function RecommendationPanel({ wardId }: { wardId: string | null }) {
  if (!wardId) return null;
  // TODO: Person D — fetch getRecommend(wardId); render actions[] + inspection_priority[]
  return <div className="rounded border p-4">TODO: Person D — Recommendations + inspection list for {wardId}</div>;
}
