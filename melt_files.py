#!/usr/bin/env python3
"""
HOI4 Save File Melter - CLI Tool
A utility to melt binary HOI4 save files to text format.
"""

import os
import sys
import argparse
from src.utils.melter import melt_save_file, is_binary_file, ensure_melted_saves_dir, melt_multiple_files

def main():
    parser = argparse.ArgumentParser(description="Melt binary HOI4 save files to text format")
    parser.add_argument("files", nargs="*", help="HOI4 save files to melt")
    parser.add_argument("--output-dir", "-o", help="Directory to save melted files")
    parser.add_argument("--check", "-c", action="store_true", help="Check if files are binary or text")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # If no files were provided, show help and exit
    if not args.files:
        parser.print_help()
        return
    
    # Prepare output directory
    output_dir = args.output_dir or ensure_melted_saves_dir()
    print(f"Using output directory: {output_dir}")
    
    # Process each file
    for file_path in args.files:
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            continue
        
        # If we're just checking file type
        if args.check:
            if is_binary_file(file_path):
                print(f"{file_path}: BINARY")
            else:
                print(f"{file_path}: TEXT")
            continue
        
        # Process the file
        print(f"Processing: {file_path}")
        if not is_binary_file(file_path):
            print(f"Skipping {os.path.basename(file_path)}: already in text format")
            continue
        
        # Melt the file
        output_path = os.path.join(output_dir, os.path.basename(file_path) + ".txt")
        success, melted_path = melt_save_file(file_path, output_path)
        
        if success:
            print(f"✓ Successfully melted to: {melted_path}")
        else:
            print(f"✗ Failed to melt: {file_path}")

if __name__ == "__main__":
    main() 