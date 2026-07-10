# thin factory returning a LangChain chat model.
import os
from app.config import get_settings
from langchain_openai import ChatOpenAI

settings = get_settings()


def get_llm(provider: str = "gemini", temperature: float = 0.0):
    """Return a configured LangChain chat model.
    provider: 'gemini' (default) | 'claude' | 'gpt' | 'kimi'
    """
    gemini_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
    anthropic_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
    openai_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
    kimi_key = settings.kimi_api_key or os.environ.get("KIMI_API_KEY")

    if gemini_key:
        gemini_key = gemini_key.strip()
    if anthropic_key:
        anthropic_key = anthropic_key.strip()
    if openai_key:
        openai_key = openai_key.strip()
    if kimi_key:
        kimi_key = kimi_key.strip()

    # Auto-fallback if requested provider's key is not set
    if provider == "gemini" and not gemini_key:
        if anthropic_key:
            provider = "claude"
        elif openai_key:
            provider = "gpt"
        elif kimi_key:
            provider = "kimi"
    elif provider == "claude" and not anthropic_key:
        if gemini_key:
            provider = "gemini"
        elif openai_key:
            provider = "gpt"

    if provider == "gemini":
        if not gemini_key:
            raise ValueError("Gemini API key is not configured. Set GEMINI_API_KEY.")
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model or "gemini-3.5-flash",
            google_api_key=gemini_key,
            temperature=temperature
        )
    elif provider == "claude":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-3-5-sonnet-20240620",
            api_key=anthropic_key,
            temperature=temperature
        )
    elif provider == "gpt":
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=openai_key,
            temperature=temperature
        )
    elif provider == "kimi":
        return ChatOpenAI(
            model="moonshot-v1-8k",
            base_url="https://api.moonshot.cn/v1",
            api_key=kimi_key,
            temperature=temperature
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
