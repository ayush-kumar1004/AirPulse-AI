import json
import os

data_dir = os.path.dirname(os.path.abspath(__file__))

def validate(filename):
    path = os.path.join(data_dir, filename)
    size = os.path.getsize(path) / 1024 / 1024
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    features = data.get('features', [])
    count = len(features)
    
    if count > 0:
        geom_type = features[0]['geometry']['type']
        attrs = list(features[0]['properties'].keys())
    else:
        geom_type = "None"
        attrs = []
        
    print(f"--- {filename} ---")
    print(f"Size: {size:.2f} MB")
    print(f"Feature count: {count}")
    print(f"Geometry type: {geom_type}")
    print(f"Attributes: {attrs}")
    print()

validate('wards.geojson')
validate('industrial_zones.geojson')
