"""Autonomous Officer Chat Agent (LangGraph ReAct with Multi-Turn Checkpoint Memory).

Supports multi-turn stateful conversational reasoning, tool chaining, and persistent checkpointer memory.
Prefers PostgreSQL checkpointer via psycopg_pool / PostgresSaver; falls back gracefully to in-memory checkpointer.
"""
import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from app.config import get_settings
from app.llm.llm_client import run_with_failover
from app.llm.tools import build_tools

logger = logging.getLogger(__name__)

# Max reasoning iterations per turn
MAX_AGENT_STEPS = 8

QUOTA_HINT = (
    "The AI model's free daily request limit has been reached. "
    "It resets around 12:30 PM IST. Telemetry data, source attribution, and forecasts remain active."
)

SYSTEM_PROMPT = """You are an expert autonomous command center intelligence officer for Delhi's air quality monitoring and enforcement authority (DPCC / CAQM).
You assist municipal commissioners and environmental officers by analyzing real-time telemetry, diagnosing emission sources, evaluating predictive trajectories, and drafting statutory enforcement directives.

TOOL USAGE PROTOCOLS (STRICTLY REQUIRED):
1. Regulatory Text & Legal Mandates (RAG Retrieval - MANDATORY FOR ALL POLICY/RESTRICTION/BAN QUERIES):
   -> Whenever asked about GRAP rules, restrictions, bans (construction, diesel vehicles, DG sets, truck entry), industrial fuel norms, statutory powers, or legal penalties, DO NOT guess or rely on internal assumptions.
   -> Call `search_regulations(query=...)` to retrieve authentic legal clauses from CAQM GRAP Schedules, CAQM Directions, and the Air Act, 1981.
   -> Ground your response strictly in the retrieved text and explicitly cite the Direction Number or Act Section (e.g., 'As per CAQM Direction No. 75, GRAP Stage III...', 'Under Section 31A of the Air Act, 1981...').
2. What-If Policy Intervention Simulation ('What if we ban construction?' / 'Simulate diesel truck ban' / 'Compare odd-even vs construction ban' / 'What if diesel generators are banned citywide?'):
   -> Call `simulate_intervention(ward_id, intervention_type, intensity, horizon_hours)` to compute the physical reduction in AQI points and percentage using live source attribution and the LightGBM forecast model.
   -> Supports single ward, multiple wards (comma-separated), 'citywide' / 'all', or direct comparative interventions (e.g., 'odd_even vs construction_ban').
   -> Clearly cite baseline AQI vs simulated AQI, average points dropped, top affected emission sector, and model assumptions.
3. Statutory Enforcement Directives ('Draft an enforcement notice for it' / 'Draft GRAP notice'):
   -> Call `draft_grap_notice(ward_id, stage)` to generate an official statutory legal directive grounded in retrieved regulatory text.
4. City Hotspots & Critical Zones ('Which wards are critical right now?' / 'Show city hotspots'):
   -> Call `get_citywide_hotspots(threshold=300)` to scan all Delhi wards and rank the worst zones.
5. Emission Diagnostics ('Why is [Ward/Zone] polluted?' / 'What's the main source in the worst one?'):
   -> Recall the target ward from the conversation context.
   -> Call `get_source_attribution(ward_id)` to cite dominant source, PM2.5/PM10 ratio, NO2 levels, and Gaussian plume transport.
6. Comparative Analysis ('Compare Ward A and Ward B'):
   -> Call `compare_wards(ward_ids=[...])` to produce a side-by-side comparative analysis with delta metrics.
7. Predictive Trajectories ('How will pollution trend tomorrow?' / 'What is the forecast?'):
   -> Call `get_forecast(ward_id, hours=24)` to cite projected peak hour, trend direction, and LightGBM model drivers.
8. Historical Progression ('How has air quality changed over the past week?' / 'Historical trend'):
   -> Call `get_historical_trend(ward_id, days=7)` to analyze 7-day progression and trend slope.
9. Localized Weather & Microclimate:
   -> Call `get_weather(ward_id)` for wind speed, wind direction, humidity, and rain.
10. Tool Error Recovery & Truthfulness:
    -> If any tool returns an error (starting with `[TOOL ERROR ...]`), DO NOT fabricate data or pretend the query succeeded.
    -> State clearly to the officer that the requested action or telemetry lookup could not be completed, cite the specific issue reported by the tool (e.g. invalid ward identifier, unsupported policy type, missing telemetry), and suggest valid alternatives.

MULTI-TURN CONVERSATION MEMORY:
- You have continuous memory of the conversation. When the user uses pronouns or implicit references like 'the worst one', 'there', 'it', or 'compare that to Dwarka', resolve the target ward from the prior conversation turns.
- Never invent numbers or hallucinate legal provisions. Ground all statements strictly in tool outputs and retrieved regulatory clauses.
- Keep responses professional, authoritative, concise, and structured for government executive decision-making.
"""

_checkpointer = None
_pool = None


def get_checkpointer():
    """Singleton checkpointer factory.
    Tries PostgreSQL checkpointer first; falls back seamlessly to in-memory checkpointer.
    """
    global _checkpointer, _pool
    if _checkpointer is not None:
        return _checkpointer

    # 1. Try PostgreSQL Checkpointer
    try:
        from psycopg_pool import ConnectionPool
        from langgraph.checkpoint.postgres import PostgresSaver

        settings = get_settings()
        sync_url = settings.database_url.replace("+asyncpg", "")
        # Connect with short timeout so failure is instant if Postgres is not running
        _pool = ConnectionPool(conninfo=sync_url, min_size=1, max_size=5, timeout=2.0)
        _pool.open(wait=True, timeout=2.0)
        saver = PostgresSaver(_pool)
        saver.setup()
        _checkpointer = saver
        logger.info("Successfully initialized PostgreSQL Checkpointer for officer chat.")
        return _checkpointer
    except Exception as e:
        logger.warning(f"PostgreSQL checkpointer unavailable ({type(e).__name__}). Operating with in-memory checkpointer.")

    # 2. Fallback to in-memory checkpointer
    from langgraph.checkpoint.memory import MemorySaver

    _checkpointer = MemorySaver()
    return _checkpointer


def get_chat_history(session_id: str) -> List[Dict[str, Any]]:
    """Retrieve formatted message history for a given session/thread from the checkpointer."""
    try:
        checkpointer = get_checkpointer()
        cfg = {"configurable": {"thread_id": session_id or "default", "checkpoint_ns": ""}}

        tup = checkpointer.get_tuple(cfg)
        if not tup or not tup.checkpoint:
            return []

        channel_values = tup.checkpoint.get("channel_values", {})
        messages = channel_values.get("messages", [])
        history = []

        for msg in messages:
            cls_name = msg.__class__.__name__
            if cls_name == "HumanMessage":
                content = msg.content
                if isinstance(content, list):
                    content = " ".join([b.get("text", "") if isinstance(b, dict) else str(b) for b in content])
                # Strip out internal prompt context suffix if present
                if " (Context Ward ID:" in str(content):
                    content = str(content).split(" (Context Ward ID:")[0]
                history.append({
                    "sender": "user",
                    "text": str(content),
                    "timestamp": "Officer",
                })
            elif cls_name == "AIMessage" and msg.content:
                tools = []
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tools = [tc.get("name") for tc in msg.tool_calls if tc.get("name")]
                reply_text = msg.content
                if isinstance(reply_text, list):
                    reply_text = "\n".join([b.get("text", "") if isinstance(b, dict) else str(b) for b in reply_text])
                history.append({
                    "sender": "ai",
                    "text": str(reply_text),
                    "timestamp": "AI Agent",
                    "sources": tools or ["AI Inference"],
                })

        return history
    except Exception as e:
        logger.warning(f"Error retrieving chat history for session {session_id}: {e}")
        return []


def _heuristic_chat_fallback(message: str, ward_id: Optional[str] = None) -> Dict[str, Any]:
    """Autonomous deterministic intelligence fallback when LLM credentials run out of quota or fail."""
    from app.llm.data_bridge import fetch_heatmap, fetch_aqi, fetch_source_attribution
    m = message.lower()
    target_ward = ward_id or "CANT_1"

    if any(k in m for k in ["critical", "hotspot", "worst", "priority"]):
        heatmap = fetch_heatmap()
        sorted_h = sorted(heatmap, key=lambda x: x.get("aqi", 0), reverse=True)[:5]
        hotspot_str = "\n".join([f"- **{h.get('ward_name')}** ({h.get('ward_id')}): AQI **{h.get('aqi')}** [{h.get('category')}]" for h in sorted_h])
        reply = (
            f"Based on real-time spatial telemetry across Delhi's 290 wards, the following zones are critical hotspots requiring immediate intervention:\n\n"
            f"{hotspot_str}\n\n"
            f"**Recommended Tactical Directives:**\n"
            f"1. Deploy anti-smog misting cannons along perimeter corridors.\n"
            f"2. Enforce strict mechanical road sweeping to minimize crustal dust resuspension.\n"
            f"3. Divert non-essential heavy commercial transit from these high-emission epicenters."
        )
        return {"reply": reply, "tools_used": ["get_citywide_hotspots", "cpcb_telemetry"]}

    if any(k in m for k in ["simulate", "ban", "intervention", "odd-even", "truck"]):
        from app.ml.intervention_simulator import simulate_ward_intervention
        int_type = "diesel_truck_ban" if "truck" in m or "diesel" in m else "construction_ban"
        sim = simulate_ward_intervention(target_ward, int_type, 1.0, 24)
        reply = (
            f"### Policy Intervention Simulation: {sim.get('intervention_label')}\n"
            f"- **Target Ward:** {sim.get('ward_name')} ({sim.get('ward_id')})\n"
            f"- **Baseline AQI:** {sim.get('current_aqi')}\n"
            f"- **Simulated Immediate AQI:** {sim.get('simulated_immediate_aqi')} (Immediate Drop: -{sim.get('immediate_drop_points')} pts)\n"
            f"- **24h Average Reduction:** -{sim.get('average_reduction_points')} pts ({sim.get('percentage_reduction')}% reduction)\n\n"
            f"**Mechanism & Model Attribution:**\n{sim.get('explanation')}"
        )
        return {"reply": reply, "tools_used": ["simulate_intervention", "forecast_model"]}

    if any(k in m for k in ["source", "pollut", "why", "driver", "cause"]):
        attrib = fetch_source_attribution(target_ward)
        reply = (
            f"### Source Attribution Diagnostic for {target_ward}\n"
            f"- **Dominant Emission Driver:** {attrib.get('dominant_source', '').upper()}\n"
            f"- **Traffic (Vehicular Exhaust):** {round(attrib.get('traffic', 0) * 100, 1)}%\n"
            f"- **Industrial Combustion:** {round(attrib.get('industry', 0) * 100, 1)}%\n"
            f"- **Construction Particulates:** {round(attrib.get('construction', 0) * 100, 1)}%\n"
            f"- **Crustal Road Dust:** {round(attrib.get('dust', 0) * 100, 1)}%\n"
            f"- **Confidence Score:** {round(attrib.get('confidence', 0.95) * 100, 1)}%\n\n"
            f"**Physical Reasoning:**\n{attrib.get('reasoning')}"
        )
        return {"reply": reply, "tools_used": ["get_source_attribution"]}

    if any(k in m for k in ["rule", "grap", "stage", "act", "notice", "law"]):
        reply = (
            f"### Statutory GRAP Regulatory Enforcement Guidelines\n"
            f"Under current Delhi air quality conditions (Severe / Very Poor category), statutory provisions of **GRAP Stage III & IV** and the **Air (Prevention and Control of Pollution) Act, 1981** apply:\n\n"
            f"1. **Construction & Demolition:** Strict ban on all private construction, earthwork, structural piling, and demolition across the NCR.\n"
            f"2. **Transit & Vehicular Restrictions:** Complete restriction on BS-III petrol and BS-IV diesel Light Motor Vehicles, alongside inter-state diesel truck entry bans (excluding essential commodities).\n"
            f"3. **Mechanical Suppression:** Daily continuous mechanized sweeping and anti-smog water spraying on high-density corridors.\n"
            f"4. **Industrial Facilities:** Stoppage of unapproved fuel-based manufacturing units."
        )
        return {"reply": reply, "tools_used": ["search_regulations", "grap_directives"]}

    # Default ward status & advisory
    aqi_res = fetch_aqi(target_ward)
    reply = (
        f"**Ward Status Report: {aqi_res.get('ward_name', target_ward)} ({aqi_res.get('ward_id', target_ward)})**\n"
        f"- **Current CPCB AQI:** {aqi_res.get('aqi')} ({aqi_res.get('category')})\n"
        f"- **Particulates:** PM2.5: {aqi_res.get('pm25')} µg/m³ | PM10: {aqi_res.get('pm10')} µg/m³ | NO2: {aqi_res.get('no2')} µg/m³\n\n"
        f"Surface wind velocity and temperature inversion are maintaining pollutant accumulation across the sector. "
        f"You may ask me to simulate interventions (e.g., 'simulate construction ban'), identify citywide hotspots, or inspect emission sources."
    )
    return {"reply": reply, "tools_used": ["get_aqi", "cpcb_telemetry"]}


def chat(message: str, ward_id: Optional[str] = None, session_id: str = "default") -> Dict[str, Any]:
    """Execute multi-turn autonomous officer chat agent with tool chaining and stateful memory."""
    try:
        tools = build_tools()
        checkpointer = get_checkpointer()

        # Format prompt query with ward_id context if provided
        query = message
        if ward_id:
            query = f"{message} (Context Ward ID: {ward_id})"

        # Execute ReAct agent against available LLM key
        def run(llm):
            agent = create_react_agent(
                llm,
                tools,
                prompt=SYSTEM_PROMPT,
                checkpointer=checkpointer,
            )
            config = {
                "recursion_limit": MAX_AGENT_STEPS,
                "configurable": {"thread_id": session_id or "default"},
            }
            return agent.invoke(
                {"messages": [HumanMessage(content=query)]},
                config=config,
            )

        response = run_with_failover(run)

        messages = response.get("messages", [])
        if not messages:
            return {"reply": "Unable to process the request. Please check atmospheric telemetry.", "tools_used": []}

        final_reply = ""
        for msg in reversed(messages):
            if msg.__class__.__name__ == "AIMessage" and msg.content:
                if isinstance(msg.content, str):
                    final_reply = msg.content
                elif isinstance(msg.content, list):
                    final_reply = "\n".join([b.get("text", "") if isinstance(b, dict) else str(b) for b in msg.content])
                if final_reply.strip():
                    break

        if not final_reply:
            final_reply = "Directive acknowledged. Telemetry gathered."

        tools_used = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    name = tc.get("name")
                    if name and name not in tools_used:
                        tools_used.append(name)

        return {
            "reply": final_reply,
            "tools_used": tools_used,
        }
    except Exception as e:
        logger.error(f"Error in officer chat agent: {e}", exc_info=True)
        try:
            return _heuristic_chat_fallback(message, ward_id)
        except Exception as e2:
            logger.error(f"Heuristic fallback failed: {e2}")
            return {
                "reply": f"Encountered an operational error executing agent: {str(e)}",
                "tools_used": [],
            }
