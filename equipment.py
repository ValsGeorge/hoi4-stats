import json
from read_with_pyradox import load_json_file
import os
from collections import defaultdict

def get_equipment_details(data, equipment_id, equipment_type):
    """Find equipment details from the equipments section."""
    if 'equipments' in data:
        equipment_list = data['equipments']
        for eq_data in equipment_list:
            if isinstance(eq_data, dict):
                if eq_data.get('id') == equipment_id and eq_data.get('type') == equipment_type:
                    return eq_data
    return None

def get_equipment_name_from_registry(equipment_registry, eq_id, eq_type):
    """Find equipment name based on ID and type from the equipment registry."""
    for eq_name, variants in equipment_registry.items():
        for variant in variants:
            if variant['id'] == eq_id and variant['type'] == eq_type:
                return eq_name
    return f"Unknown Equipment (ID: {eq_id}, Type: {eq_type})"

def analyze_save_file(json_path):
    """Analyze the entire save file for relevant data."""
    try:
        data = load_json_file(json_path)
        if not data:
            print("Failed to load JSON data")
            return

        # First analyze equipment to build the registry
        equipment_registry = analyze_equipment(data)
        # Then analyze organizations with the equipment registry
        analyze_organizations(data, equipment_registry)

    except Exception as e:
        print(f"Error analyzing save file: {str(e)}")
        raise

def analyze_equipment(data):
    """Analyze equipment data from the parsed save file."""
    try:
        print("\nAnalyzing equipment data...")
        equipment_registry = {}
        
        # First, collect all equipment names and their details
        equipment = dict()
        if 'equipments' in data:
            for eq_name, eq_variants in data['equipments'].items():
                if isinstance(eq_variants, list):
                    equipment[eq_name] = []
                    for variant in eq_variants:
                        if isinstance(variant, dict) and 'id' in variant:
                            variant_info = {
                                'name': eq_name,
                                'id': variant['id'].get('id'),
                                'type': variant['id'].get('type'),
                                'creator': variant.get('creator'),
                            }
                            equipment[eq_name].append(variant_info)
                            
            print(f"Found {len(equipment)} unique equipment types")
            # print(f"Equipment: ", equipment)

        # Write results to a text file in project directory
        output_path = os.path.join('output', 'equipment_analysis.txt')
        os.makedirs('output', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("Equipment Analysis\n")
            f.write("=================\n\n")
            
            f.write("Equipment Types and Variants:\n")
            f.write("==========================\n\n")
            
            for eq_name, variants in sorted(equipment.items()):
                f.write(f"{eq_name}\n")                
                for variant in variants:
                    f.write(f"ID: {variant['id']}\n")
                    f.write(f"Type: {variant['type']}\n")
                    f.write(f"Creator: {variant['creator']}\n")
                    f.write("\n")
        
        print(f"Equipment analysis has been written to: {output_path}")
        return equipment
            
    except Exception as e:
        print(f"Error analyzing equipment: {str(e)}")
        print("Data structure where error occurred:")
        import json
        print(json.dumps(data.get('equipments', {}), indent=2)[:500])  # Print first 500 chars
        raise

def analyze_organizations(data, equipment_registry):
    """Analyze organizations from the parsed save file."""
    try:
        print("\nAnalyzing production organizations...")
        org_registry = {}
        
        # Process country data
        if 'countries' in data:
            for country_tag, country_data in data['countries'].items():
                # Get production data for country
                if 'production' in country_data:
                    prod_data = country_data['production']
                    
                    # Look for industrial organizations
                    if 'industrial_organisations' in prod_data:
                        orgs_data = prod_data['industrial_organisations']
                        # print(f"\nFound {len(orgs_data)} organizations in {country_tag}")
                        
                        # Process each organization
                        for org_name, org_data in orgs_data.items():
                            if isinstance(org_data, dict):
                                org_details = {
                                    'name': org_name,
                                    'country': country_tag,
                                    'id': org_data.get('id', {}).get('id'),
                                    'type': org_data.get('id', {}).get('type'),
                                    'history': []
                                }
                                
                                # Get production history
                                if 'history' in org_data:
                                    for entry in org_data['history']:
                                        if isinstance(entry, dict):
                                            eq_data = entry.get('equipment', {})
                                            prod_data = entry.get('data', {})
                                            eq_id = eq_data.get('id')
                                            eq_type = eq_data.get('type')
                                            eq_name = get_equipment_name_from_registry(equipment_registry, eq_id, eq_type)
                                            org_details['history'].append({
                                                'equipment_name': eq_name,
                                                'equipment_id': eq_id,
                                                'equipment_type': eq_type,
                                                'units': prod_data.get('units', 0)
                                            })
                                
                                org_registry[org_name] = org_details
                                # print(f"Added organization: {org_name}")

        # Write results to a text file in project directory
        output_path = os.path.join('output', 'organizations_analysis.txt')
        os.makedirs('output', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("Industrial Organizations Analysis\n")
            f.write("==============================\n\n")
            
            # Group by country
            by_country = defaultdict(list)
            for org_name, details in org_registry.items():
                by_country[details['country']].append((org_name, details))
            
            # Write organized by country
            for country, orgs in sorted(by_country.items()):
                f.write(f"\nCountry: {country}\n")
                f.write("=" * 40 + "\n")
                
                for org_name, details in sorted(orgs):
                    f.write(f"\nOrganization: {org_name}\n")
                    f.write(f"ID: {details['id']}, Type: {details['type']}\n")
                    
                    if details['history']:
                        f.write("\nProduction History:\n")
                        for entry in details['history']:
                            f.write(f"  Equipment: {entry['equipment_name']}\n")
                            f.write(f"  Units: {entry['units']}\n")
                            f.write("\n")
                    f.write("-" * 40 + "\n")

        print(f"Organizations analysis has been written to: {output_path}")
        return org_registry
            
    except Exception as e:
        print(f"Error analyzing organizations: {str(e)}")
        # Print the structure of a sample country for debugging
        if 'countries' in data and 'SOV' in data['countries']:
            print("\nExample SOV data structure:")
            print(json.dumps(data['countries']['SOV'].get('production', {}), indent=2)[:500])
        raise