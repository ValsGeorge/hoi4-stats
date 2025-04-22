import sys
sys.path.append('pyradox/src')
import pyradox
import json
from pathlib import Path
import os
import shutil
import traceback
import sys

# Set recursion limit higher for deeply nested files
sys.setrecursionlimit(10000)

def load_save_file(save_path):
    """Load a HOI4 save file and return the parsed data."""
    # Get the HOI4 game directory
    game_dir = pyradox.get_game_directory('HoI4')
    if game_dir is None:
        raise Exception("Could not find HOI4 game directory")
    
    # Parse the file
    try:
        result = pyradox.parse_file(save_path, game='HoI4', path_relative_to_game=False, verbose=True)
        print(f"\nSuccessfully parsed {save_path}")
        return result
    except Exception as e:
        print(f"\nError parsing {save_path}: {str(e)}")
        traceback.print_exc()
        raise

def get_country_data(savegame, country_tag):
    """Get data for a specific country by its tag."""
    countries = savegame.find("countries")
    if not countries:
        print(f"No countries section found in savegame")
        return None
    return countries.find(country_tag)

def get_army_data(savegame, country_tag):
    """Get army data for a specific country."""
    country = get_country_data(savegame, country_tag)
    if country:
        return country.find("army")
    return None

def get_division_templates(savegame, country_tag):
    """Get division templates for a specific country."""
    country = get_country_data(savegame, country_tag)
    if country:
        return country.find("division_templates")
    return None

def save_to_file(savegame, output_path, max_depth=10):
    """Save the parsed savegame data to a file with depth limit."""
    try:
        # Manually convert to a simplified dictionary with depth limit
        data = convert_to_dict(savegame, max_depth)
        
        # Save as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"Successfully saved parsed data to {output_path}")
    except Exception as e:
        print(f"Error saving to file: {str(e)}")
        traceback.print_exc()

def convert_to_dict(tree, max_depth=10, current_depth=0):
    """Convert a Tree to a dict with a maximum depth to prevent recursion errors."""
    if current_depth >= max_depth:
        return {"max_depth_reached": True}
    
    result = {}
    
    # Process all key/value pairs in the tree
    for key, value in tree.items():
        # If value is another Tree, recursively convert it
        if isinstance(value, pyradox.datatype.tree.Tree):
            result[str(key)] = convert_to_dict(value, max_depth, current_depth + 1)
        else:
            # Convert primitive value to string to ensure JSON compatibility
            result[str(key)] = str(value)
    
    return result

def search_tree(tree, search_term, path="", results=None, max_depth=50, current_depth=0):
    """Search for a term in the tree and return paths where it's found."""
    if results is None:
        results = []
    
    # Avoid excessive recursion
    if current_depth >= max_depth:
        return results
    
    # Avoid too many results
    if len(results) > 100:
        print(f"Too many results (>100), stopping search")
        return results
    
    try:
        for key, value in tree.items():
            try:
                current_path = f"{path}/{key}" if path else str(key)
                
                # Check if the key contains the search term
                if search_term.lower() in str(key).lower():
                    results.append({
                        "path": current_path,
                        "type": "key",
                        "value": str(value) if not isinstance(value, pyradox.datatype.tree.Tree) else f"Tree with {len(value)} items"
                    })
                
                # Check if the value contains the search term (if it's not a subtree)
                if not isinstance(value, pyradox.datatype.tree.Tree) and search_term.lower() in str(value).lower():
                    results.append({
                        "path": current_path,
                        "type": "value",
                        "value": str(value)
                    })
                
                # If the value is a subtree, recursively search it
                if isinstance(value, pyradox.datatype.tree.Tree):
                    search_tree(value, search_term, current_path, results, max_depth, current_depth + 1)
            except Exception as e:
                print(f"Error processing key {key} at {path}: {str(e)}")
                continue
    except Exception as e:
        print(f"Error iterating tree at {path}: {str(e)}")
    
    return results

def extract_entity_history(savegame, entity_name):
    """Extract and display the history of a specific entity."""
    print(f"\nSearching for '{entity_name}' in savegame...")
    results = search_tree(savegame, entity_name, max_depth=50)
    
    if not results:
        print(f"No results found for '{entity_name}'")
        
        # Try a shorter search term as fallback
        parts = entity_name.split('_')
        if len(parts) > 1:
            shorter_term = parts[-2] + "_" + parts[-1]  # Use last two parts
            print(f"Trying with shorter search term: '{shorter_term}'")
            results = search_tree(savegame, shorter_term, max_depth=50)
            
            if not results:
                print(f"No results found for '{shorter_term}' either")
                
                # One more attempt with an even shorter term
                if len(parts) > 2:
                    shortest_term = parts[-1]  # Just use the last part
                    print(f"Trying with shortest search term: '{shortest_term}'")
                    results = search_tree(savegame, shortest_term, max_depth=50)
        
        if not results:
            print(f"Could not find any relevant data for '{entity_name}'")
            return None
    
    print(f"\nFound {len(results)} occurrences:")
    for idx, result in enumerate(results):
        print(f"{idx+1}. {result['path']} ({result['type']})")
        if result['type'] == 'value':
            print(f"   Value: {result['value']}")
    
    # Attempt to extract the entity's data
    for idx, result in enumerate(results):
        path_parts = result['path'].split('/')
        current_node = savegame
        
        try:
            for part in path_parts:
                if part and current_node:
                    if hasattr(current_node, 'find'):
                        current_node = current_node.find(part)
                    else:
                        current_node = None
                        break
            
            if current_node:
                print(f"\nData for occurrence {idx+1}:")
                if isinstance(current_node, pyradox.datatype.tree.Tree):
                    # Save this specific entity to a separate JSON file
                    entity_file = f"{entity_name.replace(' ', '_')}_data_{idx+1}.json"
                    with open(entity_file, 'w', encoding='utf-8') as f:
                        json.dump(convert_to_dict(current_node, max_depth=20), f, indent=2)
                    print(f"Detailed data saved to {entity_file}")
                    
                    # Display detailed view of the tree
                    def print_tree(node, indent=0):
                        for k, v in node.items():
                            prefix = "  " * indent
                            if isinstance(v, pyradox.datatype.tree.Tree):
                                print(f"{prefix}{k}:")
                                print_tree(v, indent + 1)
                            else:
                                print(f"{prefix}{k}: {v}")
                    
                    print_tree(current_node)
                else:
                    print(f"  Value: {current_node}")
        except Exception as e:
            print(f"Error extracting data for occurrence {idx+1}: {str(e)}")
    
    return results

def main():
    # Example usage
    save_path = "C:/Users/Vals_/Desktop/Projects/hoi4-stats/melted_saves/autosave_4.txt"
    # save_path = "C:/Users/Vals_/Desktop/Projects/hoi4-stats/melted_saves/savegame.txt"
    # save_path = "C:/Users/Vals_/Desktop/Projects/hoi4-stats/melted_saves/small_test.txt"
    
    print(f"Attempting to parse save file: {save_path}")
    savegame = load_save_file(save_path)
    
    # If we get here, parsing is successful
    print("Successfully processed the save file!")
    
    # Save the parsed data to a file with a depth limit
    output_path = "parsed_save.json"
    save_to_file(savegame, output_path, max_depth=50)
    
    # Now try to extract some top-level keys to show the structure
    print("\nTop level keys in savegame:")
    for key in savegame.keys():
        print(f"- {key}")
    
    # Search for the specific entity
    extract_entity_history(savegame, "SOV_tula_arms_plant_organization")
    
    return savegame

if __name__ == "__main__":
    main()