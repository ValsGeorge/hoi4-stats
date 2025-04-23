import json
import sys
from pathlib import Path
from read_with_pyradox import load_save_file

def print_dict_structure(data, indent=0, max_depth=3, current_depth=0):
    if current_depth >= max_depth:
        print("  " * indent + "...")
        return
        
    if isinstance(data, dict):
        for key, value in data.items():
            print("  " * indent + f"{key}: ", end="")
            if isinstance(value, (dict, list)):
                print()
                if isinstance(value, dict):
                    print_dict_structure(value, indent + 1, max_depth, current_depth + 1)
                else:
                    print("  " * (indent + 1) + f"List with {len(value)} items")
            else:
                print(f"{type(value).__name__}")
    elif isinstance(data, list):
        print(f"List with {len(data)} items")
        if data and isinstance(data[0], (dict, list)):
            print_dict_structure(data[0], indent + 1, max_depth, current_depth + 1)

def interactive_navigate(data, path=[]):
    while True:
        print("\nCurrent path:", " -> ".join(path) if path else "root")
        
        if isinstance(data, dict):
            print("\nAvailable keys:")
            for i, key in enumerate(data.keys(), 1):
                print(f"{i}. {key}")
            print("0. Go back")
            print("q. Quit")
            
            choice = input("\nEnter choice (number or 'q'): ")
            if choice == 'q':
                return
            elif choice == '0':
                return
            elif choice.isdigit():
                key = list(data.keys())[int(choice) - 1]
                new_path = path + [key]
                print(f"\nSelected: {key}")
                print_dict_structure(data[key], max_depth=2)
                interactive_navigate(data[key], new_path)
                
        elif isinstance(data, list):
            print(f"\nList with {len(data)} items")
            if data:
                print("\nFirst item structure:")
                print_dict_structure(data[0], max_depth=2)
            print("\n0. Go back")
            print("q. Quit")
            
            choice = input("\nEnter choice ('0' or 'q'): ")
            if choice == 'q':
                return
            elif choice == '0':
                return
                
        else:
            print(f"\nValue: {data}")
            print("\n0. Go back")
            print("q. Quit")
            
            choice = input("\nEnter choice ('0' or 'q'): ")
            if choice == 'q':
                return
            elif choice == '0':
                return

def find_paths(data, search_str, current_path=None, found_paths=None):
    if current_path is None:
        current_path = []
    if found_paths is None:
        found_paths = []
        
    search_str = search_str.lower()
    
    if isinstance(data, dict):
        for key, value in data.items():
            new_path = current_path + [key]
            # Check if key contains search string
            if search_str in str(key).lower():
                found_paths.append(new_path)
            # Recursively search in value
            find_paths(value, search_str, new_path, found_paths)
            
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_path = current_path + [f"[{i}]"]
            find_paths(item, search_str, new_path, found_paths)
            
    return found_paths

def get_value_at_path(data, path):
    current = data
    for step in path:
        if step.startswith('[') and step.endswith(']'):
            # Handle list indices
            index = int(step[1:-1])
            current = current[index]
        else:
            # Handle dictionary keys
            current = current[step]
    return current

def main():
    file_path = r"C:\Users\Vals_\Desktop\Projects\hoi4-stats\melted_saves\autosave_4.json"
    print(f"Loading file: {file_path}")
    
    try:
        # Try loading as JSON first
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print("Loaded as JSON")
        except:
            # If not JSON, try loading as save file
            data = load_save_file(file_path)
            # Convert pyradox Tree to dictionary
            save_data = {}
            for key, value in data.items():
                if hasattr(value, 'to_python'):
                    save_data[key] = value.to_python()
                else:
                    save_data[key] = value
            data = save_data
            print("Loaded as save file")
            
        while True:
            search_str = input("\nEnter search string (or 'q' to quit): ")
            if search_str.lower() == 'q':
                break
                
            paths = find_paths(data, search_str)
            if paths:
                print(f"\nFound {len(paths)} paths containing '{search_str}':")
                for i, path in enumerate(paths, 1):
                    print(f"{i}. {' -> '.join(path)}")
            else:
                print(f"No paths found containing '{search_str}'")
                
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 