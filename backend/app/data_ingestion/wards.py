# TODO: Person A — load ward GeoJSON (app/data/wards.geojson) into PostGIS and expose helpers
# (ward centroids, ward lookup by point, GeoJSON FeatureCollection for the map).
import json
from pathlib import Path

WARDS_PATH = Path(__file__).resolve().parent.parent / "data" / "wards.geojson"


def load_wards_geojson() -> dict:
    """Return the ward polygons as a GeoJSON FeatureCollection."""
    # TODO: Person A — replace placeholder file with real ward boundaries for the chosen city.
    return json.loads(WARDS_PATH.read_text(encoding="utf-8"))
