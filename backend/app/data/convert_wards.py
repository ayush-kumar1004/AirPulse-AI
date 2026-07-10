import json
import os

data_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(data_dir, 'wards.geojson')

with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for feature in data.get('features', []):
    props = feature.get('properties', {})
    
    # Map Datameet attributes to the ones expected by wards.py
    if 'Ward_No' in props:
        props['ward_id'] = str(props['Ward_No'])
    if 'Ward_Name' in props:
        props['ward_name'] = props['Ward_Name']
        
    feature['properties'] = props

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, separators=(',', ':'))

print("Converted wards.geojson attributes for compatibility.")
