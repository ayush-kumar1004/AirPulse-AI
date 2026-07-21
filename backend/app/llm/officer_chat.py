# Officer Chat Agent (LangGraph).
import logging

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from app.llm.llm_client import get_llm
from app.llm.tools import build_tools

logger = logging.getLogger(__name__)

# A ReAct agent spends one LLM request per reasoning step, and LangGraph's default
# recursion_limit of 25 allows roughly a dozen. On the free Gemini tier — 20
# requests per DAY — a single chat message could therefore consume the entire
# day's allowance. Six steps is ample for "check this ward's AQI, then its
# sources, then answer" while bounding the worst case.
MAX_AGENT_STEPS = 6

QUOTA_HINT = (
    "The AI model's free daily request limit has been reached. "
    "It resets around 12:30 PM IST. Air quality, forecast and source data are unaffected."
)


def chat(message: str, ward_id: str | None = None) -> dict:
    """Return {'reply', 'tools_used'} — tool-using answer grounded in live module data."""
    try:
        llm = get_llm(provider="gemini", temperature=0.0)
        tools = build_tools()

        system_prompt = (
            "You are an expert command center assistant for Delhi's air quality monitoring officers.\n"
            "You help officers understand why pollution is high, what forecast trends look like, "
            "and what recommendations or inspections are scheduled.\n"
            "You MUST answer questions by calling the actual tools provided. "
            "Do NOT make up values. Ground your answers strictly in tool outputs.\n"
            "If a ward ID or name is mentioned (e.g. Rohini is W02, Connaught Place is W01, etc.), call tools using that ward ID.\n"
            "If the officer asks a general question or doesn't specify a ward, but a context ward_id is supplied, use that ward_id.\n"
            "Keep your responses concise, professional, and clear."
        )

        # Build ReAct agent using langgraph prebuilt agent creator
        agent = create_react_agent(llm, tools, state_modifier=system_prompt)

        # Format prompt query with ward_id context if provided
        query = message
        if ward_id:
            query = f"{message} (Context Ward ID: {ward_id})"

        # Invoke agent
        response = agent.invoke(
            {"messages": [HumanMessage(content=query)]},
            config={"recursion_limit": MAX_AGENT_STEPS},
        )

        # Extract final reply and list of tools used
        messages = response.get("messages", [])
        if not messages:
            return {"reply": "Sorry, I encountered an issue processing your request.", "tools_used": []}

        final_reply = messages[-1].content

        tools_used = []
        for msg in messages:
            # Check for tool calls inside AI Messages
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    if tc["name"] not in tools_used:
                        tools_used.append(tc["name"])

        return {
            "reply": final_reply,
            "tools_used": tools_used
        }
    except Exception as e:
        logger.error(f"Error in officer chat agent: {e}", exc_info=True)
        if "429" in str(e) or "quota" in str(e).lower():
            return {"reply": QUOTA_HINT, "tools_used": []}
        return {
            "reply": f"Sorry, I encountered an error executing the chat agent: {str(e)}",
            "tools_used": []
        }
