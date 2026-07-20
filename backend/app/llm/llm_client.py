# Person C — thin factory returning a LangChain chat model. Gemini primary, auto-falls back to
# whichever of Claude/GPT/Kimi actually has a key set.
import logging

import httpx

from app.config import get_settings
from langchain_openai import ChatOpenAI

settings = get_settings()
logger = logging.getLogger(__name__)

GEMINI_LIST_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Model names that support generateContent but are wrong for a chat agent.
_GEMINI_EXCLUDE = ("image", "tts", "audio", "live", "embedding", "aqa", "gemma", "imagen", "veo")

# Resolved once per process so we don't hit ListModels on every chat message.
_resolved_gemini_model: str | None = None


def _resolve_gemini_model(api_key: str, preferred: str) -> str:
    """Pick a Gemini model this key can actually use.

    Hardcoded names rot: "gemini-3.5-flash" never existed, and Google then
    retired "gemini-2.5-flash" for new keys ("404 ... no longer available to new
    users"). So instead of trusting the configured name, ask the API what this
    key offers and choose: the configured model if listed, else Google's rolling
    "gemini-flash-latest" alias, else the newest flash model, else anything that
    can chat. Falls back to the configured name if the lookup itself fails.
    """
    global _resolved_gemini_model
    if _resolved_gemini_model:
        return _resolved_gemini_model

    pick = preferred
    try:
        resp = httpx.get(
            GEMINI_LIST_MODELS_URL,
            params={"key": api_key, "pageSize": 200},
            timeout=10.0,
        )
        resp.raise_for_status()
        usable = [
            m["name"].removeprefix("models/")
            for m in resp.json().get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
            and not any(x in m["name"] for x in _GEMINI_EXCLUDE)
        ]
        if usable:
            flash = sorted((m for m in usable if "flash" in m), reverse=True)
            if preferred in usable:
                pick = preferred
            elif "gemini-flash-latest" in usable:
                pick = "gemini-flash-latest"
            elif flash:
                pick = flash[0]
            else:
                pick = sorted(usable, reverse=True)[0]
    except Exception as e:
        logger.warning("Gemini model discovery failed (%s) — using configured '%s'.", e, preferred)

    if pick != preferred:
        logger.info("Gemini model '%s' not available to this key — using '%s'.", preferred, pick)
    _resolved_gemini_model = pick
    return pick


def get_llm(provider: str = "gemini", temperature: float = 0.0):
    """Return a configured LangChain chat model.
    provider: 'gemini' (default) | 'claude' | 'gpt' | 'kimi'
    """
    gemini_key = (settings.gemini_api_key or "").strip()
    anthropic_key = (settings.anthropic_api_key or "").strip()
    openai_key = (settings.openai_api_key or "").strip()
    kimi_key = (settings.kimi_api_key or "").strip()

    # Auto-fallback if the requested provider's key is not set.
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
            model=_resolve_gemini_model(gemini_key, settings.gemini_model or "gemini-flash-latest"),
            google_api_key=gemini_key,
            temperature=temperature,
        )
    elif provider == "claude":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-3-5-sonnet-20240620",
            api_key=anthropic_key,
            temperature=temperature,
        )
    elif provider == "gpt":
        return ChatOpenAI(model="gpt-4o-mini", api_key=openai_key, temperature=temperature)
    elif provider == "kimi":
        return ChatOpenAI(
            model="moonshot-v1-8k",
            base_url="https://api.moonshot.cn/v1",
            api_key=kimi_key,
            temperature=temperature,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
