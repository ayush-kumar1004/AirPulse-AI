# TODO: Person C — thin factory returning a LangChain chat model. Claude primary, GPT/Kimi fallback.
from app.config import get_settings

settings = get_settings()


def get_llm(provider: str = "claude"):
    """Return a configured LangChain chat model. TODO: Person C.
    provider: 'claude' (default) | 'gpt' | 'kimi'.
    """
    # Example:
    #   from langchain_anthropic import ChatAnthropic
    #   return ChatAnthropic(model="claude-opus-4-8", api_key=settings.anthropic_api_key)
    raise NotImplementedError("Person C: wire ChatAnthropic / ChatOpenAI / Kimi")
