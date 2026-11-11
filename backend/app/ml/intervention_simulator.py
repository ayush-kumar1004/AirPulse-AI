"""
AirPulse AI - What-If Policy Intervention Simulator
Couples real-time Source Attribution with the LightGBM Tabular Forecasting Engine.

Simulates the atmospheric impact of regulatory interventions on ward and citywide AQI:
- construction_ban
- diesel_truck_ban
- odd_even
- industrial_shutdown
- dg_set_ban
- increased_mechanized_sweeping
- anti_smog_gun_deployment
- biomass_burning_ban
- complete_grap_stage_3
- complete_grap_stage_4
"""

import math
import logging
import time
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
import numpy as np

from app.llm.data_bridge import (
    fetch_aqi,
    fetch_forecast,
    fetch_forecast_full,
    fetch_heatmap,
    fetch_source_attribution,
    fetch_weather,
)
from app.observability import log_simulation_run

logger = logging.getLogger(__name__)

# Sector reduction effectiveness matrix (fractions between 0.0 and 1.0)
# Defines what fraction of a given source's emissions are mitigated under 100% compliance
INTERVENTION_EFFECTIVENESS: Dict[str, Dict[str, float]] = {
    "construction_ban": {
        "construction": 0.78,
        "dust": 0.32,
        "traffic": 0.06,   # slight drop from construction truck traffic
        "industry": 0.00,
    },
    "diesel_truck_ban": {
        "traffic": 0.46,
        "dust": 0.12,      # less heavy wheel entrainment
        "construction": 0.05,
        "industry": 0.02,
    },
    "odd_even": {
        "traffic": 0.28,
        "dust": 0.08,
        "construction": 0.00,
        "industry": 0.00,
    },
    "industrial_shutdown": {
        "industry": 0.82,
        "traffic": 0.04,   # less freight in industrial pockets
        "construction": 0.00,
        "dust": 0.05,
    },
    "dg_set_ban": {
        "industry": 0.22,
        "traffic": 0.00,
        "construction": 0.08,
        "dust": 0.00,
    },
    "increased_mechanized_sweeping": {
        "dust": 0.58,
        "construction": 0.15,
        "traffic": 0.00,
        "industry": 0.00,
    },
    "anti_smog_gun_deployment": {
        "dust": 0.38,
        "construction": 0.32,
        "traffic": 0.00,
        "industry": 0.00,
    },
    "biomass_burning_ban": {
        "dust": 0.24,
        "industry": 0.12,
        "traffic": 0.00,
        "construction": 0.00,
    },
    "complete_grap_stage_3": {
        "construction": 0.82,
        "traffic": 0.34,
        "dust": 0.44,
        "industry": 0.18,
    },
    "complete_grap_stage_4": {
        "construction": 0.92,
        "traffic": 0.62,
        "dust": 0.58,
        "industry": 0.48,
    },
}

# Alias map for natural language queries
INTERVENTION_ALIASES: Dict[str, str] = {
    "construction": "construction_ban",
    "c&d ban": "construction_ban",
    "halt construction": "construction_ban",
    "stop construction": "construction_ban",
    "truck ban": "diesel_truck_ban",
    "diesel trucks": "diesel_truck_ban",
    "heavy vehicle ban": "diesel_truck_ban",
    "diesel ban": "diesel_truck_ban",
    "odd even": "odd_even",
    "vehicle rationing": "odd_even",
    "private vehicle ban": "odd_even",
    "industrial closure": "industrial_shutdown",
    "factory shutdown": "industrial_shutdown",
    "industry shutdown": "industrial_shutdown",
    "dg sets": "dg_set_ban",
    "diesel generators": "dg_set_ban",
    "dg set ban": "dg_set_ban",
    "sweeping": "increased_mechanized_sweeping",
    "mechanized sweeping": "increased_mechanized_sweeping",
    "water sprinkling": "increased_mechanized_sweeping",
    "anti smog guns": "anti_smog_gun_deployment",
    "anti-smog": "anti_smog_gun_deployment",
    "open burning": "biomass_burning_ban",
    "waste burning": "biomass_burning_ban",
    "grap 3": "complete_grap_stage_3",
    "grap stage 3": "complete_grap_stage_3",
    "grap stage iii": "complete_grap_stage_3",
    "grap 4": "complete_grap_stage_4",
    "grap stage 4": "complete_grap_stage_4",
    "grap stage iv": "complete_grap_stage_4",
}


def normalize_intervention(raw_name: str) -> Optional[str]:
    """Normalize input intervention string to canonical key, returning None if unrecognized."""
    if not raw_name or not str(raw_name).strip():
        return None
    cleaned = raw_name.lower().strip().replace("-", " ").replace("_", " ")
    for alias, canonical in INTERVENTION_ALIASES.items():
        if alias in cleaned:
            return canonical
    for key in INTERVENTION_EFFECTIVENESS.keys():
        if key.replace("_", " ") in cleaned or key in cleaned:
            return key
    return None


def parse_intensity(intensity: Optional[Union[float, str]]) -> float:
    """Convert intensity argument to float fraction (0.2 to 1.0)."""
    if intensity is None:
        return 1.0
    if isinstance(intensity, (int, float)):
        return max(0.1, min(1.0, float(intensity)))
    s = str(intensity).lower().strip()
    if "strict" in s or "full" in s or "complete" in s or "high" in s:
        return 1.0
    if "moderate" in s or "medium" in s or "partial" in s:
        return 0.7
    if "mild" in s or "low" in s:
        return 0.4
    try:
        val = float(s.replace("%", ""))
        if val > 1.0:
            val = val / 100.0
        return max(0.1, min(1.0, val))
    except ValueError:
        return 0.85


def simulate_ward_intervention(
    ward_id: str,
    intervention_type: str,
    intensity: float = 1.0,
    horizon_hours: int = 24
) -> Dict[str, Any]:
    """Execute atmospheric simulation for a single ward coupling source attribution
    with LightGBM forecasting.
    """
    t0 = time.monotonic()
    canonical_type = normalize_intervention(intervention_type)
    if not canonical_type:
        supported = ", ".join(sorted(INTERVENTION_EFFECTIVENESS.keys()))
        raise ValueError(
            f"Unsupported policy intervention '{intervention_type}'. Supported policies: {supported}."
        )

    effectiveness = INTERVENTION_EFFECTIVENESS[canonical_type]

    # 1. Fetch live telemetry, source attribution, and weather
    aqi_data = fetch_aqi(ward_id)
    source_data = fetch_source_attribution(ward_id)
    weather_data = fetch_weather(ward_id)

    curr_aqi = aqi_data.get("aqi", 200)
    ward_name = aqi_data.get("ward_name", f"Ward {ward_id}")

    # Extract sector shares
    traffic_share = source_data.get("traffic", 0.35)
    construction_share = source_data.get("construction", 0.25)
    industry_share = source_data.get("industry", 0.25)
    dust_share = source_data.get("dust", 0.15)
    dominant_source = source_data.get("dominant_source", "traffic").lower()

    # 2. Compute dynamic sector-weighted emission reduction
    delta_traffic = traffic_share * effectiveness.get("traffic", 0.0) * intensity
    delta_construction = construction_share * effectiveness.get("construction", 0.0) * intensity
    delta_industry = industry_share * effectiveness.get("industry", 0.0) * intensity
    delta_dust = dust_share * effectiveness.get("dust", 0.0) * intensity

    total_emission_reduction_fraction = (
        delta_traffic + delta_construction + delta_industry + delta_dust
    )

    # Local airshed responsiveness factor:
    # Under low wind (<7 kph) and stagnant inversion, local source control has high local impact (75-80%).
    # Under high wind, transboundary dilution dominates.
    wind_kph = weather_data.get("wind_kph", 10.0)
    if wind_kph < 6.0:
        local_responsiveness = 0.82
    elif wind_kph < 14.0:
        local_responsiveness = 0.74
    else:
        local_responsiveness = 0.65

    net_ambient_drop_fraction = total_emission_reduction_fraction * local_responsiveness
    net_aqi_drop_points = round(curr_aqi * net_ambient_drop_fraction, 1)
    simulated_curr_aqi = max(35, round(curr_aqi - net_aqi_drop_points))

    # 3. Dynamic Projection with LightGBM Forecast Trajectory
    try:
        raw_forecast = fetch_forecast_full(ward_id, horizon_hours=horizon_hours)
        baseline_points = raw_forecast.get("points", []) or raw_forecast.get("forecast", [])
    except Exception as e:
        logger.warning(f"Forecast fetch in simulator for {ward_id}: {e}")
        baseline_points = []

    # If full points unavailable, fetch forecast points directly
    if not baseline_points:
        try:
            baseline_points = fetch_forecast(ward_id, horizon_hours=horizon_hours)
        except Exception:
            baseline_points = []

    # If telemetry is completely offline, maintain flat current baseline (zero synthetic sine waves)
    if not baseline_points:
        now_dt = datetime.now(timezone.utc)
        baseline_points = [
            {"hour": i, "timestamp": now_dt.isoformat(), "predicted_aqi": curr_aqi}
            for i in range(1, horizon_hours + 1)
        ]

    simulated_trajectory = []
    base_aqi_sum = 0
    sim_aqi_sum = 0
    peak_base = 0
    peak_sim = 0

    for i, pt in enumerate(baseline_points[:horizon_hours], 1):
        b_val = pt.get("predicted_aqi") or pt.get("aqi", curr_aqi)
        base_aqi_sum += b_val
        if b_val > peak_base:
            peak_base = b_val

        # Atmospheric evacuation ramp over time: beta(t) = 1 - exp(-t/7.0)
        time_ramp = 1.0 - math.exp(-i / 7.0)
        reduction_t = net_aqi_drop_points * (0.65 + 0.35 * time_ramp)
        s_val = max(35, round(b_val - reduction_t))

        sim_aqi_sum += s_val
        if s_val > peak_sim:
            peak_sim = s_val

        simulated_trajectory.append({
            "hour": i,
            "timestamp": pt.get("timestamp"),
            "baseline_aqi": b_val,
            "simulated_aqi": s_val,
            "reduction_points": round(b_val - s_val, 1),
        })

    avg_baseline = round(base_aqi_sum / max(1, len(simulated_trajectory)), 1)
    avg_simulated = round(sim_aqi_sum / max(1, len(simulated_trajectory)), 1)
    avg_reduction_points = round(avg_baseline - avg_simulated, 1)
    pct_reduction = round((avg_reduction_points / max(1.0, avg_baseline)) * 100.0, 1)

    # 4. Impacted sources ranked
    impacts = [
        {"source": "Construction", "fraction_mitigated": delta_construction, "original_share": construction_share},
        {"source": "Traffic", "fraction_mitigated": delta_traffic, "original_share": traffic_share},
        {"source": "Industry", "fraction_mitigated": delta_industry, "original_share": industry_share},
        {"source": "Dust", "fraction_mitigated": delta_dust, "original_share": dust_share},
    ]
    impacts.sort(key=lambda x: x["fraction_mitigated"], reverse=True)
    top_affected_source = impacts[0]["source"]

    # 5. Scientific Explanation Narrative
    clean_label = canonical_type.replace("_", " ").title()
    explanation = (
        f"Imposing a {clean_label} (enforcement intensity: {intensity*100:.0f}%) in {ward_name} "
        f"reduces baseline AQI from {curr_aqi} to ~{simulated_curr_aqi} (net immediate drop of {net_aqi_drop_points} AQI points, "
        f"and an average {pct_reduction}% reduction over {horizon_hours} hours). "
        f"This policy primarily mitigates {top_affected_source} emissions (which currently account for {impacts[0]['original_share']*100:.1f}% "
        f"of the ward's pollution). "
        f"Peak anticipated AQI drops from {peak_base} to {peak_sim} points. "
        f"Local dispersion benefit is sustained due to ambient wind velocity of {wind_kph} km/h."
    )

    duration_ms = (time.monotonic() - t0) * 1000.0
    log_simulation_run(
        ward_id=ward_id,
        intervention_type=canonical_type,
        intensity=intensity,
        horizon_hours=horizon_hours,
        baseline_aqi=curr_aqi,
        simulated_aqi=simulated_curr_aqi,
        reduction_points=avg_reduction_points,
        percentage_reduction=pct_reduction,
        top_affected_source=top_affected_source,
        duration_ms=duration_ms,
        status="SUCCESS",
    )

    return {
        "ward_id": ward_id,
        "ward_name": ward_name,
        "intervention_type": canonical_type,
        "intervention_label": clean_label,
        "intensity": intensity,
        "horizon_hours": horizon_hours,
        "current_aqi": curr_aqi,
        "simulated_immediate_aqi": simulated_curr_aqi,
        "immediate_drop_points": net_aqi_drop_points,
        "average_baseline_aqi": avg_baseline,
        "average_simulated_aqi": avg_simulated,
        "average_reduction_points": avg_reduction_points,
        "percentage_reduction": pct_reduction,
        "peak_baseline": peak_base,
        "peak_simulated": peak_sim,
        "dominant_source": dominant_source.title(),
        "top_affected_source": top_affected_source,
        "source_breakdown_before": {
            "traffic": round(traffic_share * 100, 1),
            "construction": round(construction_share * 100, 1),
            "industry": round(industry_share * 100, 1),
            "dust": round(dust_share * 100, 1),
        },
        "assumptions": [
            f"Enforcement compliance rate calibrated at {intensity*100:.0f}%.",
            f"Local ward airshed sensitivity factor estimated at {local_responsiveness*100:.0f}% (accounting for ~{100-local_responsiveness*100:.0f}% regional transboundary background).",
            f"Atmospheric turnover modeled dynamically against LightGBM 24h predictive trajectory.",
        ],
        "explanation": explanation,
        "trajectory": simulated_trajectory[:6],  # sample preview
    }


def simulate_multi_ward_intervention(
    ward_ids: List[str],
    intervention_type: str,
    intensity: float = 1.0,
    horizon_hours: int = 24
) -> Dict[str, Any]:
    """Execute comparative multi-ward intervention simulation."""
    results = []
    for wid in ward_ids:
        try:
            res = simulate_ward_intervention(
                ward_id=wid,
                intervention_type=intervention_type,
                intensity=intensity,
                horizon_hours=horizon_hours,
            )
            results.append(res)
        except Exception as e:
            logger.warning(f"Error simulating ward {wid}: {e}")

    if not results:
        raise RuntimeError(f"No telemetry available to simulate wards: {ward_ids}")

    # Sort by reduction impact
    results.sort(key=lambda x: x["average_reduction_points"], reverse=True)
    avg_pct = round(sum(r["percentage_reduction"] for r in results) / len(results), 1)
    total_drop = round(sum(r["average_reduction_points"] for r in results), 1)

    canonical_key = normalize_intervention(intervention_type) or "construction_ban"
    return {
        "multi_ward": True,
        "intervention_type": canonical_key,
        "intervention_label": canonical_key.replace("_", " ").title(),
        "total_wards_evaluated": len(results),
        "mean_percentage_reduction": avg_pct,
        "total_reduction_points_sum": total_drop,
        "best_performing_ward": results[0]["ward_name"],
        "highest_ward_drop": results[0]["average_reduction_points"],
        "ward_results": results,
    }


def simulate_citywide_intervention(
    intervention_type: str,
    intensity: float = 1.0,
    horizon_hours: int = 24,
    top_n: int = 10
) -> Dict[str, Any]:
    """Simulate intervention impact across the top critical reporting wards citywide."""
    heatmap = fetch_heatmap()
    ward_aqis = []

    if isinstance(heatmap, list):
        for item in heatmap:
            wid = item.get("ward_id")
            aqi_val = item.get("aqi", 0)
            if wid and aqi_val:
                ward_aqis.append((wid, aqi_val))
    elif isinstance(heatmap, dict):
        for f in heatmap.get("features", []):
            props = f.get("properties", {})
            wid = props.get("ward_id") or props.get("id")
            aqi_val = props.get("aqi", 0)
            if wid and aqi_val:
                ward_aqis.append((wid, aqi_val))

    ward_aqis.sort(key=lambda x: x[1], reverse=True)
    target_wards = [w[0] for w in ward_aqis[:top_n]] if ward_aqis else ["CANT_1", "W02", "W03"]

    return simulate_multi_ward_intervention(
        ward_ids=target_wards,
        intervention_type=intervention_type,
        intensity=intensity,
        horizon_hours=horizon_hours,
    )
