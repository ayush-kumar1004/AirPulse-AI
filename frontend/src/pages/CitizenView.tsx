import React from "react";
import { MapPin, Sparkles, Activity, ShieldCheck, Sun, Moon, Sunrise, Users, Plus } from "lucide-react";

export default function CitizenView() {
  // Card hover animation style configurations
  const cardStyle = {
    backgroundColor: "#ffffff",
    border: "1px solid #dee3e5",
    borderRadius: "1rem",
    boxShadow: "0 4px 20px -2px rgba(0, 0, 0, 0.05)",
    transition: "transform 0.3s ease-out, box-shadow 0.3s ease-out",
  };

  const handleMouseEnter = (e: React.MouseEvent<HTMLDivElement>) => {
    e.currentTarget.style.transform = "translateY(-2px)";
    e.currentTarget.style.boxShadow = "0 8px 24px -2px rgba(0, 0, 0, 0.08)";
  };

  const handleMouseLeave = (e: React.MouseEvent<HTMLDivElement>) => {
    e.currentTarget.style.transform = "translateY(0)";
    e.currentTarget.style.boxShadow = "0 4px 20px -2px rgba(0, 0, 0, 0.05)";
  };

  // SVG circular progress calculation for AQI 52 (Moderate)
  const aqiVal = 52;
  const progressPercent = Math.min(100, (aqiVal / 500) * 100);
  const strokeDashoffset = 282.7 - (282.7 * progressPercent) / 100;

  return (
    <div className="flex-1 w-full h-full overflow-y-auto p-6 md:p-8 space-y-8 bg-[#fdfcff] text-[#191c1e] font-sans pb-24">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Hero Header Section */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
          <div>
            <h1 className="text-3xl font-extrabold text-[#191c1e] tracking-tight">Hello, Sarah</h1>
            <p className="text-sm text-[#40484b] mt-1">Here is your personalized health outlook for Greater Kailash, Delhi.</p>
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-[#b4f4c2]/20 border border-[#b4f4c2]/40 rounded-full">
              <ShieldCheck className="w-4 h-4 text-[#006d31]" />
              <span className="text-[10px] font-bold text-[#006d31] uppercase tracking-wider">ASTHMA FRIENDLY</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-[#a2eeff]/25 border border-[#a2eeff]/40 rounded-full">
              <Activity className="w-4 h-4 text-[#006877]" />
              <span className="text-[10px] font-bold text-[#006877] uppercase tracking-wider">DAILY JOGGER</span>
            </div>
            <button className="p-1.5 rounded-full border border-[#cbd5e1] hover:bg-[#e7e8ee] transition-colors active:scale-95">
              <Plus className="w-4 h-4 text-[#40484b]" />
            </button>
          </div>
        </header>

        {/* Bento Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column (3 cols): AQI Focus & Location Map */}
          <div className="lg:col-span-3 flex flex-col gap-8">
            {/* Current AQI Gauge Card */}
            <div
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
              style={cardStyle}
              className="p-6 flex flex-col items-center text-center relative overflow-hidden bg-white"
            >
              {/* Radial gradient background from Stitch */}
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(180,244,194,0.3)_0%,transparent_70%)] pointer-events-none" />
              
              <p className="text-[10px] font-bold text-[#40484b] tracking-widest uppercase mb-6 relative z-10">CURRENT AQI</p>
              
              <div className="relative w-48 h-48 flex items-center justify-center mb-6 z-10">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" fill="none" r="45" stroke="#e1e2e9" strokeWidth="7" />
                  <circle
                    cx="50"
                    cy="50"
                    fill="none"
                    r="45"
                    stroke="#00b954"
                    strokeDasharray="282.7"
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    strokeWidth="7"
                    className="transition-all duration-1000"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-5xl font-extrabold text-[#006d31] tracking-tight">{aqiVal}</span>
                  <span className="text-[10px] font-bold text-[#006d31] tracking-wider uppercase mt-0.5">MODERATE</span>
                </div>
              </div>

              {/* AQI Breakdown Parameters */}
              <div className="w-full flex flex-col gap-2 relative z-10 border-t border-[#dee3e5]/50 pt-4 text-xs font-medium text-[#40484b]">
                <div className="flex justify-between items-center py-1 border-b border-[#dee3e5]/20">
                  <span>PM 2.5</span>
                  <span className="font-bold text-[#191c1e]">12 µg/m³</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-[#dee3e5]/20">
                  <span>NO₂</span>
                  <span className="font-bold text-[#191c1e]">45 ppb</span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span>Humidity</span>
                  <span className="font-bold text-[#191c1e]">62%</span>
                </div>
              </div>
            </div>

            {/* Location Map Card */}
            <div style={cardStyle} className="p-6 bg-[#ededf4] border border-[#bfc8ca]/40">
              <div className="flex items-center gap-2 mb-4">
                <MapPin className="w-5 h-5 text-[#006877]" />
                <span className="text-md font-bold text-[#191c1e]">Greater Kailash</span>
              </div>
              <div className="w-full h-40 rounded-lg overflow-hidden border border-[#bfc8ca]/30 cursor-pointer group">
                <img
                  className="w-full h-full object-cover grayscale opacity-85 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-300"
                  alt="Greater Kailash neighborhood layout map"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuCJdvGR0G8Ph6GbACHEEroMtuXFlrRks6j-p6-9huXiavBNAQilJejMaA3OCZHwzN2J6rXWnUhcZlPo1WHHhWceWva8g20n3SEeGcfiwn5MfslwWVpEoXa2TMtXIFdyrGxgY755NFf7tCY5crBQBE3IaH5PlI9IyGq4vm_7YUGfC3hxF5-VP4asUiEs0KOKyMOuZT8noMbad-n03jOn3kt6nN3XwjinLsBkDbk92Ybtd2DR_ZBCJw2_F8e7JtrIyYQ3zIZYPesgGqeN"
                />
              </div>
            </div>
          </div>

          {/* Center Column (6 cols): AI Advisories & Safety Grid */}
          <div className="lg:col-span-6 flex flex-col gap-8">
            
            {/* AI Health Advice Banner */}
            <div
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
              style={cardStyle}
              className="p-6 border-l-4 border-l-[#006877] bg-white relative overflow-hidden"
            >
              <div className="flex items-center gap-1.5 mb-3">
                <div className="w-2 h-2 rounded-full bg-[#006877] animate-pulse"></div>
                <span className="text-[10px] font-bold text-[#006877] uppercase tracking-wider">AI HEALTH GUIDANCE</span>
              </div>
              <h3 className="text-lg font-bold text-[#191c1e] tracking-tight">
                Air quality is declining slightly in the next 2 hours.
              </h3>
              <p className="text-xs text-[#40484b] leading-relaxed mt-2">
                Based on your Asthma profile, we recommend shifting your outdoor workout to 4:00 PM when ozone levels are predicted to hit the day's minimum. Keep your inhaler handy for the morning commute.
              </p>
              <div className="flex gap-3 mt-6">
                <button className="bg-[#006877] text-white px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider hover:brightness-110 active:scale-[0.98] transition-all">
                  VIEW PLAN
                </button>
                <button className="border border-[#cbd5e1] px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider text-[#40484b] hover:bg-[#e7e8ee] transition-all">
                  DISMISS
                </button>
              </div>
            </div>

            {/* Today's Activity Safety Grid */}
            <div style={cardStyle} className="p-6 bg-white flex-grow flex flex-col">
              <h3 className="text-md font-bold text-[#191c1e] mb-6 tracking-tight border-b border-[#dee3e5]/50 pb-2">
                Today's Activity Safety
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-grow">
                {/* Running */}
                <div className="p-4 rounded-xl border border-[#dee3e5] flex items-start gap-4 hover:border-[#006877]/30 transition-all">
                  <div className="w-10 h-10 rounded-full bg-[#b4f4c2]/20 flex items-center justify-center flex-shrink-0">
                    <span className="text-lg">🏃</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between items-center gap-4">
                      <p className="text-xs font-bold text-[#191c1e]">Running</p>
                      <span className="text-[9px] bg-[#b4f4c2] px-2 py-0.5 rounded-full text-[#002109] font-bold">SAFE</span>
                    </div>
                    <p className="text-[10px] text-[#40484b] leading-relaxed">Best before 10 AM or after 5 PM.</p>
                  </div>
                </div>

                {/* Outdoor Event */}
                <div className="p-4 rounded-xl border border-[#dee3e5] flex items-start gap-4 opacity-75 hover:opacity-100 transition-all">
                  <div className="w-10 h-10 rounded-full bg-[#ffae83]/20 flex items-center justify-center flex-shrink-0">
                    <span className="text-lg">🍢</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between items-center gap-4">
                      <p className="text-xs font-bold text-[#191c1e]">Outdoor Event</p>
                      <span className="text-[9px] bg-[#ffae83] px-2 py-0.5 rounded-full text-[#4a2300] font-bold">CAUTION</span>
                    </div>
                    <p className="text-[10px] text-[#40484b] leading-relaxed">Avoid prolonged exposure between 1-3 PM.</p>
                  </div>
                </div>

                {/* Park Play */}
                <div className="p-4 rounded-xl border border-[#dee3e5] flex items-start gap-4 hover:border-[#006877]/30 transition-all">
                  <div className="w-10 h-10 rounded-full bg-[#b4f4c2]/20 flex items-center justify-center flex-shrink-0">
                    <span className="text-lg">👶</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between items-center gap-4">
                      <p className="text-xs font-bold text-[#191c1e]">Park Play</p>
                      <span className="text-[9px] bg-[#b4f4c2] px-2 py-0.5 rounded-full text-[#002109] font-bold">SAFE</span>
                    </div>
                    <p className="text-[10px] text-[#40484b] leading-relaxed">Conditions optimal for children today.</p>
                  </div>
                </div>

                {/* Ventilation */}
                <div className="p-4 rounded-xl border border-[#dee3e5] flex items-start gap-4 hover:border-[#006877]/30 transition-all">
                  <div className="w-10 h-10 rounded-full bg-[#a2eeff]/20 flex items-center justify-center flex-shrink-0">
                    <span className="text-lg">🪟</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between items-center gap-4">
                      <p className="text-xs font-bold text-[#191c1e]">Ventilation</p>
                      <span className="text-[9px] bg-[#b4f4c2] px-2 py-0.5 rounded-full text-[#002109] font-bold">GOOD</span>
                    </div>
                    <p className="text-[10px] text-[#40484b] leading-relaxed">Safe to open windows for 1 hour.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column (3 cols): Timeline, Timecards, Buzz */}
          <div className="lg:col-span-3 flex flex-col gap-8">
            
            {/* 24h Outlook Progress Cards */}
            <div style={cardStyle} className="p-6 bg-[#ededf4]">
              <h3 className="text-sm font-bold text-[#191c1e] mb-4 tracking-tight">24h Outlook</h3>
              <div className="space-y-3">
                {/* NOW */}
                <div className="flex items-center gap-3">
                  <span className="text-[9px] font-bold text-[#40484b] w-10 text-right">NOW</span>
                  <div className="flex-grow h-2 bg-[#e1e2e9] rounded-full overflow-hidden">
                    <div className="h-full bg-[#00b954] w-[54%]" />
                  </div>
                  <span className="text-xs font-bold text-[#191c1e] w-6 text-right">54</span>
                </div>
                {/* 14:00 */}
                <div className="flex items-center gap-3">
                  <span className="text-[9px] font-bold text-[#40484b] w-10 text-right">14:00</span>
                  <div className="flex-grow h-2 bg-[#e1e2e9] rounded-full overflow-hidden">
                    <div className="h-full bg-[#ffae83] w-[78%]" />
                  </div>
                  <span className="text-xs font-bold text-[#191c1e] w-6 text-right">78</span>
                </div>
                {/* 18:00 */}
                <div className="flex items-center gap-3">
                  <span className="text-[9px] font-bold text-[#40484b] w-10 text-right">18:00</span>
                  <div className="flex-grow h-2 bg-[#e1e2e9] rounded-full overflow-hidden">
                    <div className="h-full bg-[#00b954] w-[42%]" />
                  </div>
                  <span className="text-xs font-bold text-[#191c1e] w-6 text-right">42</span>
                </div>
                {/* 22:00 */}
                <div className="flex items-center gap-3">
                  <span className="text-[9px] font-bold text-[#40484b] w-10 text-right">22:00</span>
                  <div className="flex-grow h-2 bg-[#e1e2e9] rounded-full overflow-hidden">
                    <div className="h-full bg-[#00b954] w-[35%]" />
                  </div>
                  <span className="text-xs font-bold text-[#191c1e] w-6 text-right">35</span>
                </div>
              </div>
            </div>

            {/* Time of Day lists */}
            <div className="flex flex-col gap-2">
              {/* Morning */}
              <div style={cardStyle} className="p-4 flex justify-between items-center bg-white/40 border border-[#dee3e5]/60 hover:bg-white transition-all shadow-sm">
                <div className="flex items-center gap-2">
                  <Sunrise className="w-4 h-4 text-[#40484b]" />
                  <span className="text-xs font-bold text-[#191c1e]">Morning</span>
                </div>
                <span className="text-xs font-bold text-green-600">Fresh</span>
              </div>
              {/* Afternoon */}
              <div style={cardStyle} className="p-4 flex justify-between items-center bg-[#ffae83]/10 border border-[#ffb690]/35 hover:bg-white transition-all shadow-sm">
                <div className="flex items-center gap-2">
                  <Sun className="w-4 h-4 text-[#944b00]" />
                  <span className="text-xs font-bold text-[#191c1e]">Afternoon</span>
                </div>
                <span className="text-xs font-bold text-[#944b00]">Hazy</span>
              </div>
              {/* Evening */}
              <div style={cardStyle} className="p-4 flex justify-between items-center bg-white/40 border border-[#dee3e5]/60 hover:bg-white transition-all shadow-sm">
                <div className="flex items-center gap-2">
                  <Moon className="w-4 h-4 text-[#40484b]" />
                  <span className="text-xs font-bold text-[#191c1e]">Evening</span>
                </div>
                <span className="text-xs font-bold text-green-600">Clear</span>
              </div>
            </div>

            {/* Community Buzz advisory card */}
            <div style={cardStyle} className="p-5 border border-[#0d9488]/20 bg-[#0d9488]/5 mt-auto">
              <div className="flex items-center gap-1.5 mb-2">
                <Users className="w-4 h-4 text-[#0d9488]" />
                <span className="text-[10px] font-bold text-[#0d9488] uppercase tracking-wider">COMMUNITY BUZZ</span>
              </div>
              <p className="text-[10px] text-[#40484b] leading-relaxed">
                84 people from your neighborhood are active in the park right now.
              </p>
            </div>

          </div>

        </div>

      </div>
    </div>
  );
}
