import React, { useState } from "react";

interface FAQItem {
  question: string;
  answer: string;
}

export default function SupportCenter() {
  // Track open state of FAQ accordions
  const [openFaqs, setOpenFaqs] = useState<Record<number, boolean>>({
    0: false,
    1: false,
    2: false,
    3: false,
    4: false,
  });

  const toggleFaq = (index: number) => {
    setOpenFaqs((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  // Card mouse tracking glow
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    card.style.setProperty("--mouse-x", `${x}px`);
    card.style.setProperty("--mouse-y", `${y}px`);
  };

  const faqItems: FAQItem[] = [
    {
      question: "How is AQI calculated?",
      answer:
        "AirPulse AI uses a weighted blend of local sensor data, satellite imagery, and meteorological models. Our proprietary AI algorithm analyzes PM2.5, PM10, NO2, and CO levels to provide a real-time index compliant with global standards.",
    },
    {
      question: "How often is the forecast updated?",
      answer:
        "Forecasts are re-calculated every 15 minutes as new data streams arrive from our distributed sensor network. High-confidence predictive windows are generated for the next 6, 12, and 24 hours.",
    },
    {
      question: "Why is AI confidence low?",
      answer:
        "Confidence scores typically drop during extreme meteorological shifts or when sensor nodes in a specific locality report conflicting data. The AI flags these periods to prevent inaccurate automated decision-making.",
    },
    {
      question: "How do I generate reports?",
      answer:
        "Use the \"Generate Report\" button in the sidebar or navigate to the Reports tab. You can export historical data in PDF, CSV, or via our secure API endpoint for custom integration.",
    },
    {
      question: "How can I change my city?",
      answer:
        "Administrators can toggle monitored regions within the System Settings. Click your profile avatar to access \"Organization Settings\" and \"Manage Locations.\"",
    },
  ];

  // Placeholder actions
  const handleStartChat = () => {
    alert("Live chat is connecting... Connecting to an AirPulse agent.");
  };

  const handleSendEmail = () => {
    window.location.href = "mailto:support_airpulse.ai@gmail.com?subject=AirPulse%20AI%20Support%20Request";
  };

  return (
    <div className="flex-1 w-full h-full overflow-y-auto p-6 md:p-8 space-y-12 bg-[#0F172A] text-[#dae2fd] font-sans pb-24">
      <div className="max-w-[1200px] mx-auto space-y-12 relative">
        {/* Subtle ambient light top right */}
        <div className="absolute -top-20 -right-20 w-80 h-80 bg-[#8aebff]/5 blur-[120px] rounded-full pointer-events-none" />

        {/* Hero Header */}
        <section className="relative pt-6">
          <div className="relative z-10 space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#4ae176]/10 border border-[#4ae176]/20 mb-2">
              <span className="w-2 h-2 rounded-full bg-[#4ae176] animate-pulse" />
              <span className="text-[11px] font-semibold text-[#4ae176] uppercase tracking-wider">
                Live Support Status: Online • Usually responds within 5 minutes
              </span>
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-[#8aebff] tracking-tight">Support Center</h1>
            <p className="text-base text-[#bbc9cd] max-w-2xl leading-relaxed">
              Get help, report issues, and contact the AirPulse AI support team. We're here to ensure your urban environmental data monitoring is seamless and accurate.
            </p>
          </div>
        </section>

        {/* Quick Help Cards Grid */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1: Documentation */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl hover:-translate-y-1 hover:shadow-[0_0_20px_rgba(138,235,255,0.15)] transition-all duration-300 cursor-pointer group bg-[#1E293B]/50 border border-[#334155]/50 backdrop-blur-md relative overflow-hidden border-l-4 border-l-[#8aebff]/30"
            style={{
              background:
                "radial-gradient(300px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(138, 235, 255, 0.06), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <div className="w-12 h-12 rounded-lg bg-[#8aebff]/10 flex items-center justify-center mb-6 group-hover:bg-[#8aebff]/20 transition-colors">
              <span className="material-symbols-outlined text-[#8aebff] text-2xl">book</span>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Documentation</h3>
            <p className="text-xs text-[#bbc9cd] leading-relaxed">
              Read product documentation and user guides.
            </p>
          </div>

          {/* Card 2: Report an Issue */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl hover:-translate-y-1 hover:shadow-[0_0_20px_rgba(255,180,171,0.15)] transition-all duration-300 cursor-pointer group bg-[#1E293B]/50 border border-[#334155]/50 backdrop-blur-md relative overflow-hidden border-l-4 border-l-[#ffb4ab]/30"
            style={{
              background:
                "radial-gradient(300px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(255, 180, 171, 0.06), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <div className="w-12 h-12 rounded-lg bg-[#ffb4ab]/10 flex items-center justify-center mb-6 group-hover:bg-[#ffb4ab]/20 transition-colors">
              <span className="material-symbols-outlined text-[#ffb4ab] text-2xl">bug_report</span>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Report an Issue</h3>
            <p className="text-xs text-[#bbc9cd] leading-relaxed">
              Report bugs or incorrect AQI predictions.
            </p>
          </div>

          {/* Card 3: Contact Support */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl hover:-translate-y-1 hover:shadow-[0_0_20px_rgba(138,235,255,0.15)] transition-all duration-300 cursor-pointer group bg-[#1E293B]/50 border border-[#334155]/50 backdrop-blur-md relative overflow-hidden border-l-4 border-l-[#8aebff]/30"
            style={{
              background:
                "radial-gradient(300px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(138, 235, 255, 0.06), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <div className="w-12 h-12 rounded-lg bg-[#8aebff]/10 flex items-center justify-center mb-6 group-hover:bg-[#8aebff]/20 transition-colors">
              <span className="material-symbols-outlined text-[#8aebff] text-2xl">headset_mic</span>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Contact Support</h3>
            <p className="text-xs text-[#bbc9cd] leading-relaxed">
              Chat or email the AirPulse AI support team.
            </p>
          </div>

          {/* Card 4: System Status */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl hover:-translate-y-1 hover:shadow-[0_0_20px_rgba(74,225,118,0.15)] transition-all duration-300 cursor-pointer group bg-[#1E293B]/50 border border-[#334155]/50 backdrop-blur-md relative overflow-hidden border-l-4 border-l-[#4ae176]/30"
            style={{
              background:
                "radial-gradient(300px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(74, 225, 118, 0.06), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <div className="w-12 h-12 rounded-lg bg-[#4ae176]/10 flex items-center justify-center mb-6 group-hover:bg-[#4ae176]/20 transition-colors">
              <span className="material-symbols-outlined text-[#4ae176] text-2xl">analytics</span>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">System Status</h3>
            <p className="text-xs text-[#bbc9cd] leading-relaxed">
              View backend health, API availability, and AI services.
            </p>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="space-y-6">
          <h2 className="text-xl md:text-2xl font-bold text-[#8aebff] flex items-center gap-2">
            <span className="material-symbols-outlined text-2xl text-[#8aebff]">quiz</span> Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            {faqItems.map((faq, index) => {
              const isOpen = openFaqs[index];
              return (
                <div
                  key={index}
                  className="rounded-xl overflow-hidden bg-[#1E293B]/50 border border-[#334155]/50 backdrop-blur-md transition-all duration-300"
                >
                  <div
                    onClick={() => toggleFaq(index)}
                    className="p-6 cursor-pointer flex justify-between items-center hover:bg-[#222a3d] transition-colors"
                  >
                    <span className="text-base font-semibold text-white">{faq.question}</span>
                    <span
                      className={`material-symbols-outlined text-[#bbc9cd] transition-transform duration-300 ${
                        isOpen ? "rotate-180" : ""
                      }`}
                    >
                      expand_more
                    </span>
                  </div>
                  <div
                    className={`transition-all duration-300 ease-in-out overflow-hidden border-[#3c494c]/40 ${
                      isOpen ? "max-h-[300px] border-t p-6 opacity-100" : "max-h-0 opacity-0"
                    }`}
                  >
                    <p className="text-sm text-[#bbc9cd] leading-relaxed">{faq.answer}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Bottom Section (Two Columns) */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Contact Support Card */}
          <div
            onMouseMove={handleMouseMove}
            className="p-8 rounded-xl bg-[#1E293B]/50 border border-[#334155]/50 backdrop-blur-md relative overflow-hidden flex flex-col justify-between"
            style={{
              background:
                "radial-gradient(400px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(138, 235, 255, 0.05), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <div className="space-y-6">
              <h3 className="text-xl font-semibold text-[#8aebff]">Need more help?</h3>
              <div className="space-y-4">
                {/* Email Us */}
                <div className="flex items-center gap-4 p-4 bg-[#131b2e] rounded-lg border border-[#3c494c]/40">
                  <span className="material-symbols-outlined text-[#8aebff] text-2xl">mail</span>
                  <div>
                    <div className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">Email Us</div>
                    <div className="text-sm text-white font-medium">support_airpulse.ai@gmail.com</div>
                  </div>
                </div>
                {/* Phone Support */}
                <div className="flex items-center gap-4 p-4 bg-[#131b2e] rounded-lg border border-[#3c494c]/40">
                  <span className="material-symbols-outlined text-[#8aebff] text-2xl">call</span>
                  <div>
                    <div className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">Phone Support</div>
                    <div className="text-sm text-white font-medium">+91-8010648282</div>
                  </div>
                </div>
                {/* Working Hours */}
                <div className="flex items-center gap-4 p-4 bg-[#131b2e] rounded-lg border border-[#3c494c]/40">
                  <span className="material-symbols-outlined text-[#8aebff] text-2xl">schedule</span>
                  <div>
                    <div className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">Working Hours</div>
                    <div className="text-sm text-white font-medium">Mon - Fri, 09:00 - 18:00 IST</div>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row gap-4 pt-6 mt-6">
              <button
                onClick={handleStartChat}
                className="flex-1 py-3 px-6 bg-[#22D3EE] text-[#001f25] font-semibold rounded-lg flex items-center justify-center gap-2 hover:brightness-110 active:scale-95 transition-all text-sm shadow-[0_0_15px_rgba(34,211,238,0.2)]"
              >
                <span className="material-symbols-outlined text-lg">chat</span> Start Live Chat
              </button>
              <button
                onClick={handleSendEmail}
                className="flex-1 py-3 px-6 border border-[#3c494c]/80 text-[#dae2fd] font-semibold rounded-lg hover:bg-[#222a3d] active:scale-95 transition-all text-sm"
              >
                Send Email
              </button>
            </div>
          </div>

          {/* System Health Card */}
          <div
            onMouseMove={handleMouseMove}
            className="p-8 rounded-xl bg-[#1E293B]/50 border border-[#334155]/50 backdrop-blur-md relative overflow-hidden flex flex-col justify-between"
            style={{
              background:
                "radial-gradient(400px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(74, 225, 118, 0.03), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <div>
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-semibold text-[#8aebff]">System Health</h3>
                <span className="text-[10px] font-bold text-[#4ae176] px-2 py-1 bg-[#4ae176]/10 border border-[#4ae176]/20 rounded uppercase tracking-wider">
                  Global Health: 100%
                </span>
              </div>
              <div className="space-y-4">
                {/* Backend API */}
                <div className="flex items-center justify-between p-4 bg-[#131b2e] rounded-lg border border-[#3c494c]/40">
                  <div className="flex items-center gap-4">
                    <span className="material-symbols-outlined text-[#2fd9f4] text-xl">api</span>
                    <span className="text-sm font-medium text-white">Backend API</span>
                  </div>
                  <div className="flex items-center gap-2 text-[#4ae176]">
                    <span className="text-[10px] font-bold uppercase tracking-wider">Operational</span>
                    <span className="w-2 h-2 rounded-full bg-[#4ae176] shadow-[0_0_8px_#4ae176]" />
                  </div>
                </div>

                {/* AI Prediction Engine */}
                <div className="flex items-center justify-between p-4 bg-[#131b2e] rounded-lg border border-[#3c494c]/40">
                  <div className="flex items-center gap-4">
                    <span className="material-symbols-outlined text-[#2fd9f4] text-xl">psychology</span>
                    <span className="text-sm font-medium text-white">AI Prediction Engine</span>
                  </div>
                  <div className="flex items-center gap-2 text-[#4ae176]">
                    <span className="text-[10px] font-bold uppercase tracking-wider">Healthy</span>
                    <span className="w-2 h-2 rounded-full bg-[#4ae176] shadow-[0_0_8px_#4ae176]" />
                  </div>
                </div>

                {/* Weather Service */}
                <div className="flex items-center justify-between p-4 bg-[#131b2e] rounded-lg border border-[#3c494c]/40">
                  <div className="flex items-center gap-4">
                    <span className="material-symbols-outlined text-[#2fd9f4] text-xl">cloud</span>
                    <span className="text-sm font-medium text-white">Weather Service</span>
                  </div>
                  <div className="flex items-center gap-2 text-[#4ae176]">
                    <span className="text-[10px] font-bold uppercase tracking-wider">Operational</span>
                    <span className="w-2 h-2 rounded-full bg-[#4ae176] shadow-[0_0_8px_#4ae176]" />
                  </div>
                </div>

                {/* Primary Database */}
                <div className="flex items-center justify-between p-4 bg-[#131b2e] rounded-lg border border-[#3c494c]/40">
                  <div className="flex items-center gap-4">
                    <span className="material-symbols-outlined text-[#2fd9f4] text-xl">database</span>
                    <span className="text-sm font-medium text-white">Primary Database</span>
                  </div>
                  <div className="flex items-center gap-2 text-[#4ae176]">
                    <span className="text-[10px] font-bold uppercase tracking-wider">Healthy</span>
                    <span className="w-2 h-2 rounded-full bg-[#4ae176] shadow-[0_0_8px_#4ae176]" />
                  </div>
                </div>
              </div>
            </div>
            <div className="mt-6 text-center">
              <a
                className="text-[10px] font-bold text-[#bbc9cd] hover:text-[#8aebff] transition-colors underline decoration-dotted uppercase tracking-wider cursor-pointer"
                onClick={(e) => {
                  e.preventDefault();
                  alert("Historical status logs are healthy. All services maintain 100.0% uptime over past 30 days.");
                }}
              >
                View detailed status history
              </a>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="w-full py-6 flex flex-col md:flex-row justify-between items-center border-t border-[#3c494c]/40 gap-4 mt-8">
          <span className="text-[11px] font-bold text-[#bbc9cd] uppercase tracking-widest">AirPulse AI</span>
          <span className="text-[10px] font-semibold text-[#bbc9cd]/60 uppercase tracking-wider">
            © 2024 AirPulse AI • Urban Environmental Intelligence
          </span>
          <div className="flex gap-6">
            <a
              className="text-[10px] font-bold text-[#bbc9cd] hover:text-[#4ae176] uppercase tracking-wider transition-colors cursor-pointer"
              onClick={() => alert("Privacy Policy: AirPulse AI does not harvest personal monitoring metrics.")}
            >
              Privacy Policy
            </a>
            <a
              className="text-[10px] font-bold text-[#bbc9cd] hover:text-[#4ae176] uppercase tracking-wider transition-colors cursor-pointer"
              onClick={() => alert("Terms of Service: Authorized governmental & civic monitoring use only.")}
            >
              Terms of Service
            </a>
            <a
              className="text-[10px] font-bold text-[#bbc9cd] hover:text-[#4ae176] uppercase tracking-wider transition-colors cursor-pointer"
              onClick={() => alert("All services online. 100% operational.")}
            >
              API Status
            </a>
          </div>
        </footer>
      </div>
    </div>
  );
}
