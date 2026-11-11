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
        if "429" in str(e) or "quota" in str(e).lower():
            return {"reply": QUOTA_HINT, "tools_used": []}
        return {
            "reply": f"Encountered an operational error executing agent: {str(e)}",
            "tools_used": [],
        }
