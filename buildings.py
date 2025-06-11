import json
from read_with_pyradox import load_json_file
import os
from collections import defaultdict
from datetime import datetime
from state_defines import STATES

def format_game_date(date_str):
    """Convert game date to DD/MM/YYYY format."""
    try:
        # Parse the game date string (e.g., "1936.1.1")
        year, month, day = map(int, date_str.split('.')[:3])
        date_obj = datetime(year, month, day)
        return date_obj.strftime("%d/%m/%Y")  # Always use DD/MM/YYYY
    except:
        return date_str

def calculate_building_count(level_data):
    """Calculate actual building count from level data."""
    if isinstance(level_data, dict) and 'level' in level_data:
        levels = level_data['level']
        if isinstance(levels, list):
            return sum(levels) // 100
        return levels // 100
    return 0

def analyze_state_buildings(data):
    """Analyze buildings in each state."""
    state_buildings = defaultdict(dict)
    
    if 'states' in data:
        for state_id, state_data in data['states'].items():
            if isinstance(state_data, dict):
                # Get infrastructure level
                infra = state_data.get('building_levels', {}).get('infrastructure', 0)
                state_buildings[state_id]['infrastructure'] = calculate_building_count(infra)
                
                # Get other buildings
                buildings = state_data.get('buildings', {})
                for building_type, amount in buildings.items():
                    # Rename factories to shorter names
                    if building_type == 'industrial_complex':
                        building_type = 'civs'
                    elif building_type == 'arms_factory':
                        building_type = 'mils'
                    
                    state_buildings[state_id][building_type] = calculate_building_count(amount)
                    
    return state_buildings

def analyze_construction_queue(data):
    """Analyze construction queues for all countries."""
    construction_data = {}
    
    if 'countries' in data:
        for country_tag, country_data in data['countries'].items():
            if 'production' not in country_data:
                continue
                
            prod_data = country_data['production']
            if 'general_lines' not in prod_data or 'building' not in prod_data['general_lines']:
                continue
                
            country_queue = []
            building_lines = prod_data['general_lines']['building']
            if not isinstance(building_lines, list):
                continue
            
            for line in building_lines:
                if not isinstance(line, dict):
                    continue
                    
                building_info = line.get('building', {})
                state_id = str(building_info.get('location', 'Unknown'))
                state_name = STATES.get(state_id, "Unknown Location")
                
                # Convert building type to shorter name
                building_type = building_info.get('template', 'Unknown')
                if building_type == 'arms_factory':
                    building_type = 'mil'
                elif building_type == 'industrial_complex':
                    building_type = 'civ'
                
                line_data = {
                    'building': building_type,
                    'active_factories': line.get('active_factories', 0),
                    'produced': line.get('produced', 0),
                    'amount': line.get('amount', 0),
                    'speed': line.get('speed', 0),
                    'cost': line.get('cost', 0),
                    'created': format_game_date(line.get('created_date', 'Unknown')),
                    'state': state_id,
                    'state_name': state_name
                }
                
                if line_data['active_factories'] > 0:
                    country_queue.append(line_data)
            
            if country_queue:
                construction_data[country_tag] = country_queue
    
    return construction_data

def save_building_analysis(buildings_data, output_path):
    """Save building analysis with converted building counts."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("State Buildings Analysis\n")
        f.write("=====================\n\n")
        for state_id, buildings in sorted(buildings_data.items()):
            state_name = STATES.get(state_id, "Unknown")
            f.write(f"State {state_id} - {state_name}:\n")
            for building, amount in buildings.items():
                if amount > 0:  # Only show buildings that exist
                    f.write(f"  {building}: {amount}\n")
            f.write("\n")

def analyze_save_file(json_path):
    """Analyze the save file for building and construction data."""
    try:
        data = load_json_file(json_path)
        if not data:
            print("Failed to load JSON data")
            return None

        print("\nAnalyzing buildings...")
        state_buildings = analyze_state_buildings(data)
        
        print("Analyzing construction queues...")
        construction_queue = analyze_construction_queue(data)
        
        # Save analysis to files
        os.makedirs('output', exist_ok=True)
        
        # Save state buildings analysis
        with open(os.path.join('output', 'state_buildings.txt'), 'w', encoding='utf-8') as f:
            f.write("State Buildings Analysis\n")
            f.write("=====================\n\n")
            for state_id, buildings in sorted(state_buildings.items()):
                state_name = STATES.get(state_id, "Unknown")  # Get state name here
                f.write(f"State {state_id} - {state_name}:\n")
                for building, amount in buildings.items():
                    f.write(f"  {building}: {amount}\n")
                f.write("\n")
        
        # Save construction queue analysis
        with open(os.path.join('output', 'construction_queue.txt'), 'w', encoding='utf-8') as f:
            f.write("Construction Queue Analysis\n")
            f.write("=========================\n\n")
            for country, queue in sorted(construction_queue.items()):
                f.write(f"Country: {country}\n")
                f.write("-" * 40 + "\n")
                for item in queue:
                    f.write(f"Building: {item['building']}\n")
                    f.write(f"State: {item['state']} - {item['state_name']}\n")
                    f.write(f"Active Factories: {item['active_factories']}\n")
                    f.write(f"Produced: {item['produced']}\n")
                    f.write(f"Amount: {item['amount']}\n")
                    f.write(f"Speed: {item['speed']}\n")
                    f.write(f"Cost: {item['cost']}\n")
                    f.write(f"Started: {item['created']}\n")
                    f.write("\n")
        
        print("Building analysis complete!")
        return {
            'state_buildings': state_buildings,
            'construction_queue': construction_queue
        }

    except Exception as e:
        print(f"Error analyzing buildings: {str(e)}")
        raise
