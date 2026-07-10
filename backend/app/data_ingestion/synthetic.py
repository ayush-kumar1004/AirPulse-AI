"""
Synthetic Signal Service for the ET AI Hackathon backend.
Generates deterministic synthetic signals for Traffic and Construction using pure calculation.
No external APIs, databases, or randomness are used.
"""

import hashlib
from datetime import datetime
from typing import List, Union

from app.models.schemas import TrafficSignal, ConstructionSignal

def _pseudo_random_float(seed_str: str) -> float:
    """
    Internal helper to generate a deterministic float between 0.0 and 1.0.
    
    Args:
        seed_str (str): The seed string for hashing.
        
    Returns:
        float: A deterministic value in the range [0.0, 1.0).
    """
    h = hashlib.md5(seed_str.encode('utf-8')).hexdigest()
    # Take the first 8 characters of MD5 (32 bits) and convert to float
    return int(h[:8], 16) / 0xffffffff


def calculate_traffic_index(ward_id: str, dt: datetime) -> float:
    """
    Calculates a deterministic traffic index based on ward, date, and hour.
    
    Rules:
    - Weekdays: 08:00-10:00 & 18:00-20:00 -> High traffic
    - Weekdays: Late night -> Very low traffic
    - Weekend -> Moderate traffic
    - Returns between 0.0 and 1.0.
    
    Args:
        ward_id (str): The ward identifier.
        dt (datetime): The target datetime.
        
    Returns:
        float: Deterministic traffic index score.
    """
    weekday = dt.weekday()
    hour = dt.hour
    
    # Generate a deterministic base variation for this specific hour in this ward
    variation = _pseudo_random_float(f"{ward_id}-{dt.strftime('%Y-%m-%d')}-{hour}") * 0.2
    
    if weekday < 5:
        # Weekday
        if 8 <= hour < 10 or 18 <= hour < 20:
            base_idx = 0.7 + variation  # High: 0.7 to 0.9
        elif hour < 5 or hour >= 22:
            base_idx = 0.1 + (variation * 0.5)  # Very low: 0.1 to 0.2
        else:
            base_idx = 0.4 + variation  # Moderate: 0.4 to 0.6
    else:
        # Weekend
        if hour < 6 or hour >= 22:
            base_idx = 0.1 + (variation * 0.5)  # Very low: 0.1 to 0.2
        else:
            base_idx = 0.3 + variation  # Moderate: 0.3 to 0.5
            
    # Clamp tightly to bounds to strictly obey rules
    return round(min(1.0, max(0.0, base_idx)), 2)


def calculate_construction_sites(ward_id: str, dt: datetime) -> int:
    """
    Calculates the number of active construction sites deterministically.
    
    Rules:
    - Active only between 08:00 and 18:00.
    - Night hours -> 0 active sites.
    
    Args:
        ward_id (str): The ward identifier.
        dt (datetime): The target datetime.
        
    Returns:
        int: Number of active construction sites.
    """
    hour = dt.hour
    
    if 8 <= hour < 18:
        # Assign 1 to 3 active sites deterministically per ward
        variation = int(_pseudo_random_float(f"construction-{ward_id}") * 3) + 1
        return variation
        
    return 0


def generate_site_names(ward_id: str, num_sites: int) -> List[str]:
    """
    Generates deterministic, realistic-sounding construction site names.
    
    Args:
        ward_id (str): The ward identifier.
        num_sites (int): How many names to generate.
        
    Returns:
        List[str]: A list of synthetic construction site names.
    """
    if num_sites == 0:
        return []
        
    project_types = [
        "Road Upgrade",
        "Metro Expansion",
        "Flyover Repair",
        "Commercial Complex",
        "Drainage Overhaul"
    ]
    
    names = []
    zone_letter = ward_id[-1].upper() if ward_id else 'A'
    
    for i in range(num_sites):
        # Pick a project type deterministically
        proj_idx = int(_pseudo_random_float(f"site-name-{ward_id}-{i}") * len(project_types))
        names.append(f"{project_types[proj_idx]} Zone {zone_letter}-{i+1}")
        
    return names


def generate_note(ward_id: str, signal_type: str, value: Union[float, int]) -> str:
    """
    Generates a deterministic contextual note for the signals.
    
    Args:
        ward_id (str): The ward identifier.
        signal_type (str): Either "traffic" or "construction".
        value (Union[float, int]): The computed signal value.
        
    Returns:
        str: A human-readable note explaining the signal.
    """
    if signal_type == "traffic":
        if value >= 0.7:
            return "Heavy traffic congestion observed during rush hour patterns."
        elif value <= 0.2:
            return "Traffic is flowing smoothly with minimal congestion."
        else:
            return "Moderate traffic conditions."
            
    elif signal_type == "construction":
        if value > 0:
            return f"Construction active at {value} site(s) producing localized dust."
        else:
            return "No active construction outside of working hours."
            
    return ""


def get_traffic(ward_id: str, dt: datetime) -> TrafficSignal:
    """
    High-level public service function to get the current traffic signal.
    
    Args:
        ward_id (str): The target ward.
        dt (datetime): The target datetime.
        
    Returns:
        TrafficSignal: The complete, deterministic TrafficSignal Pydantic model.
    """
    traffic_index = calculate_traffic_index(ward_id, dt)
    note = generate_note(ward_id, "traffic", traffic_index)
    
    return TrafficSignal(
        ward_id=ward_id,
        traffic_index=traffic_index,
        note=note
    )


def get_construction(ward_id: str, dt: datetime) -> ConstructionSignal:
    """
    High-level public service function to get the current construction signal.
    
    Args:
        ward_id (str): The target ward.
        dt (datetime): The target datetime.
        
    Returns:
        ConstructionSignal: The complete, deterministic ConstructionSignal Pydantic model.
    """
    active_sites = calculate_construction_sites(ward_id, dt)
    site_names = generate_site_names(ward_id, active_sites)
    note = generate_note(ward_id, "construction", active_sites)
    
    return ConstructionSignal(
        ward_id=ward_id,
        active_sites=active_sites,
        site_names=site_names,
        note=note
    )
