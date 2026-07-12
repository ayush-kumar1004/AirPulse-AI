import React, { useState, useEffect, useRef } from "react";
import { Sparkles, MapPin, Send, MessageSquare, History, ShieldAlert, Building, HelpCircle, LogOut, ArrowRight } from "lucide-react";
import { getRecommend, officerChat } from "../api/client";

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

export default function GovernmentDashboard() {
  const [recommendations, setRecommendations] = useState<any>(null);
  const [chatInput, setChatInput] = useState<string>("");
  const [chatLoading, setChatLoading] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "user",
      text: "Which ward should inspectors visit first?",
      timestamp: "14:22 • Officer",
    },
    {
      sender: "ai",
      text: "I recommend prioritizing Rohini. The current AQI is 241 (Severe). Analysis indicates this is 62% driven by localized traffic congestion at the Outer Ring Road intersection.\n\nOur predictive model suggests it will stay in the Severe range through tomorrow morning unless immediate flow restrictions are implemented.",
      timestamp: "14:23 • AI Agent",
      sources: ["AQI Sensor #88", "Traffic API", "ML-Forecast"],
    },
  ]);

  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom of chat history only
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, chatLoading]);

  // Load recommendations
  useEffect(() => {
    const loadRecommendations = async () => {
      try {
        const res = await getRecommend("W02");
        setRecommendations(res);
      } catch (err) {
        console.error("Error loading recommendations:", err);
      }
    };
    loadRecommendations();
  }, []);

  // Card mouse tracking glow
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    card.style.setProperty("--mouse-x", `${x}px`);
    card.style.setProperty("--mouse-y", `${y}px`);
  };

  // Chat send message
  const handleSendMessage = async (text: string) => {
    if (!text.trim() || chatLoading) return;
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")} • Officer`;

    // Add user message
    const userMsg: Message = { sender: "user", text, timestamp: timeStr };
    setMessages((prev) => [...prev, userMsg]);
    setChatInput("");
    setChatLoading(true);

    try {
      const res = await officerChat({ message: text, ward_id: "W02" });
      const aiTimeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")} • AI Agent`;

      const sourcesMapped = res.tools_used?.map((t: string) => {
        if (t === "get_aqi" || t === "get_heatmap") return "AQI Sensor #88";
        if (t === "get_source_attribution") return "Traffic API";
        if (t === "get_predict") return "ML-Forecast";
        return t;
      }) || ["AI Inference"];

      const aiMsg: Message = {
        sender: "ai",
        text: res.reply || "Response processed successfully.",
        timestamp: aiTimeStr,
        sources: sourcesMapped,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error("Chat error:", err);
      const aiMsg: Message = {
        sender: "ai",
        text: "I am having trouble connecting to the live AirPulse API. However, based on static fallback data, Rohini remains the highest priority inspection zone due to elevated particulate levels.",
        timestamp: timeStr.replace("Officer", "AI Agent"),
        sources: ["Local Cache"],
      };
      setMessages((prev) => [...prev, aiMsg]);
    } finally {
      setChatLoading(false);
    }
  };

  // Fallbacks matching Stitch
  const fallbackActions: ActionRecommendation[] = [
    {
      action: "Restrict diesel trucks on Ring Road, 6-10 AM",
      target: "Ring Road corridor",
      urgency: "high",
      reason: "Traffic is 45% of load; severe forecast tomorrow AM",
    },
    {
      action: "Inspect Okhla construction sites",
      target: "Okhla Industrial Area",
      urgency: "medium",
      reason: "Dust levels rising; sensor #422 abnormal",
    },
    {
      action: "Increase water sprinkling",
      target: "Civil Lines",
      urgency: "low",
      reason: "Localized PM10 surge detected",
    },
  ];

  const fallbackPriority: InspectionItem[] = [
    { site: "Puri Site", ward: "Rohini", reason: "Dust", priority: 1 },
    { site: "DMRC", ward: "Central", reason: "Traffic", priority: 2 },
    { site: "Indraprastha", ward: "IP Estate", reason: "Grid Load", priority: 3 },
  ];

  const actionsToRender = recommendations && recommendations.actions && recommendations.actions.length > 0
    ? recommendations.actions
    : fallbackActions;

  const priorityToRender = recommendations && recommendations.inspection_priority && recommendations.inspection_priority.length > 0
    ? recommendations.inspection_priority
    : fallbackPriority;

  return (
    <div className="flex-1 w-full h-full overflow-y-auto p-6 md:p-8 space-y-8 bg-[#0F172A] text-[#dae2fd] font-sans pb-24">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* Page Header Area */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">Urban Command Center</h1>
            <p className="text-sm text-[#bbc9cd] mt-1">Intelligence for NCR Environmental Management</p>
          </div>
          <div className="flex gap-3">
            <div className="bg-[#171f33] px-4 py-2 rounded-xl border border-[#3c494c]/40 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#4ae176] animate-pulse"></div>
              <span className="text-[10px] font-bold text-white uppercase tracking-wider">System Status: Optimal</span>
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
                background: "radial-gradient(1000px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.05), transparent 80%), rgba(30, 41, 59, 0.5)",
              }}
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-[#22D3EE]" />
                  AI Priority Actions
                </h2>
                <div className="bg-[#22D3EE]/10 text-[#22D3EE] border border-[#22D3EE]/25 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-[#22D3EE]" />
                  Generated by AI
                </div>
              </div>

              {/* Action Cards List */}
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
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${urgencyBadge}`}>
                          {act.urgency}
                        </span>
                      </div>
                      <p className="text-xs text-[#bbc9cd] mb-3 pl-2">{act.reason}</p>
                      <div className="flex items-center gap-4 pl-2">
                        <div className="flex items-center gap-1.5 text-[10px] font-bold text-[#bbc9cd] uppercase bg-[#171f33] px-2.5 py-1 rounded">
                          <MapPin className="w-3.5 h-3.5 text-[#22D3EE]" />
                          {act.target}
                        </div>
                        <button className="ml-auto text-xs font-bold text-[#22D3EE] hover:underline uppercase tracking-wider">
                          Execute Action
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            {/* Inspection Priority Table */}
            <section className="glass-panel border border-[#334155]/50 rounded-2xl overflow-hidden bg-[#1E293B]/40">
              <div className="px-6 py-4 border-b border-[#3c494c]/40 bg-[#171f33]">
                <h3 className="text-[10px] font-bold text-[#bbc9cd] tracking-widest uppercase">Inspection Priority Queue</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-[#131b2e] border-b border-[#3c494c]/30">
                    <tr>
                      <th className="px-6 py-3.5 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">Site</th>
                      <th className="px-6 py-3.5 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">Ward</th>
                      <th className="px-6 py-3.5 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">Reason</th>
                      <th className="px-6 py-3.5 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">Priority</th>
                      <th className="px-6 py-3.5 text-[10px] font-bold text-[#bbc9cd] uppercase tracking-wider">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#3c494c]/20">
                    {priorityToRender.map((row: InspectionItem, idx: number) => {
                      const priorityColor = row.priority === 1
                        ? "bg-red-500/20 text-red-400 border border-red-500/30"
                        : row.priority === 2
                          ? "bg-orange-500/20 text-orange-400 border border-orange-500/30"
                          : "bg-green-500/20 text-green-400 border border-green-500/30";

                      return (
                        <tr key={idx} className="hover:bg-[#1E293B]/40 transition-colors">
                          <td className="px-6 py-4 text-xs font-bold text-white">{row.site}</td>
                          <td className="px-6 py-4 text-xs text-[#bbc9cd]">{row.ward || `Ward ${row.ward_id}`}</td>
                          <td className="px-6 py-4 text-xs text-[#bbc9cd]">{row.reason}</td>
                          <td className="px-6 py-4">
                            <span className={`w-6 h-6 rounded flex items-center justify-center text-xs font-bold ${priorityColor}`}>
                              {row.priority}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <button className="text-[#22D3EE] hover:text-white transition-colors">
                              <ArrowRight className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          </div>

          {/* Right Column (5 cols): Officer Assistant Chat Panel */}
          <div className="lg:col-span-5 h-[650px] flex flex-col">
            <section
              onMouseMove={handleMouseMove}
              className="p-0 border border-[#334155]/50 rounded-2xl relative overflow-hidden bg-[#1E293B]/50 backdrop-blur-md flex flex-col h-full shadow-inner-cyan"
              style={{
                background: "radial-gradient(800px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), rgba(34, 211, 238, 0.05), transparent 80%), rgba(30, 41, 59, 0.5)",
              }}
            >
              {/* Chat Header */}
              <div className="p-4 border-b border-[#3c494c]/40 flex items-center justify-between bg-[#171f33]">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#22D3EE]/25 flex items-center justify-center text-[#22D3EE] border border-[#22D3EE]/20 shadow-lg">
                    <MessageSquare className="w-5 h-5 text-[#22D3EE]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white tracking-tight">Ask AirPulse</h3>
                    <div className="flex items-center gap-1 mt-0.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#4ae176] animate-pulse"></div>
                      <span className="text-[9px] text-[#bbc9cd] font-bold tracking-wider uppercase">AI AGENT ONLINE</span>
                    </div>
                  </div>
                </div>
                <button className="p-2 text-[#bbc9cd] hover:text-white transition-colors">
                  <History className="w-4 h-4" />
                </button>
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
                            className={`px-4 py-3 rounded-2xl border shadow-md ${isUser
                                ? "bg-[#1E293B] border-[#3c494c]/40 rounded-tr-none text-[#dae2fd]"
                                : "bg-[#171f33] border-[#22D3EE]/20 rounded-tl-none text-[#dae2fd] whitespace-pre-line leading-relaxed text-xs"
                              }`}
                          >
                            <p className="text-xs">{msg.text}</p>
                          </div>
                          {!isUser && msg.sources && msg.sources.length > 0 && (
                            <div className="flex items-center gap-2 flex-wrap pl-1">
                              <span className="text-[9px] font-bold text-[#bbc9cd] uppercase tracking-wider">Sources:</span>
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
                <div className="flex flex-wrap gap-2 mb-4">
                  {["Simulate impact", "Compare wards", "Draft alert"].map((chip) => (
                    <button
                      key={chip}
                      onClick={() => handleSendMessage(chip)}
                      className="px-3 py-1 rounded-full border border-[#3c494c]/60 text-[10px] font-bold text-[#bbc9cd] hover:border-[#22D3EE] hover:text-[#22D3EE] transition-all bg-[#131b2e]"
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
                    placeholder="Ask about air trends, impact, or strategy..."
                    type="text"
                  />
                  <button
                    type="submit"
                    className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg bg-[#22D3EE] text-[#001f25] flex items-center justify-center hover:brightness-110 active:scale-95 transition-all shadow-md shadow-[#22d3ee]/20"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </section>
          </div>

        </div>

        {/* Bottom wind flow air currents banner */}
        <div className="rounded-2xl h-56 relative overflow-hidden border border-[#3c494c]/40 bg-[#171f33]/40 backdrop-blur-md">
          {/* animated wind SVG curves in background */}
          <svg className="absolute inset-0 w-full h-full opacity-35" fill="none" stroke="#22D3EE" strokeWidth="1.5">
            <path d="M0,80 Q200,60 400,90 T800,70 T1200,80 T1600,60" className="animate-pulse" />
            <path d="M0,120 Q300,150 600,110 T1200,130 T1600,100" strokeDasharray="8 6" className="animate-ai-pulse" />
            <path d="M0,160 Q400,130 800,170 T1600,150" strokeWidth="1.0" />
          </svg>

          <div className="absolute inset-0 bg-gradient-to-t from-[#0F172A] to-transparent pointer-events-none" />

          <div className="absolute bottom-6 left-6 z-10">
            <div className="bg-[#22D3EE]/10 backdrop-blur-xl border border-[#22D3EE]/30 rounded-xl p-4 inline-block shadow-lg">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-[#22D3EE]/20 flex items-center justify-center border border-[#22D3EE]/35">
                  <span className="text-xl text-[#22D3EE]">🌬</span>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-[#22D3EE] mb-1 uppercase tracking-widest">NCR Regional Air Flow</div>
                  <div className="text-sm font-bold text-white">Tracking particulate migration from thermal plants</div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
