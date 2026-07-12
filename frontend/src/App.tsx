// Root component + routes for the 5 screens (DOCX Section 5). Owner: Person D.
import { Route, Routes } from "react-router-dom";
import CitizenView from "./pages/CitizenView";
import CityDashboard from "./pages/CityDashboard";
import ForecastScreen from "./pages/ForecastScreen";
import GovernmentDashboard from "./pages/GovernmentDashboard";
import PollutionMap from "./pages/PollutionMap";
import SupportCenter from "./pages/SupportCenter";
import Report from "./pages/Report";
import SplashController from "./components/SplashController";
import DashboardShell from "./components/DashboardShell";

export default function App() {
  return (
    <SplashController>
      <Routes>
        <Route element={<DashboardShell />}>
          <Route path="/" element={<CityDashboard />} />
          <Route path="/map" element={<PollutionMap />} />
          <Route path="/forecast" element={<ForecastScreen />} />
          <Route path="/government" element={<GovernmentDashboard />} />
          <Route path="/citizen" element={<CitizenView />} />
          <Route path="/support" element={<SupportCenter />} />
          <Route path="/report" element={<Report />} />
        </Route>
      </Routes>
    </SplashController>
  );
}
