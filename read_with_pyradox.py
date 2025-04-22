import sys
sys.path.append('pyradox/src')
import pyradox
import json
from pathlib import Path
import os
import shutil
import traceback
import sys
import argparse
from src.utils.melter import melt_save_file, is_binary_file, ensure_melted_saves_dir

# Set recursion limit higher for deeply nested files
sys.setrecursionlimit(10000)

def load_save_file(save_path):
    """Load a HOI4 save file and return the parsed data."""
    # Check if the file exists
    if not os.path.exists(save_path):
        raise FileNotFoundError(f"Save file not found: {save_path}")
    
    # Get the HOI4 game directory
    game_dir = pyradox.get_game_directory('HoI4')
    if game_dir is None:
        print("Warning: Could not find HOI4 game directory. Some references may not resolve correctly.")
    
    # Check if the file is binary and needs to be melted
    if is_binary_file(save_path):
        print(f"\nFile appears to be binary: {save_path}")
        print("Attempting to melt the file...")
        success, melted_path = melt_save_file(save_path)
        if success:
            print(f"Successfully melted file to: {melted_path}")
            save_path = melted_path
        else:
            print("Failed to melt the file. Attempting to parse it anyway...")
    
    # Parse the file
    try:
        print(f"Parsing file: {save_path}")
        result = pyradox.parse_file(save_path, game='HoI4', path_relative_to_game=False, verbose=True)
        print(f"\nSuccessfully parsed {save_path}")
        return result
    except Exception as e:
        print(f"\nError parsing {save_path}: {str(e)}")
        traceback.print_exc()
        raise

def save_to_json(data, output_path):
    """Save the parsed data to a JSON file."""
    try:
        # Convert to a serializable format
        serializable_data = {}
        for key, value in data.items():
            # Convert each top-level key to a string
            try:
                serializable_data[str(key)] = value
            except (TypeError, ValueError) as e:
                print(f"Warning: Could not serialize key {key}: {str(e)}")
                continue
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, default=str)
        print(f"Successfully saved parsed data to {output_path}")
        return True
    except Exception as e:
        print(f"Error saving to JSON: {str(e)}")
        traceback.print_exc()
        return False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Parse HOI4 save files using pyradox')
    parser.add_argument('save_path', nargs='?', 
                        default="C:/Users/Vals_/Desktop/Projects/hoi4-stats/melted_saves/autosave_4.txt",
                        help='Path to the HOI4 save file to parse')
    parser.add_argument('--output', '-o', help='Path to save the output JSON file')
    parser.add_argument('--melt-only', action='store_true', help='Only melt the file, do not parse it')
    args = parser.parse_args()
    
    save_path = args.save_path
    print(f"Attempting to process save file: {save_path}")
    
    # If melt-only mode is enabled
    if args.melt_only:
        if is_binary_file(save_path):
            print(f"Melting binary file: {save_path}")
            melted_saves_dir = ensure_melted_saves_dir()
            output_path = os.path.join(melted_saves_dir, os.path.basename(save_path) + ".txt")
            success, melted_path = melt_save_file(save_path, output_path)
            if success:
                print(f"Successfully melted file to: {melted_path}")
                return None
            else:
                print(f"Failed to melt file: {save_path}")
                return None
        else:
            print(f"File is already in text format: {save_path}")
            return None
    
    # Parse the save file
    try:
        savegame = load_save_file(save_path)
        
        # If we get here, parsing is successful
        print("Successfully processed the save file!")
        
        # Now try to extract some top-level keys to show the structure
        print("\nTop level keys in savegame:")
        top_keys = list(savegame.keys())
        for key in top_keys[:20]:  # Show only first 20 keys
            print(f"- {key}")
        
        if len(top_keys) > 20:
            print(f"... and {len(top_keys) - 20} more keys")
        
        # Save to JSON if requested
        if args.output:
            save_to_json(savegame, args.output)
        
        return savegame
    except Exception as e:
        print(f"Error processing save file: {str(e)}")
        return None

if __name__ == "__main__":
    main()