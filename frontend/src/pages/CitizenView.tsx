// TODO: Person D — Citizen View. Location + profile + language selector, calls CitizenAdvisor.
import CitizenAdvisor from "../components/CitizenAdvisor";

export default function CitizenView() {
  return (
    <div className="mx-auto max-w-2xl p-4">
      <h1 className="mb-4 text-xl font-bold">Citizen Health Advisor</h1>
      <CitizenAdvisor />
    </div>
  );
}
