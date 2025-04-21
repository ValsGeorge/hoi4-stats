#!/usr/bin/env python3
"""
Launcher script for HOI4 Soviet MIO Production Reader
"""

import os
import sys
import subprocess

def check_requirements():
    """Check if all requirements are met."""
    try:
        import tkinter
        return True
    except ImportError:
        print("Tkinter not found. This is required for the GUI.")
        if sys.platform == 'win32':
            print("On Windows, Tkinter usually comes with Python.")
            print("Make sure you have Python installed properly.")
        elif sys.platform == 'linux':
            print("On Linux, install Tkinter with your package manager.")
            print("For example: sudo apt-get install python3-tk")
        elif sys.platform == 'darwin':
            print("On macOS, Tkinter should be included with Python.")
            print("If not, try reinstalling Python.")
        return False

def main():
    """Main launcher function."""
    if not check_requirements():
        sys.exit(1)
        
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run the main application
    main_script = os.path.join(script_dir, "hoi4_mio_reader.py")
    if os.path.exists(main_script):
        try:
            if sys.platform == 'win32':
                # On Windows, use pythonw to avoid showing a console window
                subprocess.run([sys.executable, main_script], check=True)
            else:
                subprocess.run([sys.executable, main_script], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running the application: {e}")
            sys.exit(1)
    else:
        print(f"Main script not found: {main_script}")
        sys.exit(1)

if __name__ == "__main__":
    main() 