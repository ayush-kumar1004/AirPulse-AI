import React, { useState, useEffect } from "react";
import { jsPDF } from "jspdf";
import html2canvas from "html2canvas";
import ForecastChart from "../components/ForecastChart";
import SourceBreakdown from "../components/SourceBreakdown";

export default function Report() {
  const [loading, setLoading] = useState(true);
  const [statusIndex, setStatusIndex] = useState(0);
  const [progressWidth, setProgressWidth] = useState(0);
  const [fadeOverlay, setFadeOverlay] = useState(false);
  const [generationTime, setGenerationTime] = useState("");

  // Mouse move handler for tracking glow
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    card.style.setProperty("--mouse-x", `${x}px`);
    card.style.setProperty("--mouse-y", `${y}px`);
  };

  useEffect(() => {
    // Live generation timestamp
    const now = new Date();
    setGenerationTime(
      now.toLocaleDateString() + " " + now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    );

    // Progress Bar Animation
    const progressTimer = setTimeout(() => {
      setProgressWidth(100);
    }, 100);

    // Status Carousel Animation
    const carouselInterval = setInterval(() => {
      setStatusIndex((prev) => {
        if (prev < 4) return prev + 1;
        clearInterval(carouselInterval);
        return prev;
      });
    }, 600);

    // Transition overlay fade-out and unmount
    const fadeTimer = setTimeout(() => {
      setFadeOverlay(true);
    }, 3100);

    const finishTimer = setTimeout(() => {
      setLoading(false);
    }, 3800);

    return () => {
      clearTimeout(progressTimer);
      clearInterval(carouselInterval);
      clearTimeout(fadeTimer);
      clearTimeout(finishTimer);
    };
  }, []);

  // PDF Download Action
  const downloadReportPDF = async () => {
    const element = document.getElementById("report-printable-area");
    if (!element) return;

    // Temporarily hide action buttons during capture
    const actionButtons = document.getElementById("report-action-buttons");
    if (actionButtons) {
      actionButtons.style.display = "none";
    }

    try {
      const canvas = await html2canvas(element, {
        scale: 1.5,
        useCORS: true,
        backgroundColor: "#0F172A",
      });

      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();

      const imgWidth = pdfWidth;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      let heightLeft = imgHeight;
      let position = 0;

      pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
      heightLeft -= pdfHeight;

      while (heightLeft >= 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
        heightLeft -= pdfHeight;
      }

      pdf.save(`AirPulse_AI_Government_Action_Report_${new Date().toISOString().slice(0, 10)}.pdf`);
    } catch (err) {
      console.error("Failed to download PDF cleanly via html2canvas:", err);
      window.print();
    } finally {
      if (actionButtons) {
        actionButtons.style.display = "flex";
      }
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator
        .share({
          title: "AirPulse AI - Government Action Report",
          text: "AI analysis and GRAP recommendations for Delhi Metro Area.",
          url: window.location.href,
        })
        .catch((err) => console.error(err));
    } else {
      alert("Sharing link copied to clipboard: " + window.location.href);
    }
  };

  // Mock data matching the layout props of existing charts
  const mockForecastData = {
    ward_id: "DEL01",
    points: Array.from({ length: 24 }).map((_, i) => {
      const date = new Date();
      date.setHours(date.getHours() + i);
      // Generate a realistic trending predicted AQI
      const baseAQI = 241;
      const change = i < 12 ? i * 2.5 : 30 - (i - 12) * 4;
      return {
        timestamp: date.toISOString(),
        predicted_aqi: Math.round(baseAQI + change),
        trend: i < 12 ? "stable" : "improving",
        lower: Math.round(baseAQI + change - 15),
        upper: Math.round(baseAQI + change + 15),
      };
    }),
  };

  const mockAttributionData = {
    ward_id: "DEL01",
    traffic: 0.45,
    construction: 0.25,
    industry: 0.2,
    dust: 0.1,
    confidence: 0.942,
    reasoning: "Traffic emissions have increased by 4% since 08:00 AM due to the arterial road blockage.",
  };

  return (
    <div className="flex-1 w-full h-full overflow-y-auto bg-[#0F172A] text-[#dae2fd] font-sans pb-24 relative">
      {/* STATE 1: LOADING OVERLAY */}
      {loading && (
        <div
          className={`fixed inset-0 z-[100] bg-[#0F172A] flex flex-col items-center justify-center transition-opacity duration-700 ${fadeOverlay ? "opacity-0" : "opacity-100"
            }`}
        >
          <div className="relative w-[320px] h-[320px] mb-12 flex items-center justify-center">
            {/* Pulsing ring animation */}
            <div className="absolute inset-0 rounded-full border border-[#22d3ee]/20 animate-ping" />
            <div className="absolute w-4/5 h-4/5 rounded-full border-2 border-dashed border-[#22d3ee]/30 animate-spin [animation-duration:15s]" />
            <div className="absolute w-2/3 h-2/3 rounded-full bg-[#1E293B] border border-[#334155] flex flex-col items-center justify-center">
              <span className="material-symbols-outlined text-[64px] text-[#22d3ee] animate-pulse">
                auto_awesome
              </span>
              <span className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider mt-2">
                Generating
              </span>
            </div>
          </div>
          <div className="text-center px-6">
            <h1 className="text-2xl font-semibold text-white mb-4">
              AI is generating your Report
            </h1>
            <div className="h-6 overflow-hidden mb-8">
              <div
                className="flex flex-col transition-transform duration-500 transform"
                style={{ transform: `translateY(-${statusIndex * 24}px)` }}
              >
                <p className="text-sm font-semibold text-[#bbc9cd] h-6 flex items-center justify-center gap-1.5">
                  Analyzing current AQI...
                </p>
                <p className="text-sm font-semibold text-[#bbc9cd] h-6 flex items-center justify-center gap-1.5">
                  Collecting weather...
                </p>
                <p className="text-sm font-semibold text-[#bbc9cd] h-6 flex items-center justify-center gap-1.5">
                  Evaluating pollution sources...
                </p>
                <p className="text-sm font-semibold text-[#bbc9cd] h-6 flex items-center justify-center gap-1.5">
                  Running AI recommendations...
                </p>
                <p className="text-sm font-semibold text-[#bbc9cd] h-6 flex items-center justify-center gap-1.5">
                  Preparing PDF...
                </p>
              </div>
            </div>
            <div className="w-64 h-1 bg-[#1E293B] rounded-full overflow-hidden mx-auto border border-[#334155]/20">
              <div
                className="h-full bg-[#22d3ee] transition-all duration-[3000ms] ease-out"
                style={{ width: `${progressWidth}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* STATE 2: REPORT CONTENT */}
      <div id="report-printable-area" className="max-w-[1200px] mx-auto p-6 md:p-8 space-y-8 report-print-container">
        {/* Report Header Actions */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-[#3c494c]/30 pb-6 gap-6">
          <div>
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
                AI Government Action Report
              </h1>
              <span className="px-3 py-0.5 bg-[#22d3ee]/10 border border-[#22d3ee]/20 text-[#22d3ee] rounded-full text-[10px] font-bold uppercase tracking-wider">
                Generated just now
              </span>
            </div>
            <p className="text-sm text-[#bbc9cd]">
              Strategic environmental analysis for the Delhi Metropolitan Region.
            </p>
            <div className="text-[11px] text-[#bbc9cd]/60 mt-1">
              Generated: <span className="text-[#bbc9cd] font-medium">{generationTime}</span> &bull; Model Confidence:{" "}
              <span className="text-[#22d3ee] font-bold">94.2%</span>
            </div>
          </div>
          <div id="report-action-buttons" className="flex flex-wrap gap-3 no-print">
            <button
              onClick={downloadReportPDF}
              className="flex items-center gap-2 px-4 py-2 bg-[#1E293B]/70 border border-[#334155]/50 hover:bg-[#222a3d] rounded-lg transition-all text-xs font-semibold uppercase tracking-wider text-white shadow-md active:scale-95"
            >
              <span className="material-symbols-outlined text-lg">download</span> Download PDF
            </button>
            <button
              onClick={handlePrint}
              className="flex items-center gap-2 px-4 py-2 bg-[#1E293B]/70 border border-[#334155]/50 hover:bg-[#222a3d] rounded-lg transition-all text-xs font-semibold uppercase tracking-wider text-white shadow-md active:scale-95"
            >
              <span className="material-symbols-outlined text-lg">print</span> Print
            </button>
            <button
              onClick={handleShare}
              className="flex items-center gap-2 px-5 py-2 bg-[#22D3EE] text-[#001f25] hover:brightness-110 rounded-lg transition-all text-xs font-bold uppercase tracking-wider shadow-md active:scale-95"
            >
              <span className="material-symbols-outlined text-lg">share</span> Share
            </button>
          </div>
        </div>

        {/* Executive Summary Grid (4 KPI cards) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1: Current City AQI */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl border border-[#334155]/50 bg-[#1E293B]/50 backdrop-blur-md relative overflow-hidden flex flex-col justify-between h-36"
            style={{
              background:
                "radial-gradient(200px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(239, 68, 68, 0.05), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <p className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">Current City AQI</p>
            <div className="flex items-end justify-between">
              <span className="text-5xl font-extrabold text-[#ef4444] leading-none">241</span>
              <span className="px-2 py-0.5 bg-[#ef4444]/10 border border-[#ef4444]/20 text-[#ef4444] rounded text-[10px] font-bold uppercase tracking-wider mb-1">
                Severe
              </span>
            </div>
          </div>

          {/* Card 2: Worst Ward */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl border border-[#334155]/50 bg-[#1E293B]/50 backdrop-blur-md relative overflow-hidden flex flex-col justify-between h-36"
            style={{
              background:
                "radial-gradient(200px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(239, 68, 68, 0.05), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <p className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">Worst Ward</p>
            <div>
              <span className="text-xl font-bold text-white block">Rohini</span>
              <span className="text-xs font-semibold text-[#ef4444]">AQI 312</span>
            </div>
          </div>

          {/* Card 3: Best Ward */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl border border-[#334155]/50 bg-[#1E293B]/50 backdrop-blur-md relative overflow-hidden flex flex-col justify-between h-36"
            style={{
              background:
                "radial-gradient(200px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(74, 225, 118, 0.05), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <p className="text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">Best Ward</p>
            <div>
              <span className="text-xl font-bold text-white block">Vasant Kunj</span>
              <span className="text-xs font-semibold text-[#22c55e]">AQI 88 (Satisfactory)</span>
            </div>
          </div>

          {/* Card 4: Forecast Trend */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl border border-[#334155]/50 bg-[#1E293B]/50 backdrop-blur-md relative overflow-hidden flex flex-col justify-between h-36 border-l-4 border-l-[#22D3EE] shadow-[0_0_15px_rgba(34,211,238,0.05)]"
            style={{
              background:
                "radial-gradient(200px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.05), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <p className="text-[10px] font-bold text-[#22D3EE] uppercase tracking-wider">Forecast Trend</p>
            <div className="flex items-center justify-between">
              <span className="text-lg font-bold text-[#4ae176]">↗ Improving</span>
              <span className="text-[10px] font-bold text-[#bbc9cd]/60">-12% Expected</span>
            </div>
          </div>
        </div>

        {/* Pollution Analysis and AI recommendations columns */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Pollution Sources */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl border border-[#334155]/50 bg-[#1E293B]/50 backdrop-blur-md lg:col-span-1 relative overflow-hidden flex flex-col justify-between space-y-4"
            style={{
              background:
                "radial-gradient(300px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.04), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <div>
              <h3 className="text-base font-semibold text-white mb-4">Pollution Sources</h3>
              <div className="space-y-4">
                {/* Traffic */}
                <div>
                  <div className="flex justify-between text-xs font-semibold text-[#bbc9cd] mb-1">
                    <span>Traffic</span>
                    <span>45%</span>
                  </div>
                  <div className="h-2 bg-[#0F172A] rounded-full overflow-hidden border border-[#334155]/20">
                    <div className="bg-[#22D3EE] h-full w-[45%] rounded-full" />
                  </div>
                </div>
                {/* Construction */}
                <div>
                  <div className="flex justify-between text-xs font-semibold text-[#bbc9cd] mb-1">
                    <span>Construction</span>
                    <span>25%</span>
                  </div>
                  <div className="h-2 bg-[#0F172A] rounded-full overflow-hidden border border-[#334155]/20">
                    <div className="bg-[#22D3EE] opacity-80 h-full w-[25%] rounded-full" />
                  </div>
                </div>
                {/* Industry */}
                <div>
                  <div className="flex justify-between text-xs font-semibold text-[#bbc9cd] mb-1">
                    <span>Industry</span>
                    <span>20%</span>
                  </div>
                  <div className="h-2 bg-[#0F172A] rounded-full overflow-hidden border border-[#334155]/20">
                    <div className="bg-[#22D3EE] opacity-60 h-full w-[20%] rounded-full" />
                  </div>
                </div>
                {/* Dust */}
                <div>
                  <div className="flex justify-between text-xs font-semibold text-[#bbc9cd] mb-1">
                    <span>Dust</span>
                    <span>10%</span>
                  </div>
                  <div className="h-2 bg-[#0F172A] rounded-full overflow-hidden border border-[#334155]/20">
                    <div className="bg-[#22D3EE] opacity-40 h-full w-[10%] rounded-full" />
                  </div>
                </div>
              </div>
            </div>
            <div className="p-3 bg-[#22d3ee]/5 rounded-lg border border-[#22d3ee]/10 mt-4">
              <p className="text-[11px] text-[#22d3ee] flex items-start gap-1.5">
                <span className="material-symbols-outlined text-xs mt-0.5">info</span>
                Traffic emissions have increased by 4% since 08:00 AM due to the arterial road blockage.
              </p>
            </div>
          </div>

          {/* AI Government Recommendations */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-[#22D3EE]">verified_user</span>
              AI Government Recommendations
            </h3>
            <div className="space-y-3">
              {/* High Priority */}
              <div className="p-4 rounded-xl bg-[#1E293B]/50 border border-[#334155]/50 border-l-4 border-l-[#ef4444] backdrop-blur-md flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-[#ef4444]/10 border border-[#ef4444]/20 text-[#ef4444] flex items-center justify-center flex-shrink-0 font-bold text-sm">
                  H
                </div>
                <div>
                  <p className="text-[9px] font-bold text-[#ef4444] tracking-wider uppercase mb-0.5">High Priority</p>
                  <h4 className="text-sm font-semibold text-white">Immediate ban on non-essential construction.</h4>
                  <p className="text-xs text-[#bbc9cd] mt-0.5 leading-relaxed">
                    Recommended for Rohini, Dwarka, and Mundka sectors for the next 48 hours.
                  </p>
                </div>
              </div>
              {/* Medium Priority */}
              <div className="p-4 rounded-xl bg-[#1E293B]/50 border border-[#334155]/50 border-l-4 border-l-[#ffd4bf] backdrop-blur-md flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-[#ffd4bf]/10 border border-[#ffd4bf]/20 text-[#ffd4bf] flex items-center justify-center flex-shrink-0 font-bold text-sm">
                  M
                </div>
                <div>
                  <p className="text-[9px] font-bold text-[#ffd4bf] tracking-wider uppercase mb-0.5">Medium Priority</p>
                  <h4 className="text-sm font-semibold text-white">Deploy anti-smog guns in North Delhi.</h4>
                  <p className="text-xs text-[#bbc9cd] mt-0.5 leading-relaxed">
                    Targeting hotspots identified by real-time sensor array 014-B.
                  </p>
                </div>
              </div>
              {/* Low Priority */}
              <div className="p-4 rounded-xl bg-[#1E293B]/50 border border-[#334155]/50 border-l-4 border-l-[#4ae176] backdrop-blur-md flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-[#4ae176]/10 border border-[#4ae176]/20 text-[#4ae176] flex items-center justify-center flex-shrink-0 font-bold text-sm">
                  L
                </div>
                <div>
                  <p className="text-[9px] font-bold text-[#4ae176] tracking-wider uppercase mb-0.5">Low Priority</p>
                  <h4 className="text-sm font-semibold text-white">Public advisory for N95 masks.</h4>
                  <p className="text-xs text-[#bbc9cd] mt-0.5 leading-relaxed">
                    General advisory for sensitive groups across all NCR zones.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Ward-wise Analysis Table */}
        <div className="rounded-xl border border-[#334155]/50 bg-[#1E293B]/50 overflow-hidden">
          <div className="p-5 border-b border-[#3c494c]/30 flex flex-wrap justify-between items-center gap-3">
            <h3 className="text-base font-semibold text-white">Ward-wise Analysis</h3>
            <div className="flex gap-2">
              <span className="px-2.5 py-1 bg-[#131b2e] border border-[#3c494c]/20 text-[10px] font-semibold text-[#bbc9cd] rounded">
                Filters: All Wards
              </span>
              <span className="px-2.5 py-1 bg-[#131b2e] border border-[#3c494c]/20 text-[10px] font-semibold text-[#bbc9cd] rounded">
                Sort: AQI High to Low
              </span>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-[#131b2e]/60 text-[10px] font-bold uppercase tracking-wider text-[#bbc9cd]">
                <tr>
                  <th className="px-6 py-3 border-b border-[#3c494c]/20">Ward Name</th>
                  <th className="px-6 py-3 border-b border-[#3c494c]/20">AQI Level</th>
                  <th className="px-6 py-3 border-b border-[#3c494c]/20">24h Forecast</th>
                  <th className="px-6 py-3 border-b border-[#3c494c]/20">Dominant Source</th>
                  <th className="px-6 py-3 border-b border-[#3c494c]/20">Recommended Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#3c494c]/20 text-[#dae2fd]">
                <tr className="hover:bg-[#222a3d]/50 transition-colors">
                  <td className="px-6 py-4 font-bold text-white">Rohini</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-[#ef4444] shadow-[0_0_8px_#ef4444]" />
                      <span>312 (Severe)</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-[#ef4444] font-semibold">↑ Rise</td>
                  <td className="px-6 py-4">Construction</td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-0.5 bg-[#ef4444]/10 border border-[#ef4444]/20 text-[#ef4444] rounded-full text-[10px] font-semibold">
                      GRAP Level 4
                    </span>
                  </td>
                </tr>
                <tr className="hover:bg-[#222a3d]/50 transition-colors">
                  <td className="px-6 py-4 font-bold text-white">Mundka</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-[#ef4444] shadow-[0_0_8px_#ef4444]" />
                      <span>288 (Severe)</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-[#bbc9cd]/60">→ Stable</td>
                  <td className="px-6 py-4">Industrial</td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-0.5 bg-[#ef4444]/10 border border-[#ef4444]/20 text-[#ef4444] rounded-full text-[10px] font-semibold">
                      Halt Industry
                    </span>
                  </td>
                </tr>
                <tr className="hover:bg-[#222a3d]/50 transition-colors">
                  <td className="px-6 py-4 font-bold text-white">Civil Lines</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-[#ffd4bf] shadow-[0_0_8px_#ffd4bf]" />
                      <span>142 (Moderate)</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-[#22c55e] font-semibold">↓ Fall</td>
                  <td className="px-6 py-4">Traffic</td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-0.5 bg-[#ffd4bf]/10 border border-[#ffd4bf]/20 text-[#ffd4bf] rounded-full text-[10px] font-semibold">
                      Traffic Control
                    </span>
                  </td>
                </tr>
                <tr className="hover:bg-[#222a3d]/50 transition-colors">
                  <td className="px-6 py-4 font-bold text-white">Dwarka</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-[#ef4444] shadow-[0_0_8px_#ef4444]" />
                      <span>265 (Severe)</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-[#22c55e] font-semibold">↓ Fall</td>
                  <td className="px-6 py-4">Dust / Construction</td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-0.5 bg-[#ef4444]/10 border border-[#ef4444]/20 text-[#ef4444] rounded-full text-[10px] font-semibold">
                      Water Sprinkling
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Visualizations Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Reusable Source Attribution Chart */}
          <div className="lg:col-span-1">
            <SourceBreakdown attributionData={mockAttributionData} loading={false} />
          </div>

          {/* Reusable Forecast Chart */}
          <div className="lg:col-span-1">
            <ForecastChart forecastData={mockForecastData} loading={false} />
          </div>

          {/* Stitch AQI Trend Visual */}
          <div
            onMouseMove={handleMouseMove}
            className="p-6 rounded-xl border border-[#334155]/50 bg-[#1E293B]/50 backdrop-blur-md lg:col-span-1 relative overflow-hidden flex flex-col justify-between"
            style={{
              background:
                "radial-gradient(300px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.04), transparent 80%), rgba(30, 41, 59, 0.5)",
            }}
          >
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-[11px] font-bold text-[#bbc9cd] tracking-wider uppercase">
                AQI Multi-Day Trend Forecast
              </h3>
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1 text-[9px] text-[#bbc9cd]/60">
                  <span className="w-2.5 h-1 bg-[#22d3ee]" /> AI Forecasted
                </span>
                <span className="flex items-center gap-1 text-[9px] text-[#bbc9cd]/60">
                  <span className="w-2.5 h-1 bg-[#859397]" /> Historical
                </span>
              </div>
            </div>

            <div className="h-44 flex items-end gap-3 w-full px-2">
              {/* Mon */}
              <div className="flex-1 bg-[#0F172A] relative h-[40%] rounded-t border border-[#334155]/30 group">
                <div className="absolute inset-x-0 bottom-0 bg-[#859397]/25 h-full group-hover:bg-[#859397]/40 transition-all rounded-t-sm" />
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 text-[10px] text-[#bbc9cd] font-bold bg-[#0F172A] px-1 border border-[#334155] rounded">
                  142
                </div>
              </div>
              {/* Tue */}
              <div className="flex-1 bg-[#0F172A] relative h-[55%] rounded-t border border-[#334155]/30 group">
                <div className="absolute inset-x-0 bottom-0 bg-[#859397]/25 h-full group-hover:bg-[#859397]/40 transition-all rounded-t-sm" />
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 text-[10px] text-[#bbc9cd] font-bold bg-[#0F172A] px-1 border border-[#334155] rounded">
                  175
                </div>
              </div>
              {/* Wed */}
              <div className="flex-1 bg-[#0F172A] relative h-[75%] rounded-t border border-[#334155]/30 group">
                <div className="absolute inset-x-0 bottom-0 bg-[#ef4444]/20 h-full group-hover:bg-[#ef4444]/35 transition-all rounded-t-sm" />
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 text-[10px] text-[#ef4444] font-bold bg-[#0F172A] px-1 border border-[#334155] rounded">
                  220
                </div>
              </div>
              {/* Today */}
              <div className="flex-1 bg-[#0F172A] relative h-[85%] rounded-t border border-[#22d3ee]/40 group shadow-[0_0_10px_rgba(34,211,238,0.15)]">
                <div className="absolute inset-x-0 bottom-0 bg-[#ef4444]/40 h-full group-hover:bg-[#ef4444]/65 transition-all border-t-2 border-[#22D3EE] rounded-t-sm" />
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] text-[#22d3ee] font-extrabold bg-[#0F172A] px-1 border border-[#22d3ee]/30 rounded">
                  241
                </div>
              </div>
              {/* Fri */}
              <div className="flex-1 bg-[#0F172A] relative h-[70%] rounded-t border border-[#334155]/30 group">
                <div className="absolute inset-x-0 bottom-0 bg-[#22d3ee]/15 h-full border-t-2 border-[#22d3ee] border-dashed rounded-t-sm" />
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 text-[10px] text-[#22d3ee] font-bold bg-[#0F172A] px-1 border border-[#22d3ee]/30 rounded">
                  215
                </div>
              </div>
              {/* Sat */}
              <div className="flex-1 bg-[#0F172A] relative h-[60%] rounded-t border border-[#334155]/30 group">
                <div className="absolute inset-x-0 bottom-0 bg-[#22d3ee]/15 h-full border-t-2 border-[#22d3ee] border-dashed rounded-t-sm" />
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 text-[10px] text-[#22d3ee] font-bold bg-[#0F172A] px-1 border border-[#22d3ee]/30 rounded">
                  188
                </div>
              </div>
              {/* Sun */}
              <div className="flex-1 bg-[#0F172A] relative h-[50%] rounded-t border border-[#334155]/30 group">
                <div className="absolute inset-x-0 bottom-0 bg-[#22d3ee]/15 h-full border-t-2 border-[#22d3ee] border-dashed rounded-t-sm" />
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 text-[10px] text-[#22d3ee] font-bold bg-[#0F172A] px-1 border border-[#22d3ee]/30 rounded">
                  160
                </div>
              </div>
            </div>
            <div className="flex justify-between mt-3 px-1 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">
              <span>Mon</span>
              <span>Tue</span>
              <span>Wed</span>
              <span className="text-[#22d3ee]">Today</span>
              <span>Fri</span>
              <span>Sat</span>
              <span>Sun</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="w-full py-6 flex flex-col md:flex-row justify-between items-center border-t border-[#3c494c]/30 gap-4 mt-8 report-footer">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-bold text-[#bbc9cd] uppercase tracking-widest">
              Generated by AirPulse AI
            </span>
            <span className="w-1 h-1 rounded-full bg-[#859397]/40" />
            <span className="text-[10px] font-bold text-[#22d3ee] uppercase tracking-wider">
              Model Confidence: 98%
            </span>
            <span className="w-1 h-1 rounded-full bg-[#859397]/40" />
            <span className="text-[10px] font-semibold text-[#bbc9cd]/60 uppercase tracking-wider">
              v1.0.4-Stable
            </span>
            <span className="w-1 h-1 rounded-full bg-[#859397]/40" />
            <span className="text-[10px] font-semibold text-[#bbc9cd]/60 uppercase tracking-wider">
              {generationTime}
            </span>
            <span className="w-1 h-1 rounded-full bg-[#859397]/40" />
            <span className="text-[10px] font-bold text-[#4ae176] uppercase tracking-wider border border-[#4ae176]/20 bg-[#4ae176]/5 px-2 py-0.5 rounded">
              Government Ready Report
            </span>
          </div>
          <div className="flex gap-4">
            <a className="text-[10px] font-bold text-[#bbc9cd]/50 hover:text-white uppercase tracking-wider transition-colors" href="#privacy">
              Privacy Policy
            </a>
            <a className="text-[10px] font-bold text-[#bbc9cd]/50 hover:text-white uppercase tracking-wider transition-colors" href="#terms">
              Terms of Service
            </a>
            <a className="text-[10px] font-bold text-[#bbc9cd]/50 hover:text-white uppercase tracking-wider transition-colors" href="#status">
              API Status
            </a>
          </div>
          <p className="text-[10px] font-semibold text-[#bbc9cd]/40 uppercase tracking-wider">
            © 2026 AirPulse AI &bull; Urban Environmental Intelligence
          </p>
        </footer>
      </div>
    </div>
  );
}
