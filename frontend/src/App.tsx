// Root component + routes for the 5 screens (DOCX Section 5). Owner: Person D.
import { NavLink, Route, Routes } from "react-router-dom";
import CitizenView from "./pages/CitizenView";
import CityDashboard from "./pages/CityDashboard";
import ForecastScreen from "./pages/ForecastScreen";
import GovernmentDashboard from "./pages/GovernmentDashboard";
import PollutionMap from "./pages/PollutionMap";
import SplashController from "./components/SplashController";

const link = "hover:underline";
const active = "underline font-semibold";

export default function App() {
  return (
    <SplashController>
      <div className="min-h-screen">
        <nav className="flex flex-wrap gap-4 bg-slate-900 px-6 py-3 text-white">
          <span className="font-bold">AirPulse AI</span>
          <NavLink to="/" end className={({ isActive }) => (isActive ? active : link)}>City Dashboard</NavLink>
          <NavLink to="/map" className={({ isActive }) => (isActive ? active : link)}>Pollution Map</NavLink>
          <NavLink to="/forecast" className={({ isActive }) => (isActive ? active : link)}>Forecast</NavLink>
          <NavLink to="/government" className={({ isActive }) => (isActive ? active : link)}>Government</NavLink>
          <NavLink to="/citizen" className={({ isActive }) => (isActive ? active : link)}>Citizen</NavLink>
        </nav>
        <Routes>
          <Route path="/" element={<CityDashboard />} />
          <Route path="/map" element={<PollutionMap />} />
          <Route path="/forecast" element={<ForecastScreen />} />
          <Route path="/government" element={<GovernmentDashboard />} />
          <Route path="/citizen" element={<CitizenView />} />
        </Routes>
      </div>
    </SplashController>
  );
}
