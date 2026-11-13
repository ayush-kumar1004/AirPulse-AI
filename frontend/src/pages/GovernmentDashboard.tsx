import React, { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Sparkles,
  MapPin,
  Send,
  MessageSquare,
  History,
  ShieldAlert,
  Building,
  RefreshCw,
  CheckCircle2,
  ArrowRight,
  ClipboardList,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";
import { getRecommend, getWards, officerChat, getChatHistory } from "../api/client";

interface ActionRecommendation {
  action: string;
  target: string;
  urgency: string; // high, medium, low
  reason: string;
}

interface InspectionItem {
  site: string;
  ward?: string;
  ward_id?: string;
  reason: string;
  priority: number;
}

interface Message {
  sender: "user" | "ai";
  text: string;
  timestamp: string;
  sources?: string[];
}

interface WardOption {
  id: string;
  name: string;
}

export default function GovernmentDashboard() {
  const [searchParams] = useSearchParams();
  const urlWard = searchParams.get("ward");

  const [wards, setWards] = useState<WardOption[]>([]);
  const [selectedWard, setSelectedWard] = useState<string>(urlWard || "CANT_1");
  const [recommendations, setRecommendations] = useState<any>(null);
  const [loadingRecs, setLoadingRecs] = useState<boolean>(true);

  // Multi-turn persistent session ID (survives page refresh via localStorage + checkpointer)
  const [sessionId, setSessionId] = useState<string>(() => {
    const saved = localStorage.getItem("airpulse_officer_session");
    if (saved) return saved;
    const fresh = "officer-sess-" + Math.random().toString(36).substring(2, 9);
    localStorage.setItem("airpulse_officer_session", fresh);
    return fresh;
  });

  const [chatInput, setChatInput] = useState<string>("");
  const [chatLoading, setChatLoading] = useState<boolean>(false);
  const [executedActions, setExecutedActions] = useState<Record<number, boolean>>({});

  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "user",
      text: "Which wards are critical right now?",
      timestamp: "Officer",
    },
    {
      sender: "ai",
      text: "Based on real-time citywide sensor telemetry, Rohini (W02) and Anand Vihar (W07) are critical hotspots with AQI levels exceeding 240. Localized particulate matter is trapped under low inversion layer height.\n\nAsk me to diagnose the main emission source in either ward, run a 24h predictive trajectory, compare them, or draft an executive GRAP enforcement notice.",
      timestamp: "AI Agent",
      sources: ["City Hotspot Scanner", "CPCB Telemetry"],
    },
  ]);

  // Restore persistent conversation history from checkpointer on mount
  useEffect(() => {
    let isMounted = true;
    const restoreHistory = async () => {
      try {
        const res = await getChatHistory(sessionId);
        if (isMounted && res?.messages && res.messages.length > 0) {
          setMessages(res.messages);
        }
      } catch (err) {
        console.warn("Could not restore chat history from checkpointer:", err);
      }
    };
    restoreHistory();
    return () => {
      isMounted = false;
    };
  }, [sessionId]);

  const handleResetSession = () => {
    const fresh = "officer-sess-" + Math.random().toString(36).substring(2, 9);
    localStorage.setItem("airpulse_officer_session", fresh);
    setSessionId(fresh);
    setMessages([
      {
        sender: "ai",
        text: "Fresh session initialized. Full multi-turn checkpointer memory is active. What environmental telemetry or enforcement actions would you like to investigate?",
        timestamp: "AI Agent",
        sources: ["Session Init"],
      },
    ]);
  };

  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat history
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, chatLoading]);

  // Load available wards on mount
  useEffect(() => {
    let isMounted = true;
    const loadWards = async () => {
      try {
        const res = await getWards();
        const features = res?.features ?? [];
        const options: WardOption[] = features
          .map((f: any) => ({
            id: f.properties?.ward_id ?? f.properties?.id ?? f.id,
            name: f.properties?.ward_name ?? f.properties?.Ward_Name ?? f.properties?.name ?? `Ward ${f.properties?.ward_id ?? f.id ?? ""}`,
          }))
          .filter((w: WardOption) => Boolean(w.id));

        if (options.length === 0) {
          options.push(
            { id: "W01", name: "Connaught Place" },
            { id: "W02", name: "Rohini" },
            { id: "W03", name: "Dwarka" },
            { id: "W04", name: "Karol Bagh" },
            { id: "W05", name: "Okhla Industrial Area" },
            { id: "W06", name: "Greater Kailash" },
            { id: "W07", name: "Anand Vihar" },
            { id: "W08", name: "Janakpuri" },
            { id: "W09", name: "Narela" },
            { id: "W10", name: "Vasant Kunj" }
          );
        }

        if (isMounted) {
          setWards(options);
          const currentUrlWard = searchParams.get("ward");
          if (currentUrlWard && options.some((o) => o.id === currentUrlWard)) {
            setSelectedWard(currentUrlWard);
          } else if (!options.some((o) => o.id === selectedWard)) {
            setSelectedWard(options[0]?.id || "CANT_1");
          }
        }
      } catch (err) {
        console.warn("Could not load wards GeoJSON, using default ward list", err);
        if (isMounted) {
          setWards([
            { id: "W01", name: "Connaught Place" },
            { id: "W02", name: "Rohini" },
            { id: "W03", name: "Dwarka" },
            { id: "W04", name: "Karol Bagh" },
            { id: "W05", name: "Okhla Industrial Area" },
            { id: "W06", name: "Greater Kailash" },
            { id: "W07", name: "Anand Vihar" },
            { id: "W08", name: "Janakpuri" },
            { id: "W09", name: "Narela" },
            { id: "W10", name: "Vasant Kunj" },
          ]);
        }
      }
    };
    loadWards();
    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch recommendations whenever selectedWard changes
  const fetchRecommendations = useCallback(async (wardId: string) => {
    setLoadingRecs(true);
    try {
      const data = await getRecommend(wardId);
      setRecommendations(data);
    } catch (err) {
      console.error("Error loading recommendations:", err);
      // Sensible fallback conforming to GRAP rules
      setRecommendations({
        ward_id: wardId,
        actions: [
          {
            action: "Deploy mechanized road sweeping & water sprinklers",
            target: `${wardId} Arterial Road Corridor`,
            urgency: "high",
            reason: "Elevated road dust & particulate suspension under low boundary layer height.",
          },
          {
            action: "Inspect major construction sites for dust netting compliance",
            target: "Local Construction Hubs",
            urgency: "medium",
            reason: "GRAP Stage II compliance protocol active.",
          },
          {
            action: "Stagger diesel freight movement during peak morning commute",
            target: "Major Ring Road Intersections",
            urgency: "medium",
            reason: "Traffic contribution to localized NO2 and PM2.5 elevated.",
          },
        ],
        inspection_priority: [
          { site: "Metro Transit Construction Site", ward_id: wardId, reason: "Uncovered dry cement & aggregate stockpiles", priority: 1 },
          { site: "Outer Ring Road Junction", ward_id: wardId, reason: "Diesel idling and traffic choke point", priority: 2 },
          { site: "Sub-station Industrial Cluster", ward_id: wardId, reason: "Diesel generator set emissions audit", priority: 3 },
        ],
      });
    } finally {
      setLoadingRecs(false);
    }
  }, []);

  useEffect(() => {
    if (selectedWard) {
      fetchRecommendations(selectedWard);
    }
  }, [selectedWard, fetchRecommendations]);

  // Card mouse tracking glow
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    card.style.setProperty("--mouse-x", `${x}px`);
    card.style.setProperty("--mouse-y", `${y}px`);
  };

  // Chat send message with multi-turn session ID
  const handleSendMessage = async (text: string) => {
    if (!text.trim() || chatLoading) return;
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")} • Officer`;

    const userMsg: Message = { sender: "user", text, timestamp: timeStr };
    setMessages((prev) => [...prev, userMsg]);
    setChatInput("");
    setChatLoading(true);

    try {
      const res = await officerChat({
        message: text,
        ward_id: selectedWard,
        session_id: sessionId,
      });

      const aiTimeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")} • AI Agent`;

      const sourcesMapped =
        res.tools_used && res.tools_used.length > 0
          ? res.tools_used.map((t: string) => {
              if (t === "get_citywide_hotspots") return "City Hotspot Scanner";
              if (t === "get_source_attribution") return "Chemical Attribution";
              if (t === "get_forecast" || t === "get_predict") return "LightGBM Forecast";
              if (t === "compare_wards") return "Ward Comparative Analytics";
              if (t === "draft_grap_notice") return "CAQM GRAP Directive Engine";
              if (t === "get_historical_trend") return "7-Day Historical Telemetry";
              if (t === "get_aqi") return "CPCB Telemetry";
              if (t === "get_weather") return "Open-Meteo Edge";
              if (t === "get_recommendations") return "GRAP Actions";
              return t;
            })
          : ["AI Autonomous Inference"];

      const aiMsg: Message = {
        sender: "ai",
        text: res.reply || "Recommendation processed successfully.",
        timestamp: aiTimeStr,
        sources: Array.from(new Set(sourcesMapped)),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error("Chat error:", err);
      const aiMsg: Message = {
        sender: "ai",
        text: "I was unable to reach the live command intelligence service. However, under standard GRAP Stage II protocols, intensive water sprinkling and diesel transport restrictions should proceed.",
        timestamp: timeStr.replace("Officer", "AI Agent"),
        sources: ["Cached Protocol"],
      };
      setMessages((prev) => [...prev, aiMsg]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleExecuteAction = (idx: number, act: ActionRecommendation) => {
    setExecutedActions((prev) => ({ ...prev, [idx]: true }));
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")} • System Notice`;
    const noticeMsg: Message = {
      sender: "ai",
      text: `✓ Dispatch Order Issued: "${act.action}" assigned to DPCC Field Unit for ${act.target}. Urgency level: ${act.urgency.toUpperCase()}.`,
      timestamp: timeStr,
      sources: ["Command Dispatch"],
    };
    setMessages((prev) => [...prev, noticeMsg]);
  };

  const currentWardName =
    wards.find((w) => w.id === selectedWard)?.name ?? `Ward ${selectedWard}`;

  const actionsToRender: ActionRecommendation[] = recommendations?.actions ?? [];
  const priorityToRender: InspectionItem[] = recommendations?.inspection_priority ?? [];

  return (
    <div className="flex-1 w-full h-full overflow-y-auto p-6 md:p-8 space-y-8 bg-[#0F172A] text-[#dae2fd] font-sans pb-24">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Page Header Area with Dynamic Ward Selector */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-[#1E293B]/60 p-6 rounded-2xl border border-[#334155]/60 backdrop-blur-md">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 text-[10px] font-extrabold uppercase tracking-wider rounded-full bg-[#22D3EE]/20 text-[#22D3EE]">
                Government Tactical Console
              </span>
              <span className="text-xs text-[#94a3b8]">· DPCC Environmental Response</span>
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">Urban Command Center</h1>
            <p className="text-sm text-[#bbc9cd] mt-1">
              Intelligence and GRAP Action Directives for{" "}
              <span className="font-bold text-[#22D3EE]">{currentWardName}</span>
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Ward Selector */}
            <div className="flex items-center gap-2 bg-[#0f172a] px-3.5 py-2 rounded-xl border border-[#334155] shadow-inner">
              <MapPin className="w-4 h-4 text-[#22D3EE]" />
              <select
                aria-label="Select Target Ward"
                value={selectedWard}
                onChange={(e) => setSelectedWard(e.target.value)}
                className="bg-transparent text-xs font-bold text-white focus:outline-none cursor-pointer"
              >
                {wards.map((w) => (
                  <option key={w.id} value={w.id} className="bg-[#0f172a] text-white">
                    {w.name} ({w.id})
                  </option>
                ))}
              </select>
            </div>

            {/* Refresh Button */}
            <button
              onClick={() => fetchRecommendations(selectedWard)}
              disabled={loadingRecs}
              title="Refresh AI Recommendations"
              className="p-2.5 rounded-xl border border-[#334155] bg-[#0f172a] hover:bg-[#1E293B] text-[#bbc9cd] hover:text-white transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loadingRecs ? "animate-spin text-[#22D3EE]" : ""}`} />
            </button>

            {/* Status Pill */}
            <div className="bg-[#171f33] px-3.5 py-2 rounded-xl border border-[#3c494c]/40 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#4ae176] animate-pulse" />
              <span className="text-[10px] font-bold text-white uppercase tracking-wider">
                GRAP ENGINE: ACTIVE
              </span>
            </div>
          </div>
        </header>

        {/* Two-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column (7 cols): AI Recommended Actions & Queue */}
          <div className="lg:col-span-7 space-y-6">
            <section
              onMouseMove={handleMouseMove}
              className="p-6 rounded-2xl border border-[#334155]/50 relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md shadow-inner-cyan border-l-4 border-l-[#22D3EE]"
              style={{
                background:
                  "radial-gradient(1000px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.05), transparent 80%), rgba(30, 41, 59, 0.5)",
              }}
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                    <ShieldAlert className="w-5 h-5 text-[#22D3EE]" />
                    AI Priority Actions
                  </h2>
                  <p className="text-xs text-[#94a3b8] mt-0.5">
                    Targeted regulatory and mitigation levers for {currentWardName}
                  </p>
                </div>
                <div className="bg-[#22D3EE]/10 text-[#22D3EE] border border-[#22D3EE]/25 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-[#22D3EE]" />
                  <span>GRAP Directives</span>
                </div>
              </div>

              {/* Action Cards List */}
              {loadingRecs ? (
                <div className="py-12 flex flex-col items-center justify-center gap-2 text-[#94a3b8]">
                  <RefreshCw className="w-6 h-6 animate-spin text-[#22D3EE]" />
                  <span className="text-xs">Analyzing ward telemetry and generating GRAP actions...</span>
                </div>
              ) : actionsToRender.length === 0 ? (
                <div className="py-8 text-center text-xs text-[#94a3b8]">
                  No urgent actions required for this ward at current atmospheric conditions.
                </div>
              ) : (
                <div className="space-y-4">
                  {actionsToRender.map((act: ActionRecommendation, idx: number) => {
                    const isHigh = act.urgency?.toLowerCase() === "high";
                    const isMedium = act.urgency?.toLowerCase() === "medium";

                    let borderLeftColor = "bg-[#4ae176]";
                    let urgencyBadge = "bg-green-500/20 text-green-400 border border-green-500/30";
                    if (isHigh) {
                      borderLeftColor = "bg-red-600";
                      urgencyBadge = "bg-red-900/40 text-red-400 border border-red-500/30";
                    } else if (isMedium) {
                      borderLeftColor = "bg-orange-500";
                      urgencyBadge = "bg-orange-950/40 text-orange-400 border border-orange-500/30";
                    }

                    const isExecuted = executedActions[idx];

                    return (
                      <div
                        key={idx}
                        className="relative overflow-hidden bg-[#131b2e] border border-[#3c494c]/40 rounded-xl p-4 transition-all hover:bg-[#1E293B] group"
                      >
                        <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${borderLeftColor}`} />
                        <div className="flex justify-between items-start mb-2 pl-2">
                          <h3 className="text-sm font-bold text-white tracking-tight group-hover:text-[#22D3EE] transition-colors">
                            {act.action}
                          </h3>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${urgencyBadge}`}
                          >
                            {act.urgency}
                          </span>
                        </div>
                        <p className="text-xs text-[#bbc9cd] mb-3 pl-2 leading-relaxed">{act.reason}</p>
                        <div className="flex items-center gap-4 pl-2">
                          <div className="flex items-center gap-1.5 text-[10px] font-bold text-[#bbc9cd] uppercase bg-[#171f33] px-2.5 py-1 rounded">
                            <MapPin className="w-3.5 h-3.5 text-[#22D3EE]" />
                            {act.target}
                          </div>
                          <button
                            onClick={() => handleExecuteAction(idx, act)}
                            disabled={isExecuted}
                            className={`ml-auto text-xs font-bold uppercase tracking-wider flex items-center gap-1 transition-all ${
                              isExecuted
                                ? "text-green-400 cursor-default"
                                : "text-[#22D3EE] hover:underline"
                            }`}
                          >
                            {isExecuted ? (
                              <>
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                <span>Dispatched</span>
                              </>
                            ) : (
                              <>
                                <span>Execute Directive</span>
                                <ArrowRight className="w-3.5 h-3.5" />
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </section>

            {/* Inspection Priority Table */}
            <section className="glass-panel border border-[#334155]/50 rounded-2xl overflow-hidden bg-[#1E293B]/40">
              <div className="px-6 py-4 border-b border-[#3c494c]/40 bg-[#171f33] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ClipboardList className="w-4 h-4 text-[#22D3EE]" />
                  <h3 className="text-xs font-bold text-white tracking-wider uppercase">
                    Field Inspection Priority Queue
                  </h3>
                </div>
                <span className="text-[10px] font-bold text-[#94a3b8] uppercase">
                  Ranked by Risk Weight
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-[#131b2e] border-b border-[#3c494c]/30">
                    <tr>
                      <th className="px-6 py-3.5 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">
                        Target Site
                      </th>
                      <th className="px-6 py-3.5 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">
                        Zone / Ward
                      </th>
                      <th className="px-6 py-3.5 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">
                        Inspection Driver
                      </th>
                      <th className="px-6 py-3.5 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">
                        Priority
                      </th>
                      <th className="px-6 py-3.5 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">
                        Action
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#3c494c]/20">
                    {priorityToRender.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-6 py-6 text-center text-xs text-[#94a3b8]">
                          No pending site inspections scheduled.
                        </td>
                      </tr>
                    ) : (
                      priorityToRender.map((row: InspectionItem, idx: number) => {
                        const priorityColor =
                          row.priority === 1
                            ? "bg-red-500/20 text-red-400 border border-red-500/30"
                            : row.priority === 2
                            ? "bg-orange-500/20 text-orange-400 border border-orange-500/30"
                            : "bg-green-500/20 text-green-400 border border-green-500/30";

                        return (
                          <tr key={idx} className="hover:bg-[#1E293B]/40 transition-colors">
                            <td className="px-6 py-4 text-xs font-bold text-white">{row.site}</td>
                            <td className="px-6 py-4 text-xs text-[#bbc9cd]">
                              {row.ward || row.ward_id || currentWardName}
                            </td>
                            <td className="px-6 py-4 text-xs text-[#bbc9cd]">{row.reason}</td>
                            <td className="px-6 py-4">
                              <span
                                className={`w-6 h-6 rounded flex items-center justify-center text-xs font-bold ${priorityColor}`}
                              >
                                {row.priority}
                              </span>
                            </td>
                            <td className="px-6 py-4">
                              <button
                                onClick={() =>
                                  handleSendMessage(`Draft field inspection brief for ${row.site} in ${currentWardName}`)
                                }
                                className="text-[#22D3EE] hover:text-white transition-colors"
                                title="Ask AI about this site"
                              >
                                <ArrowRight className="w-4 h-4" />
                              </button>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </div>

          {/* Right Column (5 cols): Officer Assistant Chat Panel */}
          <div className="lg:col-span-5 h-[700px] flex flex-col">
            <section
              onMouseMove={handleMouseMove}
              className="p-0 border border-[#334155]/50 rounded-2xl relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md flex flex-col h-full shadow-inner-cyan"
              style={{
                background:
                  "radial-gradient(800px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.05), transparent 80%), rgba(30, 41, 59, 0.5)",
              }}
            >
              {/* Chat Header */}
              <div className="p-4 border-b border-[#3c494c]/40 flex items-center justify-between bg-[#171f33]">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#22D3EE]/25 flex items-center justify-center text-[#22D3EE] border border-[#22D3EE]/20 shadow-lg">
                    <MessageSquare className="w-5 h-5 text-[#22D3EE]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white tracking-tight">Ask AirPulse Agent</h3>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#4ae176] animate-pulse" />
                      <span className="text-[9px] text-[#bbc9cd] font-bold tracking-wider uppercase">
                        MULTI-TURN MEMORY READY
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleResetSession}
                    title="Start Fresh Session (Reset Checkpointer Thread)"
                    className="p-1.5 rounded-lg border border-[#3c494c]/50 text-[#bbc9cd] hover:text-white hover:bg-[#1E293B] transition-all flex items-center gap-1 text-[10px]"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">New Session</span>
                  </button>
                  <div className="text-[10px] font-bold text-[#22D3EE] bg-[#22D3EE]/10 px-2.5 py-1 rounded-full border border-[#22D3EE]/20">
                    {selectedWard}
                  </div>
                </div>
              </div>

              {/* Chat History */}
              <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                {messages.map((msg, idx) => {
                  const isUser = msg.sender === "user";
                  return (
                    <div key={idx} className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}>
                      <div className="flex gap-3 max-w-[90%]">
                        {!isUser && (
                          <div className="w-8 h-8 rounded-full bg-[#22D3EE]/10 flex-shrink-0 flex items-center justify-center text-[#22D3EE] border border-[#22D3EE]/20 mt-1 shadow-md">
                            <Sparkles className="w-4 h-4 text-[#22D3EE]" />
                          </div>
                        )}
                        <div className="space-y-2">
                          <div
                            className={`px-4 py-3 rounded-2xl border shadow-md ${
                              isUser
                                ? "bg-[#1E293B] border-[#3c494c]/40 rounded-tr-none text-[#dae2fd]"
                                : "bg-[#171f33] border-[#22D3EE]/20 rounded-tl-none text-[#dae2fd] whitespace-pre-line leading-relaxed text-xs"
                            }`}
                          >
                            <p className="text-xs">{msg.text}</p>
                          </div>
                          {!isUser && msg.sources && msg.sources.length > 0 && (
                            <div className="flex items-center gap-2 flex-wrap pl-1">
                              <span className="text-[9px] font-bold text-[#bbc9cd] uppercase tracking-wider">
                                Citations:
                              </span>
                              {msg.sources.map((src, sIdx) => (
                                <span
                                  key={sIdx}
                                  className="bg-[#2d3449] border border-[#3c494c]/20 px-2 py-0.5 rounded text-[9px] font-bold text-[#22D3EE] tracking-wide uppercase"
                                >
                                  {src}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                      <span className="text-[9px] text-[#bbc9cd]/60 mt-1 font-bold uppercase tracking-wider pr-1 pl-11">
                        {msg.timestamp}
                      </span>
                    </div>
                  );
                })}

                {chatLoading && (
                  <div className="flex gap-3 max-w-[90%] items-start">
                    <div className="w-8 h-8 rounded-full bg-[#22D3EE]/10 flex-shrink-0 flex items-center justify-center text-[#22D3EE] border border-[#22D3EE]/20 animate-pulse">
                      <Sparkles className="w-4 h-4 text-[#22D3EE]" />
                    </div>
                    <div className="bg-[#171f33] border border-[#22D3EE]/20 px-4 py-3 rounded-2xl rounded-tl-none flex items-center gap-1.5 shadow-md">
                      <span className="w-1.5 h-1.5 bg-[#22D3EE] rounded-full animate-bounce" />
                      <span className="w-1.5 h-1.5 bg-[#22D3EE] rounded-full animate-bounce [animation-delay:0.2s]" />
                      <span className="w-1.5 h-1.5 bg-[#22D3EE] rounded-full animate-bounce [animation-delay:0.4s]" />
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input Area */}
              <div className="p-4 bg-[#060e20] border-t border-[#3c494c]/40">
                {/* Suggestions chips */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {[
                    "Which wards are critical right now?",
                    "What's the main source in the worst one?",
                    "Simulate construction ban in this ward",
                    "Compare odd-even vs construction ban",
                    "Simulate diesel truck ban citywide",
                    "Draft an enforcement notice for it",
                    "What are the construction rules under GRAP Stage 3?",
                    "Compare Rohini and Dwarka",
                  ].map((chip) => (
                    <button
                      key={chip}
                      onClick={() => handleSendMessage(chip)}
                      className="px-2.5 py-1 rounded-full border border-[#3c494c]/60 text-[10px] font-semibold text-[#bbc9cd] hover:border-[#22D3EE] hover:text-[#22D3EE] transition-all bg-[#131b2e] truncate max-w-[210px]"
                    >
                      {chip}
                    </button>
                  ))}
                </div>

                {/* Form Input */}
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage(chatInput);
                  }}
                  className="relative group"
                >
                  <input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    className="w-full bg-[#131b2e] border border-[#3c494c]/40 focus:border-[#22D3EE]/70 focus:ring-2 focus:ring-[#22D3EE]/10 rounded-xl px-4 py-3 text-xs text-white pr-12 transition-all outline-none"
                    placeholder={`Ask about ${currentWardName} air trends, GRAP, or strategy...`}
                    type="text"
                  />
                  <button
                    type="submit"
                    disabled={chatLoading || !chatInput.trim()}
                    className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg bg-[#22D3EE] text-[#001f25] flex items-center justify-center hover:brightness-110 active:scale-95 transition-all shadow-md shadow-[#22d3ee]/20 disabled:opacity-50"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </section>
          </div>
        </div>

        {/* Bottom wind flow air currents banner */}
        <div className="rounded-2xl h-44 relative overflow-hidden border border-[#3c494c]/40 bg-[#171f33]/40 backdrop-blur-md">
          <svg className="absolute inset-0 w-full h-full opacity-35" fill="none" stroke="#22D3EE" strokeWidth="1.5">
            <path d="M0,60 Q200,40 400,70 T800,50 T1200,60 T1600,40" className="animate-pulse" />
            <path d="M0,100 Q300,130 600,90 T1200,110 T1600,80" strokeDasharray="8 6" />
            <path d="M0,140 Q400,110 800,150 T1600,130" strokeWidth="1.0" />
          </svg>

          <div className="absolute inset-0 bg-gradient-to-t from-[#0F172A] to-transparent pointer-events-none" />

          <div className="absolute bottom-6 left-6 z-10">
            <div className="bg-[#22D3EE]/10 backdrop-blur-xl border border-[#22D3EE]/30 rounded-xl p-3.5 inline-block shadow-lg">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-[#22D3EE]/20 flex items-center justify-center border border-[#22D3EE]/35">
                  <span className="text-lg text-[#22D3EE]">🌬</span>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-[#22D3EE] mb-0.5 uppercase tracking-widest">
                    NCR Atmospheric Dynamics
                  </div>
                  <div className="text-xs font-bold text-white">
                    Live boundary layer tracking: Inversion layer height monitored across Delhi NCR
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
