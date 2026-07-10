# Officer Chat Agent (LangGraph).
import logging
from app.llm.llm_client import get_llm
from app.llm.tools import build_tools
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


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
        response = agent.invoke({"messages": [HumanMessage(content=query)]})

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
        return {
            "reply": f"Sorry, I encountered an error executing the chat agent: {str(e)}",
            "tools_used": []
        }

