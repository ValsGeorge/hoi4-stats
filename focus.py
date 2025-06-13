import json
from read_with_pyradox import load_json_file

def analyze_focus_data(data):
    """Analyze focus tree completion for each country."""
    focus_data = {}
    
    if not isinstance(data, dict):
        print("Input data is not a dictionary")
        return {}

    if 'countries' in data:
        for country_tag, country_data in data['countries'].items():
            if not isinstance(country_data, dict):
                continue
                
            focus_info = {}
            
            # Get focus tree name
            focus_info['focus_tree'] = country_data.get('focus_tree', '')
            
            # Extract focus data directly from the focus object
            if 'focus' in country_data:
                focus = country_data['focus']
                if isinstance(focus, dict):
                    focus_info.update({
                        'completed': focus.get('completed', []),
                        'progress': focus.get('progress', 0),
                        'current': focus.get('current', ''),
                        'paused': focus.get('paused', False)
                    })
            
            focus_data[country_tag] = focus_info

    return focus_data

def analyze_save_file(json_path):
    """Analyze the save file for focus tree data."""
    try:
        data = load_json_file(json_path)
        if not data:
            print("Failed to load JSON data")
            return None

        focus_data = analyze_focus_data(data)
        
        # Get save date
        save_date = data.get('date', 'Unknown Date')
        
        return {
            'date': save_date,
            'focus_data': focus_data
        }

    except Exception as e:
        print(f"Error analyzing focus trees: {str(e)}")
        raise
