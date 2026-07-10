import React from "react";
import { NavLink, Outlet, Link } from "react-router-dom";
import {
  LayoutDashboard,
  Map,
  Compass,
  Gavel,
  User,
  PlusCircle,
  HelpCircle,
  LogOut,
  Search,
  Bell,
  Settings,
  Building,
} from "lucide-react";
import ParticleBackground from "./ParticleBackground";
import logo from "../assets/airpulse-logo.svg";

export default function DashboardShell() {
  // Stitch Cyan primary theme colors for active/inactive links
  const activeLinkClass =
    "flex items-center gap-3 bg-[#22D3EE]/10 text-[#22D3EE] border-l-4 border-[#22D3EE] px-4 py-3 transition-all font-semibold font-body-md";
  const inactiveLinkClass =
    "flex items-center gap-3 text-[#bbc9cd] px-4 py-3 hover:bg-[#1E293B] hover:text-white rounded-lg transition-all active:translate-x-1 font-body-md";

  return (
    <div className="min-h-screen bg-[#0b1326] text-[#dae2fd] font-sans flex flex-col relative overflow-hidden">
      {/* Ambient background glows and particles */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.08] z-0">
        <ParticleBackground />
      </div>
      <div className="fixed inset-0 pointer-events-none opacity-20 bg-[radial-gradient(circle_at_70%_30%,#22d3ee22,transparent_60%)] z-0" />

      {/* TopNavBar */}
      <header className="fixed top-0 w-full z-50 flex justify-between items-center px-6 h-16 bg-[#0b1326]/80 backdrop-blur-xl border-b border-[#3c494c]/40">
        {/* Left: Branding */}
        <div className="flex items-center gap-2.5">
          <img
            alt="AirPulse AI Logo"
            className="h-8 w-8 object-contain"
            src={logo}
          />
          <span className="text-xl font-bold text-[#22D3EE] tracking-tight">AirPulse AI</span>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-4">
          <div className="relative hidden sm:block">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#bbc9cd] w-4 h-4" />
            <input
              className="bg-[#131b2e] border border-[#3c494c]/40 rounded-full pl-10 pr-4 py-1.5 text-sm focus:ring-1 focus:ring-[#22D3EE] outline-none transition-all w-48 focus:w-64 text-white"
              placeholder="Search ward..."
              type="text"
            />
          </div>
          <button className="p-2 text-[#bbc9cd] hover:text-[#22D3EE] hover:bg-[#1E293B] transition-colors rounded-full focus:outline-none">
            <Bell className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* SideNavBar */}
      <aside className="hidden md:flex flex-col fixed left-0 top-16 bottom-0 w-[280px] z-40 bg-[#0b1326] border-r border-[#3c494c]/40 p-6 justify-between">
        <div className="space-y-6">
          {/* Location Headquarters Banner */}
          <div className="flex items-center gap-3 px-2 py-2 bg-[#1E293B]/40 rounded-lg border border-[#3c494c]/20">
            <div className="w-9 h-9 rounded-lg bg-[#22D3EE]/10 flex items-center justify-center border border-[#22D3EE]/20">
              <Building className="w-5 h-5 text-[#22D3EE]" />
            </div>
            <div>
              <p className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">Delhi HQ</p>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#4ae176]" />
                <p className="text-[10px] font-semibold text-[#bbc9cd]/60">Live Monitoring</p>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            <NavLink
              to="/"
              end
              className={({ isActive }) => (isActive ? activeLinkClass : inactiveLinkClass)}
            >
              <LayoutDashboard className="w-5 h-5" />
              <span className="text-sm">Dashboard</span>
            </NavLink>
            <NavLink
              to="/map"
              className={({ isActive }) => (isActive ? activeLinkClass : inactiveLinkClass)}
            >
              <Map className="w-5 h-5" />
              <span className="text-sm">Map View</span>
            </NavLink>
            <NavLink
              to="/forecast"
              className={({ isActive }) => (isActive ? activeLinkClass : inactiveLinkClass)}
            >
              <Compass className="w-5 h-5" />
              <span className="text-sm">AI Forecasts</span>
            </NavLink>
            <NavLink
              to="/government"
              className={({ isActive }) => (isActive ? activeLinkClass : inactiveLinkClass)}
            >
              <Gavel className="w-5 h-5" />
              <span className="text-sm">Command Center</span>
            </NavLink>
            <NavLink
              to="/citizen"
              className={({ isActive }) => (isActive ? activeLinkClass : inactiveLinkClass)}
            >
              <User className="w-5 h-5" />
              <span className="text-sm">Citizen View</span>
            </NavLink>
          </nav>
        </div>

        {/* Generate Report Button, Settings & Help */}
        <div className="space-y-4">
          <Link
            to="/report"
            className="w-full bg-[#22D3EE] text-[#001f25] font-semibold py-3 rounded-xl hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(34,211,238,0.3)]"
          >
            <PlusCircle className="w-5 h-5" />
            <span className="text-xs uppercase tracking-wider font-bold">Generate Report</span>
          </Link>
          <div className="space-y-1">
            <NavLink
              to="/support"
              className={({ isActive }) =>
                isActive
                  ? "flex items-center gap-3 bg-[#22D3EE]/10 text-[#22D3EE] border-l-4 border-[#22D3EE] px-4 py-2 text-xs font-semibold uppercase tracking-wider transition-all"
                  : "flex items-center gap-3 text-[#bbc9cd]/60 px-4 py-2 hover:text-[#22D3EE] text-xs font-semibold uppercase tracking-wider transition-all"
              }
            >
              <HelpCircle className="w-4 h-4" />
              <span>Support</span>
            </NavLink>
            <a
              className="flex items-center gap-3 text-[#bbc9cd]/60 px-4 py-2 hover:text-[#22D3EE] text-xs font-semibold uppercase tracking-wider transition-colors"
              href="#settings"
            >
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </a>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="fixed left-0 md:left-[280px] right-0 top-16 bottom-12 flex flex-col z-30 overflow-hidden bg-[#0F172A]">
        <Outlet />
      </main>

      {/* Fixed Footer */}
      <footer className="fixed bottom-0 w-full h-12 px-6 flex justify-between items-center bg-[#0b1326] border-t border-[#3c494c]/20 z-50 text-[10px] font-semibold text-[#bbc9cd]/40 tracking-wider uppercase">
        <span>© 2026 AirPulse AI • Urban Environmental Intelligence</span>
        <div className="flex gap-4">
          <a className="hover:text-[#22D3EE] transition-colors" href="#privacy">
            Privacy Policy
          </a>
          <a className="hover:text-[#22D3EE] transition-colors" href="#terms">
            Terms of Service
          </a>
          <a className="hover:text-[#22D3EE] transition-colors" href="#status">
            API Status
          </a>
        </div>
      </footer>
    </div>
  );
}
