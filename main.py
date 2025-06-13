import os
import read_with_pyradox as parser
import equipment
import buildings
import tkinter as tk
from gui import AnalyzerGUI
from excel_generator import create_excel_report  # Fix the import name

def process_save_file(save_path):
    # Generate output JSON path in project directory
    base_name = os.path.splitext(os.path.basename(save_path))[0]
    json_path = os.path.join("melted_saves", f"{base_name}.json")

    # Ensure melted_saves directory exists
    os.makedirs("melted_saves", exist_ok=True)

    # Parse the save file to JSON
    parser.process_save_file(save_path, json_path)
    
    # Analyze both equipment and buildings
    equipment_data = equipment.analyze_save_file(json_path)
    buildings_data = buildings.analyze_save_file(json_path)
    
    # Generate Excel report with correct function name
    # if equipment_data and buildings_data:
    #     create_excel_report(equipment_data, buildings_data, base_name)
    
    return True

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalyzerGUI(root)
    root.mainloop()
