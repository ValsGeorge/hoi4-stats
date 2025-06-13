import json
from read_with_pyradox import load_json_file

def analyze_agency_data(data):
    """Analyze intelligence agencies for each country."""
    agency_data = {}
    
    if not isinstance(data, dict):
        return {}

    if 'countries' in data:
        for country_tag, country_data in data['countries'].items():
            if not isinstance(country_data, dict):
                continue
                
            # Skip if no intelligence agency
            if 'intelligence_agency' not in country_data:
                continue
                
            agency = country_data['intelligence_agency']
            if not isinstance(agency, dict):
                continue

            agency_info = {
                'name': agency.get('name', ''),
                'level': agency.get('building', 0),
                'max_operative_count': agency.get('max_operative_count', 0),
                'usable_operative_slots': agency.get('usable_operative_slots', 0),
                'operatives': [],
                'upgrades': agency.get('upgrades', {}),
                'defense': agency.get('defense', 0)
            }

            # Process operatives (support both array and dict formats)
            operatives = agency.get('operative', [])
            if isinstance(operatives, dict):
                # Count dict entries as operatives
                agency_info['operatives'] = [1 for _ in operatives.values() if isinstance(_, dict)]
            elif isinstance(operatives, list):
                # Count list entries
                agency_info['operatives'] = [1 for _ in operatives if isinstance(_, dict)]

            agency_data[country_tag] = agency_info

    return agency_data

def analyze_save_file(json_path):
    """Analyze the save file for intelligence agency data."""
    try:
        data = load_json_file(json_path)
        if not data:
            print("Failed to load JSON data")
            return None

        agency_data = analyze_agency_data(data)
        
        return {
            'date': data.get('date', 'Unknown Date'),
            'agency_data': agency_data
        }

    except Exception as e:
        print(f"Error analyzing intelligence agencies: {str(e)}")
        raise
