import urllib.request
import urllib.parse
import json
import os

query = """
[out:json][timeout:25];
area["name"="Delhi"]->.searchArea;
(
  way["landuse"="industrial"](area.searchArea);
  relation["landuse"="industrial"](area.searchArea);
);
out geom;
"""

url = "https://overpass-api.de/api/interpreter"
data = urllib.parse.urlencode({'data': query}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'User-Agent': 'ET-Hackathon-Bot/1.0'})

print("Fetching from Overpass API...")
with urllib.request.urlopen(req) as response:
    result = json.loads(response.read().decode('utf-8'))

features = []
for element in result.get('elements', []):
    tags = element.get('tags', {})
    name = tags.get('name', 'Unnamed Industrial Zone')
    
    geom = element.get('geometry')
    if not geom:
        continue
        
    coordinates = [[ [pt['lon'], pt['lat']] for pt in geom ]]
    
    # Ensure closed polygon
    if coordinates[0][0] != coordinates[0][-1]:
        coordinates[0].append(coordinates[0][0])

    feature = {
        "type": "Feature",
        "properties": {
            "name": name,
            "id": element.get('id')
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": coordinates
        }
    }
    features.append(feature)

geojson = {
    "type": "FeatureCollection",
    "features": features
}

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'industrial_zones.geojson')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(geojson, f, indent=2)

print(f"Saved {len(features)} industrial zones to {output_path}")
