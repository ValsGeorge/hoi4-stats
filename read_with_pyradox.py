import sys
sys.path.append('pyradox/src')
import pyradox
import pyradox.datatype.time
import json
from pathlib import Path
import os
import shutil
import traceback
import sys
import argparse
from src.utils.melter import melt_save_file, is_binary_file, ensure_melted_saves_dir
import re
import time

# Set recursion limit higher for deeply nested files
sys.setrecursionlimit(10000)

# Global cache for parsed files
_file_cache = {}

def load_save_file(save_path, callback=None):
    """
    Load a HOI4 save file and return the parsed data.
    
    Args:
        save_path: Path to the save file
        callback: Optional callback function to report progress (takes percentage and status message)
    
    Returns:
        Parsed save file data
    """
    try:
        # Check if file needs melting
        if is_binary_file(save_path):
            print(f"Melting binary save file: {save_path}")
            if callback:
                callback(5, "Melting save file")
                
            # Create melted saves directory and get output path
            melted_saves_dir = ensure_melted_saves_dir()
            melted_path = os.path.join(melted_saves_dir, os.path.basename(save_path) + ".txt")
            
            # Melt the file
            success, melted_path = melt_save_file(save_path, melted_path)
            if not success:
                raise Exception(f"Failed to melt save file: {save_path}")
                
            # Use the melted path for further processing
            save_path = melted_path
            
        # Check if the file exists
        if not os.path.exists(save_path):
            raise FileNotFoundError(f"Save file not found: {save_path}")
        
        # Get file modification time to use as cache key
        file_stat = os.stat(save_path)
        cache_key = f"{save_path}:{file_stat.st_mtime}"
        
        # Check if we've already parsed this file
        if cache_key in _file_cache:
            if callback:
                callback(100, "Loaded from memory cache")
            return _file_cache[cache_key]
        
        # Get the HOI4 game directory
        game_dir = pyradox.get_game_directory('HoI4')
        if game_dir is None:
            print("Warning: Could not find HOI4 game directory. Some references may not resolve correctly.")
        
        # Parse the file
        try:
            if callback:
                callback(10, "Preparing to parse file")
                
            print(f"Parsing file: {save_path}")
            start_time = time.time()
            
            # Manual progress updates for better UI feedback
            if callback:
                callback(20, "Starting parse operation")
            
            # Parse the file (without token_callback which isn't supported)
            result = pyradox.parse_file(
                save_path, 
                game='HoI4', 
                path_relative_to_game=False, 
                verbose=True
            )
            
            # Simulate progress updates since we can't get real-time feedback
            if callback:
                callback(80, "Parse completed, finalizing")
            
            parse_time = time.time() - start_time
            print(f"\nSuccessfully parsed {save_path} in {parse_time:.2f} seconds")
            
            if callback:
                callback(95, "Finalizing")
                
            # Cache the result
            _file_cache[cache_key] = result
            
            if callback:
                callback(100, "Complete")
                
            return result
        except Exception as e:
            print(f"\nError parsing {save_path}: {str(e)}")
            traceback.print_exc()
            raise
    except Exception as e:
        print(f"Error processing save file: {str(e)}")
        traceback.print_exc()
        return None

def save_to_json(data, output_path):
    """Save the parsed data to a JSON file."""
    try:
        # Custom JSON encoder to handle pyradox types
        class PyradoxJSONEncoder(json.JSONEncoder):
            def default(self, obj):
                # Handle Time objects
                if isinstance(obj, pyradox.datatype.time.Time):
                    return str(obj)  # Convert to string format like "1936.1.1.12"
                # Handle other pyradox types by converting to Python types
                elif hasattr(obj, "to_python"):
                    return obj.to_python()
                # Default string conversion for any other non-serializable types
                else:
                    return str(obj)
        
        # Convert to a serializable format
        serializable_data = {}
        for key, value in data.items():
            # Convert keys to appropriate Python types
            if isinstance(key, pyradox.datatype.time.Time):
                # Format date keys in a sortable way
                py_key = str(key)
            else:
                # Use string representation for other keys
                py_key = str(key)
            
            # Use the key and value
            serializable_data[py_key] = value
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, cls=PyradoxJSONEncoder)
        print(f"Successfully saved parsed data to {output_path}")
        return True
    except Exception as e:
        print(f"Error saving to JSON: {str(e)}")
        traceback.print_exc()
        return False

def load_json_file(file_path):
    """Load a JSON file and convert date strings back to Time objects."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Convert date strings back to Time objects
        def convert_dates(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and re.match(r'^-?\d+\.\d+\.\d+(\.\d+)?$', value):
                        obj[key] = pyradox.datatype.time.Time.from_string(value)
                    elif isinstance(value, dict):
                        convert_dates(value)
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            if isinstance(item, str) and re.match(r'^-?\d+\.\d+\.\d+(\.\d+)?$', item):
                                value[i] = pyradox.datatype.time.Time.from_string(item)
                            elif isinstance(item, dict):
                                convert_dates(item)
            return obj
            
        return convert_dates(data)
    except Exception as e:
        print(f"Error loading JSON file: {str(e)}")
        traceback.print_exc()
        return None

def clear_cache():
    """Clear the file cache to free memory"""
    global _file_cache
    _file_cache.clear()

def process_save_file(save_path, output_json_path):
    """Process a save file and convert it to JSON."""
    try:
        # Define a progress reporting function
        def report_progress(percent, message):
            print(f"\rProgress: [{percent:3d}%] {message}", end="")
        
        # Parse the save file
        savegame = load_save_file(save_path, callback=report_progress)
        
        # Save to JSON
        if save_to_json(savegame, output_json_path):
            print(f"JSON data saved to: {output_json_path}")
            return True
        return False
    except Exception as e:
        print(f"Error processing save file: {str(e)}")
        return False