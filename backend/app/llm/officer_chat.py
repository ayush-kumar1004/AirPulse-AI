# TODO: Person C — Officer Chat Agent (LangGraph). Answers e.g. "why is Zone 4 polluted today?"
# by CALLING the other modules as tools (app.llm.tools.build_tools()). Report which tools it used.
# MUST match schemas.ChatResponse.


def chat(message: str, ward_id: str | None = None) -> dict:
    """Return {'reply', 'tools_used'} — tool-using answer grounded in live module data."""
    raise NotImplementedError("Person C: implement officer chat agent (LangGraph + tools)")
