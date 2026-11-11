"""LangChain Agent Tools for the AirPulse Officer Chat Assistant.

Exposes comprehensive tools grounded in live modules:
  - compare_wards: Side-by-side comparative diagnostics across multiple Delhi wards
  - get_citywide_hotspots: Ranks citywide critical hotspots above given AQI threshold
  - get_source_attribution: Dynamic chemical ratios + Gaussian plume source apportionment
  - get_forecast: Recursive LightGBM 24h/48h/72h trajectory + peak anticipation
  - simulate_intervention: Multi-sector policy intervention simulator coupled with ML forecasting
  - search_regulations: Semantic RAG retrieval over official CAQM GRAP & Air Act legal text
  - draft_grap_notice: Legally formatted statutory GRAP enforcement directives
  - get_historical_trend: Multi-day historical telemetry analysis and trend slope
  - get_aqi, get_weather, get_recommendations
"""
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union

from langchain_core.tools import tool

from app.llm.data_bridge import (
    fetch_aqi,
    fetch_aqi_history,
    fetch_forecast,
    fetch_forecast_full,
    fetch_heatmap,
    fetch_source_attribution,
    fetch_weather,
)
from app.llm.recommendation_agent import recommend_actions
from app.observability import log_tool_execution

logger = logging.getLogger(__name__)


@tool
def get_aqi(ward_id: str) -> str:
    """Get current AQI and pollutant breakdown (PM2.5, PM10, NO2) for a specific Delhi ward."""
    t0 = time.monotonic()
    clean_id = str(ward_id or "").strip()
    if not clean_id:
        msg = "[TOOL ERROR - Invalid Parameter]: ward_id cannot be empty. Please specify a ward ID (e.g., 'CANT_1', 'W02')."
        log_tool_execution("get_aqi", {"ward_id": ward_id}, status="FAILED", duration_ms=0, error=msg)
        return msg

    try:
        res = fetch_aqi(clean_id)
        out = (
            f"Ward: {res['ward_name']} ({res['ward_id']})\n"
            f"- AQI: {res['aqi']} ({res['category']})\n"
            f"- Pollutants: PM2.5: {res['pm25']} µg/m³, PM10: {res['pm10']} µg/m³, NO2: {res['no2']} µg/m³\n"
            f"- Telemetry Timestamp: {res['updated_at']}"
        )
        dur = (time.monotonic() - t0) * 1000.0
        log_tool_execution("get_aqi", {"ward_id": clean_id}, status="SUCCESS", duration_ms=dur, output_summary=out)
        return out
    except Exception as e:
        dur = (time.monotonic() - t0) * 1000.0
        err_msg = f"[TOOL ERROR - Telemetry Synchronization Failed]: Unable to retrieve current AQI for ward '{clean_id}': {str(e)}"
        log_tool_execution("get_aqi", {"ward_id": clean_id}, status="FAILED", duration_ms=dur, error=str(e))
        return err_msg


@tool
def get_source_attribution(ward_id: str) -> str:
    """Get the dynamic percentage breakdown of pollution sources (traffic, construction, industry, dust),
    dominant source, chemical ratios (PM2.5/PM10, NO2), and Gaussian plume dispersion for a Delhi ward.
    Use this to answer questions like 'Why is this ward polluted?' or to diagnose the primary emission driver.
    """
    t0 = time.monotonic()
    clean_id = str(ward_id or "").strip()
    if not clean_id:
        msg = "[TOOL ERROR - Invalid Parameter]: ward_id cannot be empty. Please specify a ward ID (e.g., 'CANT_1', 'W02')."
        log_tool_execution("get_source_attribution", {"ward_id": ward_id}, status="FAILED", duration_ms=0, error=msg)
        return msg

    try:
        res = fetch_source_attribution(clean_id)
        dominant = res.get("dominant_source", "traffic").upper()
        shares = (
            f"Traffic: {res.get('traffic', 0.0)*100:.1f}%, "
            f"Industry: {res.get('industry', 0.0)*100:.1f}%, "
            f"Construction: {res.get('construction', 0.0)*100:.1f}%, "
            f"Dust: {res.get('dust', 0.0)*100:.1f}%"
        )
        raw = res.get("raw_factors", {})
        ratio_str = f"PM2.5/PM10 Ratio: {raw.get('pm25_pm10_ratio', 'N/A')}"
        no2_str = f"NO2: {raw.get('no2', 'N/A')} µg/m³"
        zone_str = (
            f"Nearest Industrial Cluster: {raw.get('nearest_zone', 'N/A')} "
            f"({raw.get('distance_km', 'N/A')} km, Plume Alignment: {raw.get('plume_alignment_factor', 'N/A')})"
        )

        out = (
            f"Source Attribution Diagnostics for Ward {clean_id}:\n"
            f"- Dominant Driver: {dominant}\n"
            f"- Contributions: {shares}\n"
            f"- Chemical Tracers: {ratio_str}, {no2_str}\n"
            f"- Dispersion Physics: {zone_str}\n"
            f"- Scientific Explanation: {res.get('reasoning', 'Chemical apportionment completed.')}\n"
            f"- Diagnostic Confidence: {res.get('confidence', 0.85)*100:.0f}%"
        )
        dur = (time.monotonic() - t0) * 1000.0
        log_tool_execution("get_source_attribution", {"ward_id": clean_id}, status="SUCCESS", duration_ms=dur, output_summary=out)
        return out
    except Exception as e:
        dur = (time.monotonic() - t0) * 1000.0
        err_msg = f"[TOOL ERROR - Source Attribution Failed]: Unable to compute source diagnostics for ward '{clean_id}': {str(e)}"
        log_tool_execution("get_source_attribution", {"ward_id": clean_id}, status="FAILED", duration_ms=dur, error=str(e))
        return err_msg


@tool
def get_forecast(ward_id: str, hours: int = 24) -> str:
    """Get recursive LightGBM AQI prediction forecast for 24, 48, or 72 hours in a specific Delhi ward.
    Returns projected trajectory, anticipated peak concentration, and top feature importance drivers.
    """
    t0 = time.monotonic()
    clean_id = str(ward_id or "").strip()
    if not clean_id:
        msg = "[TOOL ERROR - Invalid Parameter]: ward_id cannot be empty."
        log_tool_execution("get_forecast", {"ward_id": ward_id, "hours": hours}, status="FAILED", duration_ms=0, error=msg)
        return msg

    if not isinstance(hours, int) or hours <= 0:
        msg = f"[TOOL ERROR - Invalid Horizon]: Forecast horizon must be a positive integer (24, 48, or 72). Received: '{hours}'."
        log_tool_execution("get_forecast", {"ward_id": clean_id, "hours": hours}, status="FAILED", duration_ms=0, error=msg)
        return msg

    try:
        horizon = 72 if hours > 48 else (48 if hours > 24 else 24)
        full_res = fetch_forecast_full(clean_id, horizon)
        points = full_res.get("points", [])
        if not points:
            return f"[TOOL ERROR - Missing Forecast Points]: No prediction trajectory could be generated for ward {clean_id}."

        peak_pt = max(points, key=lambda p: p.get("predicted_aqi", 0))
        lines = [
            f"LightGBM AQI Forecast for Ward {clean_id} ({horizon}h horizon):",
            f"- Anticipated Peak AQI: {round(peak_pt['predicted_aqi'])} at {peak_pt['timestamp']}",
            f"- General Trend: {peak_pt.get('trend', 'stable').upper()}",
        ]

        if full_res.get("summary_reason"):
            lines.append(f"- Driver Summary: {full_res['summary_reason']}")

        # Sample 4-6 evenly spaced checkpoint hours
        step = max(1, len(points) // 6)
        sample_pts = points[::step][:6]
        lines.append("\nProjected Timeline Checkpoints:")
        for pt in sample_pts:
            lines.append(
                f"  • {pt['timestamp']}: Predicted AQI {round(pt['predicted_aqi'])} "
                f"(95% CI: [{round(pt.get('lower', 0))}-{round(pt.get('upper', 0))}])"
            )

        top_feats = full_res.get("top_features", [])
        if top_feats:
            lines.append("\nTop Model Feature Drivers:")
            for f in top_feats[:3]:
                lines.append(f"  • {f.get('feature')}: {f.get('importance', f.get('importance_percent', 0))}%")

        out = "\n".join(lines)
        dur = (time.monotonic() - t0) * 1000.0
        log_tool_execution("get_forecast", {"ward_id": clean_id, "hours": horizon}, status="SUCCESS", duration_ms=dur, output_summary=out)
        return out
    except Exception as e:
        dur = (time.monotonic() - t0) * 1000.0
        err_msg = f"[TOOL ERROR - Forecasting Failed]: Unable to calculate LightGBM prediction for ward '{clean_id}': {str(e)}"
        log_tool_execution("get_forecast", {"ward_id": clean_id, "hours": hours}, status="FAILED", duration_ms=dur, error=str(e))
        return err_msg


# Alias get_predict to get_forecast for model compatibility
get_predict = get_forecast


@tool
def get_citywide_hotspots(threshold: int = 300) -> str:
    """Scan all calibrated sensor points across Delhi and return the top critical pollution hotspots.
    Filters wards with AQI >= threshold (default 300). Use this to identify where urgent intervention is required.
    """
    t0 = time.monotonic()
    try:
        thresh = int(threshold) if threshold else 300
    except (ValueError, TypeError):
        thresh = 300

    try:
        items = fetch_heatmap()
        if not items:
            return "[TOOL ERROR - Telemetry Synchronizing]: Citywide ward readings currently unavailable. Please retry momentarily."

        exceeding = [w for w in items if w.get("aqi", 0) >= thresh]
        ranked_all = sorted(items, key=lambda w: w.get("aqi", 0), reverse=True)

        lines = [
            f"Citywide Hotspot Analysis (Threshold: AQI {thresh}):",
            f"- Total Reporting Wards: {len(items)}",
        ]

        if exceeding:
            lines.append(f"- Wards Exceeding Threshold ({thresh}+): {len(exceeding)}")
            top_list = sorted(exceeding, key=lambda w: w.get("aqi", 0), reverse=True)[:6]
        else:
            lines.append(f"- Zero wards currently exceed {thresh}. Displaying top 5 highest citywide zones:")
            top_list = ranked_all[:5]

        lines.append("\nCritical Hotspots Ranking:")
        for idx, w in enumerate(top_list, 1):
            lines.append(f"  {idx}. {w['ward_name']} ({w['ward_id']}) — AQI: {w['aqi']} [{w['category'].upper()}]")

        worst = ranked_all[0]
        lines.append(f"\nWorst Zone in Delhi: {worst['ward_name']} ({worst['ward_id']}) with AQI {worst['aqi']}.")
        out = "\n".join(lines)
        dur = (time.monotonic() - t0) * 1000.0
        log_tool_execution("get_citywide_hotspots", {"threshold": thresh}, status="SUCCESS", duration_ms=dur, output_summary=out)
        return out
    except Exception as e:
        dur = (time.monotonic() - t0) * 1000.0
        err_msg = f"[TOOL ERROR - Citywide Hotspot Scan Failed]: {str(e)}"
        log_tool_execution("get_citywide_hotspots", {"threshold": thresh}, status="FAILED", duration_ms=dur, error=str(e))
        return err_msg


@tool
def compare_wards(ward_ids: Union[List[str], str]) -> str:
    """Compare atmospheric conditions, pollutant ratios, dominant emission drivers, and 24h trends
    between two or more Delhi wards side-by-side (e.g. ['W01', 'W02'] or 'Rohini, Dwarka').
    """
    t0 = time.monotonic()
    if isinstance(ward_ids, str):
        clean_ids = [w.strip() for w in ward_ids.replace(";", ",").split(",") if w.strip()]
    elif isinstance(ward_ids, list):
        clean_ids = [str(w).strip() for w in ward_ids if str(w).strip()]
    else:
        clean_ids = []

    if len(clean_ids) < 2:
        msg = f"[TOOL ERROR - Insufficient Comparison Targets]: compare_wards requires at least two distinct wards to evaluate comparative metrics. Received: {ward_ids}."
        log_tool_execution("compare_wards", {"ward_ids": ward_ids}, status="FAILED", duration_ms=0, error=msg)
        return msg

    try:
        reports = []
        errors = []
        for wid in clean_ids:
            try:
                aqi = fetch_aqi(wid)
                attr = fetch_source_attribution(wid)
                weather = fetch_weather(wid)
                dominant = attr.get("dominant_source", "traffic").upper()

                reports.append({
                    "ward_id": wid,
                    "name": aqi.get("ward_name", f"Ward {wid}"),
                    "aqi": aqi.get("aqi", 0),
                    "cat": aqi.get("category", "Moderate"),
                    "pm25": aqi.get("pm25", 0),
                    "pm10": aqi.get("pm10", 0),
                    "no2": aqi.get("no2", 0),
                    "wind": f"{weather.get('wind_kph')} km/h {weather.get('wind_dir')}",
                    "dominant": f"{dominant} ({attr.get(dominant.lower(), 0)*100:.0f}%)",
                })
            except Exception as e:
                errors.append(f"Ward {wid}: {e}")

        if not reports:
            msg = f"[TOOL ERROR - Telemetry Retrieval Failed]: Could not retrieve telemetry for comparison targets: {clean_ids}. Details: {'; '.join(errors)}"
            log_tool_execution("compare_wards", {"ward_ids": clean_ids}, status="FAILED", duration_ms=0, error=msg)
            return msg

        lines = ["Comparative Ward Environmental Assessment:\n"]
        for r in reports:
            lines.append(
                f"• {r['name']} ({r['ward_id']}):\n"
                f"   AQI: {r['aqi']} ({r['cat']}) | PM2.5: {r['pm25']} | PM10: {r['pm10']} | NO2: {r['no2']}\n"
                f"   Wind: {r['wind']} | Dominant Source: {r['dominant']}"
            )

        if len(reports) >= 2:
            sorted_by_aqi = sorted(reports, key=lambda r: r["aqi"], reverse=True)
            diff = sorted_by_aqi[0]["aqi"] - sorted_by_aqi[-1]["aqi"]
            lines.append(
                f"\nSummary Delta: {sorted_by_aqi[0]['name']} is {diff} AQI points higher than {sorted_by_aqi[-1]['name']}, "
                f"primarily driven by {sorted_by_aqi[0]['dominant']}."
            )

        if errors:
            lines.append(f"\nNote: telemetry unavailable for: {', '.join(errors)}")

        out = "\n".join(lines)
        dur = (time.monotonic() - t0) * 1000.0
        log_tool_execution("compare_wards", {"ward_ids": clean_ids}, status="SUCCESS", duration_ms=dur, output_summary=out)
        return out
    except Exception as e:
        dur = (time.monotonic() - t0) * 1000.0
        err_msg = f"[TOOL ERROR - Comparison Execution Failed]: {str(e)}"
        log_tool_execution("compare_wards", {"ward_ids": clean_ids}, status="FAILED", duration_ms=dur, error=str(e))
        return err_msg


@tool
def search_regulations(query: str, top_k: int = 5) -> str:
    """Perform semantic vector retrieval over official statutory air quality regulations,
    including CAQM Graded Response Action Plan (GRAP Stages I-IV), CAQM statutory directions
    (Direction Nos. 71, 73, 75, 77), and the Air (Prevention and Control of Pollution) Act, 1981
    (Sections 19, 21, 31A, 37, 38).

    Use this tool whenever an officer asks about:
    - Current restrictions, vehicle bans, construction bans, or industrial fuel rules
    - What is permitted or prohibited under GRAP Stages I, II, III, or IV
    - Legal powers of enforcement, statutory penalties, and criminal liability under the Air Act
    - Mandates for anti-smog guns, dust portals, or diesel generator restrictions
    """
    t0 = time.monotonic()
    clean_query = str(query or "").strip()
    if not clean_query:
        msg = "[TOOL ERROR - Empty Query]: Search query for regulations cannot be empty. Please specify a regulatory topic or GRAP Stage."
        log_tool_execution("search_regulations", {"query": query}, status="FAILED", duration_ms=0, error=msg)
        return msg

    try:
        from app.llm.data_bridge import fetch_regulations
        results = fetch_regulations(query=clean_query, top_k=max(1, min(10, top_k)))
        if not results:
            return f"[RETRIEVAL NOTICE]: No statutory provisions matched query: '{clean_query}'. Try broader terms like 'GRAP Stage 3', 'truck ban', 'diesel generator', or 'Air Act penalties'."

        lines = [f"Retrieved Regulatory Provisions for Query '{clean_query}' ({len(results)} matches):\n"]
        for idx, r in enumerate(results, 1):
            lines.append(
                f"[Citation {idx}] {r['title']}\n"
                f"• Legal Reference: {r.get('legal_citation', 'Statutory Regulation')}\n"
                f"• Category: {r.get('category')} | Clause/Section: {r.get('section', 'General')}\n"
                f"• Vector Relevance Score: {r.get('similarity_score', 0.0)}\n"
                f"• Statutory Mandate:\n"
                f"{r.get('content', '').strip()}\n"
            )

        out = "\n".join(lines)
        dur = (time.monotonic() - t0) * 1000.0
        log_tool_execution("search_regulations", {"query": clean_query, "top_k": top_k}, status="SUCCESS", duration_ms=dur, output_summary=out)
        return out
    except Exception as e:
        dur = (time.monotonic() - t0) * 1000.0
        logger.error(f"Error in search_regulations tool: {e}", exc_info=True)
        err_msg = f"[TOOL ERROR - Regulatory Search Failed]: {str(e)}"
        log_tool_execution("search_regulations", {"query": clean_query}, status="FAILED", duration_ms=dur, error=str(e))
        return err_msg


@tool
def draft_grap_notice(ward_id: str, stage: str = "auto") -> str:
    """Draft an official statutory legal enforcement directive for a ward under Section 19(1)
    and Section 31A of the Air Act, 1981, dynamically retrieving and citing authentic CAQM GRAP
    stage mandates and statutory penalties.
    """
    t0 = time.monotonic()
    clean_id = str(ward_id or "").strip()
    if not clean_id:
        msg = "[TOOL ERROR - Invalid Parameter]: ward_id cannot be empty. Please specify a ward ID (e.g., 'CANT_1', 'W02')."
        log_tool_execution("draft_grap_notice", {"ward_id": ward_id, "stage": stage}, status="FAILED", duration_ms=0, error=msg)
        return msg

    clean_stage = str(stage or "auto").strip()
    # Validate stage parameter
    valid_stages = ("auto", "i", "ii", "iii", "iv", "stage i", "stage ii", "stage iii", "stage iv", "1", "2", "3", "4", "stage 1", "stage 2", "stage 3", "stage 4")
    if clean_stage.lower() not in valid_stages:
        msg = f"[TOOL ERROR - Invalid GRAP Stage]: '{clean_stage}' is not a recognized GRAP Stage. Valid options: 'auto', 'Stage I', 'Stage II', 'Stage III', 'Stage IV'."
        log_tool_execution("draft_grap_notice", {"ward_id": clean_id, "stage": clean_stage}, status="FAILED", duration_ms=0, error=msg)
        return msg

    try:
        from app.llm.data_bridge import fetch_regulations
        aqi_info = fetch_aqi(clean_id)
        source_info = fetch_source_attribution(clean_id)
        aqi_val = aqi_info.get("aqi", 250)
        ward_name = aqi_info.get("ward_name", f"Ward {clean_id}")
        dominant = source_info.get("dominant_source", "traffic").upper()

        # Determine GRAP stage
        if clean_stage.lower() == "auto":
            if aqi_val <= 200:
                grap_stage = "Stage I (Precautionary)"
                stage_roman = "I"
                category = "GRAP_STAGE_1"
            elif aqi_val <= 300:
                grap_stage = "Stage I ('Poor' AQI 201-300)"
                stage_roman = "I"
                category = "GRAP_STAGE_1"
            elif aqi_val <= 400:
                grap_stage = "Stage II ('Very Poor' AQI 301-400)"
                stage_roman = "II"
                category = "GRAP_STAGE_2"
            elif aqi_val <= 450:
                grap_stage = "Stage III ('Severe' AQI 401-450)"
                stage_roman = "III"
                category = "GRAP_STAGE_3"
            else:
                grap_stage = "Stage IV ('Severe+' AQI >450)"
                stage_roman = "IV"
                category = "GRAP_STAGE_4"
        else:
            stage_roman = clean_stage.upper().replace("STAGE", "").strip()
            num_to_roman = {"1": "I", "2": "II", "3": "III", "4": "IV"}
            stage_roman = num_to_roman.get(stage_roman, stage_roman)
            grap_stage = f"Stage {stage_roman}"
            cat_map = {"I": "GRAP_STAGE_1", "II": "GRAP_STAGE_2", "III": "GRAP_STAGE_3", "IV": "GRAP_STAGE_4"}
            category = cat_map.get(stage_roman, "GRAP_STAGE_2")

        # 1. Retrieve authentic GRAP regulatory clauses via semantic search
        grap_chunks = fetch_regulations(
            query=f"GRAP Stage {stage_roman} {dominant} mandates restrictions and dust vehicular enforcement",
            top_k=2,
            category=category,
        )
        if not grap_chunks:
            grap_chunks = fetch_regulations(query=f"GRAP Stage {stage_roman} actions", top_k=2)

        # 2. Retrieve statutory enforcement powers (Section 31A & 37)
        legal_chunks = fetch_regulations(
            query="Section 31A directions closure electricity power stoppage Section 37 imprisonment penalty",
            top_k=1,
            category="AIR_ACT_1981",
        )

        mandate_lines = []
        citations_used = []
        for c in grap_chunks:
            citations_used.append(c.get("legal_citation", "CAQM Direction No. 75"))
            mandate_lines.append(f"[{c.get('section', 'Mandate')}] {c.get('title')}:")
            for line in c.get("content", "").split("\n"):
                line = line.strip()
                if line and not line.startswith("GRAP Stage"):
                    mandate_lines.append(f"  • {line}")

        penal_lines = []
        for lc in legal_chunks:
            citations_used.append(lc.get("legal_citation", "Section 31A / 37, The Air Act, 1981"))
            for line in lc.get("content", "").split("\n"):
                line = line.strip()
                if line and not line.startswith("The Air"):
                    penal_lines.append(f"  • {line}")

        mandates_text = "\n".join(mandate_lines) if mandate_lines else "  • Enforce intensified sweeping, water misting, and hotspot surveillance."
        penal_text = "\n".join(penal_lines) if penal_lines else "  • Non-compliance attracts prosecution and penalties under Section 37 of the Air Act, 1981."

        notice = f"""================================================================================
GOVERNMENT OF NCT OF DELHI
DELHI POLLUTION CONTROL COMMITTEE (DPCC) / CAQM ENFORCEMENT CELL
STATUTORY DIRECTIVE UNDER SECTION 19(1) & SECTION 31A OF THE AIR ACT, 1981
================================================================================
Ref No: DPCC/ENF/GRAP-{stage_roman}/2026/W-{clean_id}
Target Jurisdiction: {ward_name} (Ward ID: {clean_id})
Date/Time Issued: Live Telemetry Cycle
Operational Air Quality: {aqi_val} AQI ({aqi_info.get('category', 'Poor')})
Dominant Emission Vector: {dominant} ({source_info.get(dominant.lower(), 0)*100:.1f}% contribution)

1. STATUTORY RETRIEVAL & LEGAL BASES:
{chr(10).join(f"   - {cit}" for cit in set(citations_used))}

2. OPERATIVE STATUTORY MANDATES ({grap_stage.upper()}):
{mandates_text}

3. PENAL PROVISIONS & LEGAL ENFORCEMENT (AIR ACT, 1981):
{penal_text}

4. FIELD INSPECTION & TASKING:
   - DPCC Flying Squad #4 and Municipal Ward Engineers are deployed for immediate on-site compliance audits.
   - Authorizes immediate sealing, electrical disconnection, and compounding prosecution against any violating entity.
   - Compliance certification must be submitted to the Urban Command Center within 12 hours.

BY ORDER OF THE COMMISSION FOR AIR QUALITY MANAGEMENT (NCR)
================================================================================"""
        dur = (time.monotonic() - t0) * 1000.0
        log_tool_execution("draft_grap_notice", {"ward_id": clean_id, "stage": stage_roman}, status="SUCCESS", duration_ms=dur, output_summary=f"Drafted GRAP {stage_roman} notice for {clean_id}")
        return notice
    except Exception as e:
        dur = (time.monotonic() - t0) * 1000.0
        err_msg = f"[TOOL ERROR - Notice Drafting Failed]: Could not draft statutory directive for ward '{clean_id}': {str(e)}"
        log_tool_execution("draft_grap_notice", {"ward_id": clean_id, "stage": clean_stage}, status="FAILED", duration_ms=dur, error=str(e))
        return err_msg


@tool
def get_historical_trend(ward_id: str, days: int = 7) -> str:
    """Get multi-day historical AQI telemetry for a ward to evaluate whether air quality is improving,
    worsening, or plateauing. Computes average AQI, peak spikes, and daily progression.
    """
    t0 = time.monotonic()
    clean_id = str(ward_id or "").strip()
    if not clean_id:
        msg = "[TOOL ERROR - Invalid Parameter]: ward_id cannot be empty."
        log_tool_execution("get_historical_trend", {"ward_id": ward_id, "days": days}, status="FAILED", duration_ms=0, error=msg)
        return msg

    try:
        num_days = int(days)
        if num_days <= 0 or num_days > 30:
            msg = f"[TOOL ERROR - Invalid Days Parameter]: days must be an integer between 1 and 30. Received: {days}."
            log_tool_execution("get_historical_trend", {"ward_id": clean_id, "days": days}, status="FAILED", duration_ms=0, error=msg)
            return msg
    except (ValueError, TypeError):
        msg = f"[TOOL ERROR - Invalid Days Parameter]: days must be an integer. Received: {days}."
        log_tool_execution("get_historical_trend", {"ward_id": clean_id, "days": days}, status="FAILED", duration_ms=0, error=msg)
        return msg

    try:
        history = fetch_aqi_history(clean_id, days=num_days)
        if not history:
            return f"[TOOL ERROR - Telemetry Missing]: Historical records unavailable for ward {clean_id} over {num_days} days."

        aqis = [r["aqi"] for r in history if r.get("aqi") is not None]
        if not aqis:
            return f"[TOOL ERROR - No Valid Readings]: No valid numerical AQI readings found in {num_days}-day history for ward {clean_id}."

        avg_aqi = round(sum(aqis) / len(aqis))
        max_aqi = max(aqis)
        min_aqi = min(aqis)
        first_aqi = aqis[0]
        last_aqi = aqis[-1]
        delta = last_aqi - first_aqi

        trend_status = "Worsening (Upward Trend)" if delta > 15 else ("Improving (Downward Trend)" if delta < -15 else "Stable / Stagnant")

        lines = [
            f"Historical AQI Telemetry for Ward {clean_id} (Past {num_days} Days):",
            f"- Observations Sampled: {len(history)} records",
            f"- Mean {num_days}-Day AQI: {avg_aqi}",
            f"- Range: Min {min_aqi} ↔ Max {max_aqi}",
            f"- Net Change: {delta:+d} AQI points ({trend_status})",
            "\nDaily Progression Highlights:",
        ]

        step = max(1, len(history) // num_days)
        for i, r in enumerate(history[::step][:num_days], 1):
            ts = r.get("timestamp", "").split("T")[0]
            lines.append(f"  Day {i} ({ts}): AQI {r['aqi']}")

        out = "\n".join(lines)
        dur = (time.monotonic() - t0) * 1000.0
        log_tool_execution("get_historical_trend", {"ward_id": clean_id, "days": num_days}, status="SUCCESS", duration_ms=dur, output_summary=out)
        return out
    except Exception as e:
        dur = (time.monotonic() - t0) * 1000.0
        err_msg = f"[TOOL ERROR - Historical Telemetry Failed]: {str(e)}"
        log_tool_execution("get_historical_trend", {"ward_id": clean_id, "days": num_days}, status="FAILED", duration_ms=dur, error=str(e))
        return err_msg


@tool
def get_weather(ward_id: str) -> str:
    """Get current weather conditions (temperature, humidity, wind speed, wind direction, rain) for a specific Delhi ward."""
    t0 = time.monotonic()
    clean_id = str(ward_id or "").strip()
    if not clean_id:
        msg = "[TOOL ERROR - Invalid Parameter]: ward_id cannot be empty."
        log_tool_execution("get_weather", {"ward_id": ward_id}, status="FAILED", duration_ms=0, error=msg)
        return msg

    try:
        res = fetch_weather(clean_id)
        out = (
            f"Weather Telemetry for Ward {clean_id}:\n"
            f"- Temperature: {res.get('temp_c')} °C\n"
            f"- Wind Velocity: {res.get('wind_kph')} km/h from {res.get('wind_dir')} ({res.get('wind_deg')}°)\n"
            f"- Relative Humidity: {res.get('humidity')}%\n"
            f"- Precipitation: {res.get('rain_mm')} mm"
        )
        dur = (time.monotonic() - t0) * 1000.0
        log_tool_execution("get_weather", {"ward_id": clean_id}, status="SUCCESS", duration_ms=dur, output_summary=out)
        return out
    except Exception as e:
        dur = (time.monotonic() - t0) * 1000.0
        err_msg = f"[TOOL ERROR - Weather Fetch Failed]: {str(e)}"
        log_tool_execution("get_weather", {"ward_id": clean_id}, status="FAILED", duration_ms=dur, error=str(e))
        return err_msg


@tool
def get_recommendations(ward_id: str) -> str:
    """Get ranked government mitigation actions and site inspection priority list for a specific Delhi ward."""
    t0 = time.monotonic()
    clean_id = str(ward_id or "").strip()
    if not clean_id:
        msg = "[TOOL ERROR - Invalid Parameter]: ward_id cannot be empty."
        log_tool_execution("get_recommendations", {"ward_id": ward_id}, status="FAILED", duration_ms=0, error=msg)
        return msg

    try:
        res = recommend_actions(clean_id)
        actions = []
        for idx, act in enumerate(res.get("actions", []), 1):
            actions.append(f"{idx}. [{act['urgency'].upper()}] {act['action']} on {act['target']} — Reason: {act['reason']}")

        inspections = []
        for ins in res.get("inspection_priority", []):
            inspections.append(f"• Priority {ins['priority']}: {ins['site']} ({ins['ward_id']}) — {ins['reason']}")

        out = (
            f"Targeted Government Directives for Ward {clean_id}:\n"
            + "\n".join(actions)
            + "\n\nField Inspection Priority Queue:\n"
            + "\n".join(inspections)
        )
        dur = (time.monotonic() - t0) * 1000.0
        log_tool_execution("get_recommendations", {"ward_id": clean_id}, status="SUCCESS", duration_ms=dur, output_summary=out)
        return out
    except Exception as e:
        dur = (time.monotonic() - t0) * 1000.0
        err_msg = f"[TOOL ERROR - Recommendation Generation Failed]: {str(e)}"
        log_tool_execution("get_recommendations", {"ward_id": clean_id}, status="FAILED", duration_ms=dur, error=str(e))
        return err_msg


@tool
def simulate_intervention(
    ward_id: str = "current",
    intervention_type: str = "construction_ban",
    intensity: str = "1.0",
    horizon_hours: int = 24
) -> str:
    """Simulate the atmospheric and predictive impact of policy interventions on AQI.
    
    Couples live Source Attribution with the LightGBM predictive model to calculate:
    - Pre-intervention vs Post-intervention AQI
    - Immediate and 24h/48h average reduction in AQI points and percentage
    - Peak anticipated AQI suppression
    - Sector emissions mitigated and model assumptions

    Parameters:
    - ward_id: Specific ward ID (e.g. 'CANT_1', 'W02'), comma-separated list ('CANT_1, W02'),
      or 'citywide' / 'all' to evaluate top critical zones.
    - intervention_type: Policy intervention to simulate:
      * 'construction_ban' (halts C&D excavation, masonry, concrete batching)
      * 'diesel_truck_ban' (restricts medium/heavy commercial diesel freight)
      * 'odd_even' (private vehicle road space rationing)
      * 'industrial_shutdown' (shuts down industrial boilers/kilns in proximity)
      * 'dg_set_ban' (diesel generator prohibition across commercial/residential)
      * 'increased_mechanized_sweeping' (high-frequency vacuum sweeping + misting)
      * 'anti_smog_gun_deployment' (localized particulate suppression)
      * 'complete_grap_stage_3' (composite Stage III: C&D ban + BS-III/IV LMV ban)
      * 'complete_grap_stage_4' (emergency Stage IV: truck halt + all construction ban + 50% WFH)
      Or compare two interventions using 'vs' (e.g., 'odd_even vs construction_ban').
    - intensity: Enforcement intensity ('1.0' for strict 100%, '0.7' for moderate, '0.4' for partial).
    - horizon_hours: Time window for recursive forecasting (24 or 48 hours).
    """
    t0 = time.monotonic()
    try:
        from app.ml.intervention_simulator import (
            INTERVENTION_EFFECTIVENESS,
            normalize_intervention,
            parse_intensity,
            simulate_ward_intervention,
            simulate_multi_ward_intervention,
            simulate_citywide_intervention,
        )

        num_intensity = parse_intensity(intensity)
        horizon = 48 if horizon_hours and horizon_hours >= 48 else 24
        target_str = str(ward_id or "CANT_1").strip()
        int_str = str(intervention_type or "").strip()

        if not int_str:
            supported = ", ".join(sorted(INTERVENTION_EFFECTIVENESS.keys()))
            msg = f"[TOOL ERROR - Missing Intervention]: Please specify a policy intervention to simulate. Supported policies: {supported}."
            log_tool_execution("simulate_intervention", {"ward_id": target_str, "intervention": int_str}, status="FAILED", duration_ms=0, error=msg)
            return msg

        # Check for intervention comparison (e.g. "odd_even vs construction_ban")
        if " vs " in int_str.lower() or " versus " in int_str.lower():
            delim = " vs " if " vs " in int_str.lower() else " versus "
            int_a, int_b = [x.strip() for x in int_str.lower().split(delim, 1)]
            
            canon_a = normalize_intervention(int_a)
            canon_b = normalize_intervention(int_b)
            if not canon_a or not canon_b:
                unrec = int_a if not canon_a else int_b
                supported = ", ".join(sorted(INTERVENTION_EFFECTIVENESS.keys()))
                msg = f"[TOOL ERROR - Unsupported Policy Intervention]: '{unrec}' is not a recognized atmospheric policy. Supported policies: {supported}."
                log_tool_execution("simulate_intervention", {"ward_id": target_str, "intervention": int_str}, status="FAILED", duration_ms=0, error=msg)
                return msg

            sim_a = simulate_ward_intervention(target_str if target_str not in ("citywide", "all") else "CANT_1", int_a, num_intensity, horizon)
            sim_b = simulate_ward_intervention(target_str if target_str not in ("citywide", "all") else "CANT_1", int_b, num_intensity, horizon)

            out = (
                f"Comparative Intervention Simulation for {sim_a['ward_name']} ({horizon}h horizon):\n\n"
                f"• Option A: {sim_a['intervention_label']} (Intensity: {num_intensity*100:.0f}%)\n"
                f"   Baseline AQI: {sim_a['current_aqi']} → Simulated AQI: {sim_a['simulated_immediate_aqi']}\n"
                f"   Average 24h Drop: -{sim_a['average_reduction_points']} points (-{sim_a['percentage_reduction']}%)\n"
                f"   Peak AQI Reduction: {sim_a['peak_baseline']} → {sim_a['peak_simulated']} (-{sim_a['peak_baseline'] - sim_a['peak_simulated']} pts)\n"
                f"   Primary Sector Affected: {sim_a['top_affected_source']}\n\n"
                f"• Option B: {sim_b['intervention_label']} (Intensity: {num_intensity*100:.0f}%)\n"
                f"   Baseline AQI: {sim_b['current_aqi']} → Simulated AQI: {sim_b['simulated_immediate_aqi']}\n"
                f"   Average 24h Drop: -{sim_b['average_reduction_points']} points (-{sim_b['percentage_reduction']}%)\n"
                f"   Peak AQI Reduction: {sim_b['peak_baseline']} → {sim_b['peak_simulated']} (-{sim_b['peak_baseline'] - sim_b['peak_simulated']} pts)\n"
                f"   Primary Sector Affected: {sim_b['top_affected_source']}\n\n"
                f"Verdict: {sim_a['intervention_label'] if sim_a['average_reduction_points'] >= sim_b['average_reduction_points'] else sim_b['intervention_label']} "
                f"yields a {abs(sim_a['average_reduction_points'] - sim_b['average_reduction_points']):.1f} points greater atmospheric reduction "
                f"because the target zone's dominant source is {sim_a['dominant_source']}."
            )
            dur = (time.monotonic() - t0) * 1000.0
            log_tool_execution("simulate_intervention", {"ward_id": target_str, "intervention": int_str}, status="SUCCESS", duration_ms=dur, output_summary=out)
            return out

        # Validate non-comparison intervention
        canon = normalize_intervention(int_str)
        if not canon:
            supported = ", ".join(sorted(INTERVENTION_EFFECTIVENESS.keys()))
            msg = f"[TOOL ERROR - Unsupported Policy Intervention]: '{int_str}' is not a recognized atmospheric policy. Supported policies: {supported}."
            log_tool_execution("simulate_intervention", {"ward_id": target_str, "intervention": int_str}, status="FAILED", duration_ms=0, error=msg)
            return msg

        # Citywide evaluation
        if target_str.lower() in ("citywide", "all", "delhi", "entire city"):
            res = simulate_citywide_intervention(int_str, num_intensity, horizon)
            lines = [
                f"Citywide Intervention Simulation: {res['intervention_label']} (Intensity: {num_intensity*100:.0f}%)\n"
                f"• Wards Analyzed: Top {res['total_wards_evaluated']} Critical Hotspots\n"
                f"• Mean Citywide AQI Reduction: -{res['mean_percentage_reduction']}%\n"
                f"• Highest Responding Ward: {res['best_performing_ward']} (-{res['highest_ward_drop']} pts)\n\n"
                f"Ward-by-Ward Simulated Impact Ranking:"
            ]
            for w in res.get("ward_results", []):
                lines.append(
                    f"  • {w['ward_name']} ({w['ward_id']}): AQI {w['current_aqi']} → {w['simulated_immediate_aqi']} "
                    f"(-{w['average_reduction_points']} pts / -{w['percentage_reduction']}%) | Driver: {w['dominant_source']}"
                )
            out = "\n".join(lines)
            dur = (time.monotonic() - t0) * 1000.0
            log_tool_execution("simulate_intervention", {"ward_id": target_str, "intervention": int_str}, status="SUCCESS", duration_ms=dur, output_summary=out)
            return out

        # Multi-ward evaluation (comma-separated or list)
        if "," in target_str:
            targets = [t.strip() for t in target_str.split(",") if t.strip()]
            res = simulate_multi_ward_intervention(targets, int_str, num_intensity, horizon)
            lines = [
                f"Multi-Ward Intervention Simulation: {res['intervention_label']} (Intensity: {num_intensity*100:.0f}%)\n"
                f"• Total Wards: {res['total_wards_evaluated']} | Mean Reduction: -{res['mean_percentage_reduction']}%\n"
                f"• Most Responsive Ward: {res['best_performing_ward']} (-{res['highest_ward_drop']} pts)\n"
            ]
            for w in res.get("ward_results", []):
                lines.append(
                    f"  • {w['ward_name']}: AQI {w['current_aqi']} → {w['simulated_immediate_aqi']} "
                    f"(-{w['average_reduction_points']} pts / -{w['percentage_reduction']}%)"
                )
            out = "\n".join(lines)
            dur = (time.monotonic() - t0) * 1000.0
            log_tool_execution("simulate_intervention", {"ward_id": target_str, "intervention": int_str}, status="SUCCESS", duration_ms=dur, output_summary=out)
            return out

        # Single ward evaluation
        res = simulate_ward_intervention(target_str, int_str, num_intensity, horizon)
        out = (
            f"What-If Intervention Simulation for {res['ward_name']} (Ward: {res['ward_id']}):\n"
            f"• Proposed Policy: {res['intervention_label']} (Enforcement Intensity: {num_intensity*100:.0f}%)\n"
            f"• Atmospheric Horizon: {horizon} Hours\n\n"
            f"Predictive AQI Trajectory:\n"
            f"  - Current Baseline AQI:      {res['current_aqi']} ({res['dominant_source']} dominant)\n"
            f"  - Simulated Immediate AQI:   {res['simulated_immediate_aqi']} (-{res['immediate_drop_points']} points)\n"
            f"  - Average Projected AQI:     {res['average_baseline_aqi']} → {res['average_simulated_aqi']} (-{res['percentage_reduction']}%)\n"
            f"  - Peak AQI Suppression:      {res['peak_baseline']} → {res['peak_simulated']} (-{res['peak_baseline'] - res['peak_simulated']} points)\n\n"
            f"Emission Vector Dynamics:\n"
            f"  - Baseline Sector Shares:    Traffic: {res['source_breakdown_before']['traffic']}%, Construction: {res['source_breakdown_before']['construction']}%, Industry: {res['source_breakdown_before']['industry']}%, Dust: {res['source_breakdown_before']['dust']}%\n"
            f"  - Primary Sector Mitigated:  {res['top_affected_source']}\n\n"
            f"Scientific Synthesis:\n"
            f"{res['explanation']}\n\n"
            f"Model Assumptions:\n"
            + "\n".join(f"  • {a}" for a in res['assumptions'])
        )
        dur = (time.monotonic() - t0) * 1000.0
        log_tool_execution("simulate_intervention", {"ward_id": target_str, "intervention": int_str}, status="SUCCESS", duration_ms=dur, output_summary=out)
        return out
    except Exception as e:
        dur = (time.monotonic() - t0) * 1000.0
        logger.error(f"Error in simulate_intervention tool: {e}", exc_info=True)
        err_msg = f"[TOOL ERROR - Policy Simulation Failed]: {str(e)}"
        log_tool_execution("simulate_intervention", {"ward_id": ward_id, "intervention": intervention_type}, status="FAILED", duration_ms=dur, error=str(e))
        return err_msg


def build_tools():
    """Return the complete list of tools for the LangGraph officer chat agent."""
    return [
        get_citywide_hotspots,
        get_source_attribution,
        simulate_intervention,
        search_regulations,
        get_forecast,
        compare_wards,
        draft_grap_notice,
        get_historical_trend,
        get_aqi,
        get_weather,
        get_recommendations,
    ]
