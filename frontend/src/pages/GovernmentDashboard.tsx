// TODO: Person D — Screen 4 "Government Dashboard": recommended interventions, inspection priority
// list, officer chat. Modules 1, 2, 3. Data via getRecommend + officerChat.
import { useState } from "react";
import OfficerChat from "../components/OfficerChat";
import RecommendationPanel from "../components/RecommendationPanel";

export default function GovernmentDashboard() {
  const [ward] = useState("W01");
  return (
    <div className="grid grid-cols-1 gap-4 p-4 lg:grid-cols-2">
      <RecommendationPanel wardId={ward} />
      <OfficerChat wardId={ward} />
    </div>
  );
}
