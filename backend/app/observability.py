"""AirPulse AI - Structured Observability & Telemetry Service.

Provides structured logging and event tracking for:
  - Model prediction requests (horizon, output bounds, latency)
  - Agent tool executions (inputs, status, duration, error details)
  - RAG regulatory retrieval (query, cosine scores, citations)
  - What-If policy simulations (assumptions, sector mitigations, delta AQI)
  - In-memory event ring buffer for runtime inspection and health checks.
"""
from collections import deque
from datetime import datetime, timezone
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("airpulse.telemetry")

# In-memory circular buffer of recent structured telemetry events
_EVENT_BUFFER: deque = deque(maxlen=200)


def _record_event(event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Record a structured telemetry event into the circular buffer and standard logger."""
    record = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    _EVENT_BUFFER.append(record)
    
    # Also log in structured key-value format for log collectors
    status_str = f"status={record.get('status', 'OK')} " if "status" in record else ""
    dur_str = f"duration={record.get('duration_ms', 0):.1f}ms " if "duration_ms" in record else ""
    logger.info(f"[{event_type.upper()}] {status_str}{dur_str}| {json.dumps(payload, default=str)}")
    return record


def log_prediction_request(
    ward_id: str,
    horizon_hours: int,
    points_count: int,
    min_predicted_aqi: int,
    max_predicted_aqi: int,
    duration_ms: float,
    status: str = "SUCCESS",
    model_name: str = "LightGBM Regressor",
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Structured log for ML forecast inference calls."""
    payload = {
        "ward_id": ward_id,
        "horizon_hours": horizon_hours,
        "points_count": points_count,
        "min_predicted_aqi": min_predicted_aqi,
        "max_predicted_aqi": max_predicted_aqi,
        "model_name": model_name,
        "status": status,
        "duration_ms": round(duration_ms, 2),
    }
    if error:
        payload["error"] = error
    return _record_event("ml_forecast_inference", payload)


def log_tool_execution(
    tool_name: str,
    arguments: Dict[str, Any],
    status: str,
    duration_ms: float,
    error: Optional[str] = None,
    output_summary: Optional[str] = None,
) -> Dict[str, Any]:
    """Structured log for Officer Agent tool executions."""
    # Sanitize large arguments if necessary
    clean_args = {k: str(v)[:100] for k, v in arguments.items()}
    payload = {
        "tool_name": tool_name,
        "arguments": clean_args,
        "status": status,
        "duration_ms": round(duration_ms, 2),
    }
    if error:
        payload["error"] = error
    if output_summary:
        payload["output_summary"] = output_summary[:150]
    return _record_event("agent_tool_call", payload)


def log_rag_retrieval(
    query: str,
    category_filter: Optional[str],
    chunks_returned: int,
    top_similarity_score: float,
    citations: List[str],
    duration_ms: float,
    status: str = "SUCCESS",
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Structured log for RAG semantic search and legal retrieval."""
    payload = {
        "query": query[:120],
        "category_filter": category_filter,
        "chunks_returned": chunks_returned,
        "top_similarity_score": round(top_similarity_score, 4),
        "citations": citations[:4],
        "status": status,
        "duration_ms": round(duration_ms, 2),
    }
    if error:
        payload["error"] = error
    return _record_event("rag_retrieval", payload)


def log_simulation_run(
    ward_id: str,
    intervention_type: str,
    intensity: float,
    horizon_hours: int,
    baseline_aqi: int,
    simulated_aqi: int,
    reduction_points: float,
    percentage_reduction: float,
    top_affected_source: str,
    duration_ms: float,
    status: str = "SUCCESS",
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Structured log for policy simulation runs."""
    payload = {
        "ward_id": ward_id,
        "intervention_type": intervention_type,
        "intensity": round(intensity, 2),
        "horizon_hours": horizon_hours,
        "baseline_aqi": baseline_aqi,
        "simulated_aqi": simulated_aqi,
        "reduction_points": round(reduction_points, 1),
        "percentage_reduction": round(percentage_reduction, 1),
        "top_affected_source": top_affected_source,
        "status": status,
        "duration_ms": round(duration_ms, 2),
    }
    if error:
        payload["error"] = error
    return _record_event("policy_simulation", payload)


def log_model_evaluation(
    model_name: str,
    eval_samples: int,
    mae: float,
    rmse: float,
    mape: float,
    status: str,
    warning: Optional[str] = None,
) -> Dict[str, Any]:
    """Structured log for LightGBM model evaluation runs."""
    payload = {
        "model_name": model_name,
        "eval_samples": eval_samples,
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2),
        "status": status,
    }
    if warning:
        payload["warning"] = warning
    return _record_event("model_evaluation", payload)


def get_recent_telemetry_events(
    limit: int = 50,
    event_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve recent recorded events from circular buffer."""
    events = list(_EVENT_BUFFER)
    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]
    return events[-limit:]


def clear_telemetry_events() -> None:
    """Clear the event buffer (useful for test isolation)."""
    _EVENT_BUFFER.clear()

