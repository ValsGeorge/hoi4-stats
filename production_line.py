from typing import Dict, Any
from pyradox.datatype import Tree

def read_military_lines(save_data: Tree, country_tag: str = "SOV") -> None:
    """Read military production lines for a specific country."""
    
    # First check if we have a valid save_data object
    if not isinstance(save_data, Tree):
        print("Invalid save data format")
        return
    
    # Look for country data in different possible locations
    countries = None
    if "countries" in save_data:
        countries = save_data["countries"]
    else:
        # Try alternate paths if countries not found at root
        print("Could not find countries data in save file")
        return
        
    # Get specific country data
    country_data = countries.get(country_tag)
    if not country_data:
        print(f"Could not find data for country {country_tag}")
        return

    # Navigate to production data
    if "production" not in country_data:
        print(f"No production data found for {country_tag}")
        return
        
    production = country_data["production"]
    
    # Get military production lines
    if "military_production" not in production:
        print(f"No military production lines found for {country_tag}")
        return
        
    military_lines = production["military_production"]
    
    print(f"\nMilitary Production Lines for {country_tag}:")
    print("-" * 50)
    
    # Process each production line
    for line_id, line_data in military_lines.items():
        if not isinstance(line_data, (dict, Tree)):
            continue
            
        # Extract line details with safe access
        line_size = line_data.get("factory_level", 0)
        equipment = line_data.get("producer", {})
        efficiency = line_data.get("efficiency", 0)
        location = line_data.get("state", "Unknown")
        
        equipment_id = equipment.get("equipment_id")
        equipment_type = equipment.get("equipment_type")
        
        # Print the line details
        print(f"Line ID: {line_id}")
        print(f"  Factories: {line_size}")
        print(f"  Equipment: ID={equipment_id}, Type={equipment_type}")
        print(f"  Efficiency: {efficiency:.2f}")
        print(f"  State: {location}")
        print("-" * 30)

if __name__ == "__main__":
    # Example usage
    from read_with_pyradox import load_save_file
    
    save_file = input("Enter path to save file: ")
    save_data = load_save_file(save_file)
    
    if save_data:
        read_military_lines(save_data, "SOV")
    else:
        print("Failed to load save file")