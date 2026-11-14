# Person C — thin factory returning a LangChain chat model. Gemini primary, auto-falls back to
# whichever of Claude/GPT/Kimi actually has a key set.
import logging
from datetime import datetime, timedelta, timezone

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

# Keys known to be out of quota, mapped to the UTC time their allowance resets.
_exhausted_until: dict[str, datetime] = {}


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


def gemini_keys() -> list[str]:
    """Every configured Gemini key, in order, without duplicates.

    Reads GEMINI_API_KEY plus the comma-separated GEMINI_API_KEYS pool. Each key
    carries its own free-tier daily allowance, so N keys give N times the budget.
    """
    raw = [settings.gemini_api_key or ""] + (settings.gemini_api_keys or "").split(",")
    seen, out = set(), []
    for k in (x.strip() for x in raw):
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def mistral_keys() -> list[str]:
    """Every configured Mistral key, in order, without duplicates.

    Reads MISTRAL_API_KEY plus optional MISTRAL_API_KEYS pool.
    """
    raw = [settings.mistral_api_key or ""] + (settings.mistral_api_keys or "").split(",")
    seen, out = set(), []
    for k in (x.strip() for x in raw):
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _is_quota_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "429" in text or "quota" in text or "resourceexhausted" in text or "rate limit" in text or "rate_limit" in text


def _mark_exhausted(key: str) -> None:
    """Park a key until the daily quota resets (midnight US Pacific = UTC-8)."""
    now = datetime.now(timezone.utc)
    reset = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
    if reset <= now:
        reset += timedelta(days=1)
    _exhausted_until[key] = reset
    logger.warning(
        "LLM key ...%s hit its quota — skipping it until %s UTC.", key[-4:], reset.strftime("%H:%M %d-%b")
    )


def _available_gemini_keys() -> list[str]:
    now = datetime.now(timezone.utc)
    return [k for k in gemini_keys() if _exhausted_until.get(k, now) <= now]


def _available_mistral_keys() -> list[str]:
    now = datetime.now(timezone.utc)
    return [k for k in mistral_keys() if _exhausted_until.get(k, now) <= now]


def run_with_failover(work, temperature: float = 0.0):
    """Run `work(llm)`, moving to the next credential whenever one is out of quota.

    Tries credentials based on LLM_PROVIDER or available keys (Mistral, Gemini,
    OpenAI, Claude, Kimi). A key that reports a quota error is parked until
    the daily reset so later requests skip it immediately instead of spending a
    call to rediscover it. Non-quota errors are raised straight away.
    """
    preferred = (settings.llm_provider or "").strip().lower()
    m_keys = _available_mistral_keys()
    g_keys = _available_gemini_keys()

    attempts: list[tuple[str, str | None]] = []

    # If Mistral is explicitly requested, or if Mistral key is provided and preferred
    if preferred == "mistral" or (m_keys and not g_keys) or (m_keys and preferred != "gemini"):
        attempts.extend([("mistral", k) for k in m_keys])
        attempts.extend([("gemini", k) for k in g_keys])
    else:
        attempts.extend([("gemini", k) for k in g_keys])
        attempts.extend([("mistral", k) for k in m_keys])

    for name, key in (
        ("gpt", (settings.openai_api_key or "").strip()),
        ("claude", (settings.anthropic_api_key or "").strip()),
        ("kimi", (settings.kimi_api_key or "").strip()),
    ):
        if key and (name, key) not in attempts:
            attempts.append((name, key))

    if not attempts:
        raise ValueError(
            "No LLM credentials configured. Set MISTRAL_API_KEY (or GEMINI_API_KEY / "
            "OPENAI_API_KEY / ANTHROPIC_API_KEY / KIMI_API_KEY) in backend/.env."
        )

    last_error: Exception | None = None
    for provider, key in attempts:
        try:
            return work(get_llm(provider=provider, temperature=temperature, api_key=key))
        except Exception as e:
            if not _is_quota_error(e):
                raise
            last_error = e
            if provider in ("gemini", "mistral") and key:
                _mark_exhausted(key)
            else:
                logger.warning("%s provider is out of quota — trying the next credential.", provider)

    logger.error("Every configured LLM credential is out of quota.")
    raise last_error  # type: ignore[misc]


def get_llm(provider: str = "gemini", temperature: float = 0.0, api_key: str | None = None):
    """Return a configured LangChain chat model.
    provider: 'gemini' | 'mistral' | 'claude' | 'gpt' | 'kimi'
    api_key: use this specific credential instead of the configured default.
    """
    gemini_key = (api_key if provider == "gemini" and api_key else "") or next(iter(gemini_keys()), "")
    mistral_key = (api_key if provider == "mistral" and api_key else "") or next(iter(mistral_keys()), "")
    anthropic_key = (api_key if provider == "claude" and api_key else "") or (settings.anthropic_api_key or "").strip()
    openai_key = (api_key if provider == "gpt" and api_key else "") or (settings.openai_api_key or "").strip()
    kimi_key = (api_key if provider == "kimi" and api_key else "") or (settings.kimi_api_key or "").strip()

    # Auto-fallback if the requested provider's key is not set.
    if provider == "gemini" and not gemini_key:
        if mistral_key:
            provider = "mistral"
        elif anthropic_key:
            provider = "claude"
        elif openai_key:
            provider = "gpt"
        elif kimi_key:
            provider = "kimi"
    elif provider == "mistral" and not mistral_key:
        if gemini_key:
            provider = "gemini"
        elif openai_key:
            provider = "gpt"
        elif anthropic_key:
            provider = "claude"
        elif kimi_key:
            provider = "kimi"
    elif provider == "claude" and not anthropic_key:
        if mistral_key:
            provider = "mistral"
        elif gemini_key:
            provider = "gemini"
        elif openai_key:
            provider = "gpt"

    if provider == "mistral":
        if not mistral_key:
            raise ValueError("Mistral API key is not configured. Set MISTRAL_API_KEY.")
        return ChatOpenAI(
            model=settings.mistral_model or "mistral-small-latest",
            base_url="https://api.mistral.ai/v1",
            api_key=mistral_key,
            temperature=temperature,
            max_retries=1,
            request_timeout=25.0,
        )
    elif provider == "gemini":
        if not gemini_key:
            raise ValueError("Gemini API key is not configured. Set GEMINI_API_KEY.")
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=_resolve_gemini_model(gemini_key, settings.gemini_model or "gemini-flash-latest"),
            google_api_key=gemini_key,
            temperature=temperature,
            # Default is 6 retries. Every retry is billed against the free tier's
            # 20-requests-per-day allowance, and a *daily* quota 429 can never
            # succeed by retrying — so retries silently multiplied the cost of
            # each failure until the whole day's budget was gone.
            max_retries=0,
            request_timeout=10.0,
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
