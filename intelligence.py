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
                'operatives': [],
                'upgrades': {},
                'defense': agency.get('defense', 0),
                'operative_slots': agency.get('max_operative_count', 0)
            }
            
            # Process operatives
            if 'operative' in agency and isinstance(agency['operative'], list):
                for operative in agency['operative']:
                    if isinstance(operative, dict):
                        op_info = {
                            'name': operative.get('name', 'Unknown'),
                            'nationality': operative.get('nationalities', ''),
                            'skill': operative.get('skill', 0),
                            'traits': operative.get('traits', []),
                            'mission': operative.get('mission', {}),
                            'state': operative.get('state', '')
                        }
                        agency_info['operatives'].append(op_info)
            
            # Process upgrades
            if 'upgrades' in agency and isinstance(agency['upgrades'], dict):
                agency_info['upgrades'] = agency['upgrades']
            
            agency_data[country_tag] = agency_info

    return agency_data

def analyze_save_file(json_path):
    """Analyze the save file for intelligence agency data."""
    try:
        data = load_json_file(json_path)
        if not data:
            print("Failed to load JSON data")
            return None

        print("\nAnalyzing intelligence agencies...")
        agency_data = analyze_agency_data(data)
        
        return {
            'date': data.get('date', 'Unknown Date'),
            'agency_data': agency_data
        }

    except Exception as e:
        print(f"Error analyzing intelligence agencies: {str(e)}")
        raise
