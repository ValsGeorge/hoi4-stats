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

def main():
    # Example usage
    save_path = "C:/Users/Vals_/Desktop/Projects/hoi4-stats/melted_saves/autosave_4.txt"
    # save_path = "C:/Users/Vals_/Desktop/Projects/hoi4-stats/melted_saves/savegame.txt"
    # save_path = "C:/Users/Vals_/Desktop/Projects/hoi4-stats/melted_saves/small_test.txt"
    
    print(f"Attempting to parse save file: {save_path}")
    savegame = load_save_file(save_path)
    
    # If we get here, parsing is successful
    print("Successfully processed the save file!")
    
    # Now try to extract some top-level keys to show the structure
    print("\nTop level keys in savegame:")
    for key in savegame.keys():
        print(f"- {key}")
        
    return savegame

if __name__ == "__main__":
    main()