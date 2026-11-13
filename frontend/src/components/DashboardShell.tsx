import React, { useState, useEffect, useRef } from "react";
import { NavLink, Outlet, Link, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Map,
  Compass,
  Gavel,
  User,
  PlusCircle,
  HelpCircle,
  Search,
  Bell,
  Settings,
  Building,
  X,
  CheckCircle2,
  AlertTriangle,
  Sliders,
} from "lucide-react";
import ParticleBackground from "./ParticleBackground";
import logo from "../assets/airpulse-logo.png";
import { getWards } from "../api/client";

interface WardItem {
  id: string;
  name: string;
}

export default function DashboardShell() {
  const navigate = useNavigate();
  const [allWards, setAllWards] = useState<WardItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<WardItem[]>([]);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);

  // Load wards for global search
  useEffect(() => {
    let mounted = true;
    getWards()
      .then((res: any) => {
        if (!mounted) return;
        const features = res?.features ?? [];
        const mapped = features
          .map((f: any) => ({
            id: f.properties?.ward_id ?? f.properties?.id ?? f.id,
            name: f.properties?.ward_name ?? f.properties?.Ward_Name ?? f.properties?.name ?? `Ward ${f.properties?.ward_id ?? ""}`,
          }))
          .filter((w: WardItem) => Boolean(w.id));
        setAllWards(mapped);
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  // Filter search results
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setIsSearchOpen(false);
      return;
    }
    const q = searchQuery.toLowerCase().trim();
    const matches = allWards
      .filter((w) => w.name.toLowerCase().includes(q) || w.id.toLowerCase().includes(q))
      .slice(0, 8);
    setSearchResults(matches);
    setIsSearchOpen(true);
  }, [searchQuery, allWards]);

  // Click outside to close search dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setIsSearchOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelectWard = (wardId: string) => {
    setIsSearchOpen(false);
    setSearchQuery("");
    navigate(`/map?ward=${wardId}`);
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && searchResults.length > 0) {
      handleSelectWard(searchResults[0].id);
    }
  };

  // Cyan primary theme colors for active/inactive links
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
        <Link to="/" className="flex items-center gap-2.5 cursor-pointer">
          <img
            alt="AirPulse AI Logo"
            className="h-8 w-8 object-contain"
            src={logo}
          />
          <span className="text-xl font-bold text-[#22D3EE] tracking-tight">AirPulse AI</span>
        </Link>

        {/* Right: Actions */}
        <div className="flex items-center gap-4">
          <div ref={searchRef} className="relative hidden sm:block">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#bbc9cd] w-4 h-4 pointer-events-none" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              onFocus={() => searchQuery.trim() && setIsSearchOpen(true)}
              className="bg-[#131b2e] border border-[#3c494c]/40 rounded-full pl-10 pr-4 py-1.5 text-sm focus:ring-1 focus:ring-[#22D3EE] outline-none transition-all w-48 focus:w-72 text-white"
              placeholder="Search ward (e.g. Rohini, Bawana)..."
              type="text"
            />
            {/* Search Autocomplete Dropdown */}
            {isSearchOpen && searchResults.length > 0 && (
              <div className="absolute left-0 right-0 mt-2 bg-[#0f172a] border border-[#334155] rounded-xl shadow-2xl overflow-hidden z-50 max-h-72 overflow-y-auto">
                <div className="px-3 py-1.5 text-[10px] uppercase font-bold text-[#94a3b8] bg-[#1e293b]/50 border-b border-[#334155]">
                  Matching Wards ({searchResults.length})
                </div>
                {searchResults.map((w) => (
                  <button
                    key={w.id}
                    onClick={() => handleSelectWard(w.id)}
                    className="w-full text-left px-3.5 py-2.5 text-xs text-slate-200 hover:bg-[#22D3EE]/15 hover:text-[#22D3EE] transition-colors flex items-center justify-between border-b border-[#334155]/30 last:border-0"
                  >
                    <span className="font-semibold truncate">{w.name}</span>
                    <span className="text-[10px] text-slate-400 font-mono ml-2 uppercase">{w.id}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <button
            onClick={() => setIsNotificationsOpen(true)}
            title="System Notifications"
            className="p-2 text-[#bbc9cd] hover:text-[#22D3EE] hover:bg-[#1E293B] transition-colors rounded-full focus:outline-none relative"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#EF4444] animate-pulse" />
          </button>
        </div>
      </header>

      {/* SideNavBar — bottom-12 prevents overlapping with the 48px fixed footer */}
      <aside className="hidden md:flex flex-col fixed left-0 top-16 bottom-12 w-[280px] z-40 bg-[#0b1326] border-r border-[#3c494c]/40 p-6 justify-between">
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

          {/* Core Navigation Links */}
          <nav className="space-y-1">
            <NavLink
              to="/"
              className={({ isActive }) => (isActive ? activeLinkClass : inactiveLinkClass)}
            >
              <LayoutDashboard className="w-5 h-5" />
              <span>Dashboard</span>
            </NavLink>
            <NavLink
              to="/map"
              className={({ isActive }) => (isActive ? activeLinkClass : inactiveLinkClass)}
            >
              <Map className="w-5 h-5" />
              <span>Map View</span>
            </NavLink>
            <NavLink
              to="/forecast"
              className={({ isActive }) => (isActive ? activeLinkClass : inactiveLinkClass)}
            >
              <Compass className="w-5 h-5" />
              <span>AI Forecasts</span>
            </NavLink>
            <NavLink
              to="/government"
              className={({ isActive }) => (isActive ? activeLinkClass : inactiveLinkClass)}
            >
              <Gavel className="w-5 h-5" />
              <span>Command Center</span>
            </NavLink>
            <NavLink
              to="/citizen"
              className={({ isActive }) => (isActive ? activeLinkClass : inactiveLinkClass)}
            >
              <User className="w-5 h-5" />
              <span>Citizen View</span>
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
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="w-full text-left flex items-center gap-3 text-[#bbc9cd]/60 px-4 py-2 hover:text-[#22D3EE] text-xs font-semibold uppercase tracking-wider transition-colors cursor-pointer"
            >
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </button>
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
          <Link className="hover:text-[#22D3EE] transition-colors" to="/support">
            Privacy Policy
          </Link>
          <Link className="hover:text-[#22D3EE] transition-colors" to="/support">
            Terms of Service
          </Link>
          <Link className="hover:text-[#22D3EE] transition-colors" to="/support">
            API Status
          </Link>
        </div>
      </footer>

      {/* Settings Modal */}
      {isSettingsOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0f172a] border border-[#334155] rounded-2xl w-full max-w-md p-6 shadow-2xl relative">
            <div className="flex items-center justify-between pb-4 border-b border-[#334155]">
              <div className="flex items-center gap-2 text-white font-bold text-lg">
                <Sliders className="w-5 h-5 text-[#22D3EE]" />
                System Settings
              </div>
              <button
                onClick={() => setIsSettingsOpen(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="py-4 space-y-4 text-xs text-slate-300">
              <div>
                <label className="block font-semibold uppercase tracking-wider text-[#94a3b8] mb-1">
                  Air Quality Index Standard
                </label>
                <select className="w-full bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 text-white">
                  <option value="cpcb">Indian CPCB NAQI (Standard for Delhi)</option>
                  <option value="us">US EPA AQI</option>
                </select>
              </div>
              <div>
                <label className="block font-semibold uppercase tracking-wider text-[#94a3b8] mb-1">
                  Telemetry Refresh Rate
                </label>
                <select className="w-full bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 text-white">
                  <option value="300">Every 5 Minutes (Standard)</option>
                  <option value="60">Every 1 Minute (High Precision)</option>
                </select>
              </div>
              <div className="pt-2 flex items-center justify-between text-slate-400">
                <span>Active Monitored City</span>
                <span className="font-bold text-[#22D3EE]">Delhi NCR (290 Wards)</span>
              </div>
            </div>
            <div className="pt-4 border-t border-[#334155] flex justify-end">
              <button
                onClick={() => setIsSettingsOpen(false)}
                className="px-4 py-2 bg-[#22D3EE] text-[#001f25] font-bold rounded-lg hover:brightness-110 text-xs"
              >
                Save & Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Notifications Drawer / Modal */}
      {isNotificationsOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0f172a] border border-[#334155] rounded-2xl w-full max-w-md p-6 shadow-2xl relative">
            <div className="flex items-center justify-between pb-4 border-b border-[#334155]">
              <div className="flex items-center gap-2 text-white font-bold text-lg">
                <Bell className="w-5 h-5 text-[#22D3EE]" />
                Live Environmental Alerts
              </div>
              <button
                onClick={() => setIsNotificationsOpen(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="py-4 space-y-3 text-xs">
              <div className="p-3 bg-red-950/40 border border-red-500/30 rounded-xl flex items-start gap-2.5">
                <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-red-200">Severe AQI Hotspot Warning</p>
                  <p className="text-slate-300 text-[11px] mt-0.5">
                    Bankner & Narela have exceeded AQI 470. Emergency misting deployed under GRAP Stage IV.
                  </p>
                </div>
              </div>
              <div className="p-3 bg-cyan-950/40 border border-cyan-500/30 rounded-xl flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-cyan-200">Wind Direction Steady (NW)</p>
                  <p className="text-slate-300 text-[11px] mt-0.5">
                    Surface wind velocity measured at 10.2 km/h across the Delhi Cantt & Vasant Kunj corridor.
                  </p>
                </div>
              </div>
            </div>
            <div className="pt-2 border-t border-[#334155] flex justify-end">
              <button
                onClick={() => setIsNotificationsOpen(false)}
                className="px-4 py-2 bg-[#1e293b] hover:bg-[#334155] text-white font-semibold rounded-lg text-xs"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
