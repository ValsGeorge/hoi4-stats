import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
import json
from src.utils.melter import melt_save_file, is_binary_file, ensure_melted_saves_dir
from read_with_pyradox import load_save_file, save_to_json

class HOI4StatsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HOI4 Stats Analyzer")
        self.root.geometry("800x600")
        
        self.save_data = None
        self.equipment_data = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # File Selection Frame
        file_frame = ttk.LabelFrame(self.root, text="Save File", padding="10")
        file_frame.pack(fill="x", padx=10, pady=5)
        
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=50).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Load", command=self.load_file).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Load JSON", command=self.load_json).pack(side="left", padx=5)
        
        # Analysis Frame
        analysis_frame = ttk.LabelFrame(self.root, text="Industrial Organizations History", padding="10")
        analysis_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Search and Filter
        filter_frame = ttk.Frame(analysis_frame)
        filter_frame.pack(fill="x", pady=5)
        
        ttk.Label(filter_frame, text="Country:").pack(side="left", padx=5)
        self.country_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.country_var, width=10).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Search", command=self.filter_organizations).pack(side="left", padx=5)
        
        # Organizations Treeview
        self.tree = ttk.Treeview(analysis_frame, columns=("Organization", "Country", "Date", "Equipment", "Amount"), show="headings")
        self.tree.heading("Organization", text="Organization")
        self.tree.heading("Country", text="Country")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Equipment", text="Equipment")
        self.tree.heading("Amount", text="Amount")
        self.tree.pack(fill="both", expand=True, pady=5)
        
        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w").pack(fill="x", padx=10, pady=5)
        
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select HOI4 Save File",
            filetypes=[("HOI4 Save Files", "*.hoi4"), ("All Files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            
    def load_file(self):
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showerror("Error", "Please select a save file first")
            return
            
        self.status_var.set("Processing file...")
        self.root.update()
        
        try:
            # Check if file is binary and melt if necessary
            if is_binary_file(file_path):
                self.status_var.set("Melting binary file...")
                melted_saves_dir = ensure_melted_saves_dir()
                output_path = os.path.join(melted_saves_dir, os.path.basename(file_path) + ".txt")
                success, melted_path = melt_save_file(file_path, output_path)
                if not success:
                    messagebox.showerror("Error", "Failed to melt the binary file")
                    return
                file_path = melted_path
                
            # Parse the save file
            self.status_var.set("Parsing save file...")
            save_data = load_save_file(file_path)
            
            # Convert pyradox Tree to dictionary
            self.save_data = {}
            for key, value in save_data.items():
                if hasattr(value, 'to_python'):
                    self.save_data[key] = value.to_python()
                else:
                    self.save_data[key] = value
            
            # Debug: Print all top-level keys
            print("Top-level keys in save data:", list(self.save_data.keys()))
            
            # Save to JSON
            json_path = os.path.splitext(file_path)[0] + ".json"
            if save_to_json(self.save_data, json_path):
                self.status_var.set(f"Successfully saved to {json_path}")
            else:
                self.status_var.set("Failed to save JSON file")
                
            # Extract equipment data for name mapping
            self.equipment_data = self.save_data.get("equipments", {})
            self.update_organizations_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process file: {str(e)}")
            self.status_var.set("Error processing file")
            
    def get_equipment_name(self, equipment_id, equipment_type):
        """Convert equipment ID and type to its name"""
        print(f"\nLooking up equipment: ID={equipment_id}, Type={equipment_type}")
        if not hasattr(self, 'equipment_name_map'):
            print("Building equipment name map...")
            self.equipment_name_map = {}
            if self.equipment_data:
                print(f"Equipment data keys: {list(self.equipment_data.keys())}")
                for name, items in self.equipment_data.items():
                    print(f"Processing equipment type: {name}")
                    if isinstance(items, dict):
                        # Handle direct equipment entries
                        if "id" in items and isinstance(items["id"], dict):
                            item_id = items["id"].get("id")
                            item_type = items["id"].get("type")
                            if item_id is not None and item_type is not None:
                                print(f"Mapping: ({item_id}, {item_type}) -> {name}")
                                self.equipment_name_map[(item_id, item_type)] = name
                    elif isinstance(items, list):
                        # Handle list of equipment entries
                        for item in items:
                            if isinstance(item, dict):
                                item_id = item.get("id", {}).get("id")
                                item_type = item.get("id", {}).get("type")
                                if item_id is not None and item_type is not None:
                                    print(f"Mapping: ({item_id}, {item_type}) -> {name}")
                                    self.equipment_name_map[(item_id, item_type)] = name
            else:
                print("No equipment data available")
        
        # Try to find the name in the map
        name = self.equipment_name_map.get((equipment_id, equipment_type))
        if name:
            print(f"Found name: {name}")
        else:
            print(f"No name found for ID={equipment_id}, Type={equipment_type}")
            # Try to find the equipment directly in the equipment_data
            for key, value in self.equipment_data.items():
                if isinstance(value, dict) and "id" in value:
                    if value["id"].get("id") == equipment_id and value["id"].get("type") == equipment_type:
                        name = key
                        print(f"Found direct match: {name}")
                        break
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and "id" in item:
                            if item["id"].get("id") == equipment_id and item["id"].get("type") == equipment_type:
                                name = key
                                print(f"Found direct match: {name}")
                                break
                        if name:
                            break
                if name:
                    break
        
        return name or f"Unknown ({equipment_id}, {equipment_type})"
        
    def update_organizations_list(self):
        if not self.save_data:
            print("No save data available")
            return
            
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Get countries data
        countries = self.save_data.get("countries", {})
        print("Countries found:", list(countries.keys()))
        if not countries:
            print("No countries found in save data")
            return
            
        # Add organization items
        for country_code, country_data in countries.items():
            print(f"\nProcessing country: {country_code}")
            if not isinstance(country_data, dict):
                print(f"Invalid country_data type: {type(country_data)}")
                continue
                
            # Get industrial organizations from production
            production = country_data.get("production", {})
            organizations = production.get("industrial_organisations", {})
            print(f"Organizations found for {country_code}:", list(organizations.keys()))
            if not organizations:
                print(f"No organizations found for {country_code}")
                continue
                
            for org_name, org_data in organizations.items():
                print(f"\nProcessing organization: {org_name}")
                if not isinstance(org_data, dict):
                    print(f"Invalid org_data type: {type(org_data)}")
                    continue
                    
                history = org_data.get("history", [])
                print(f"History entries: {len(history)}")
                if not isinstance(history, list):
                    print(f"Invalid history type: {type(history)}")
                    continue
                    
                for entry in history:
                    if not isinstance(entry, dict):
                        print(f"Invalid entry type: {type(entry)}")
                        continue
                        
                    equipment = entry.get("equipment", {})
                    data = entry.get("data", {})
                    
                    equipment_id = equipment.get("id")
                    equipment_type = equipment.get("type")
                    print(f"Equipment ID: {equipment_id}, Type: {equipment_type}")
                    
                    equipment_name = self.get_equipment_name(equipment_id, equipment_type)
                    print(f"Mapped equipment name: {equipment_name}")
                    
                    date = data.get("date", "---")
                    units = data.get("units", "---")
                    print(f"Date: {date}, Units: {units}")
                    
                    self.tree.insert("", "end", values=(
                        org_name,
                        country_code,
                        date,
                        equipment_name,
                        units
                    ))
                
    def filter_organizations(self):
        country = self.country_var.get().upper()
        if not country:
            self.update_organizations_list()
            return
            
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Get countries data
        countries = self.save_data.get("countries", {})
        if not countries:
            return
            
        # Add filtered items
        for country_code, country_data in countries.items():
            if country_code.upper() != country:
                continue
                
            if not isinstance(country_data, dict):
                continue
                
            # Get industrial organizations from production
            production = country_data.get("production", {})
            organizations = production.get("industrial_organisations", {})
            if not organizations:
                continue
                
            for org_name, org_data in organizations.items():
                if not isinstance(org_data, dict):
                    continue
                    
                history = org_data.get("history", [])
                if not isinstance(history, list):
                    continue
                    
                for entry in history:
                    if not isinstance(entry, dict):
                        continue
                        
                    equipment = entry.get("equipment", {})
                    data = entry.get("data", {})
                    
                    equipment_id = equipment.get("id")
                    equipment_type = equipment.get("type")
                    equipment_name = self.get_equipment_name(equipment_id, equipment_type)
                    
                    self.tree.insert("", "end", values=(
                        org_name,
                        country_code,
                        data.get("date", "---"),
                        equipment_name,
                        data.get("units", "---")
                    ))

    def load_json(self):
        file_path = filedialog.askopenfilename(
            title="Select JSON File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if not file_path:
            return
            
        self.status_var.set("Loading JSON file...")
        self.root.update()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.save_data = json.load(f)
                
            # Debug: Print all top-level keys
            print("Top-level keys in JSON data:", list(self.save_data.keys()))
                
            # Extract equipment data for name mapping
            self.equipment_data = self.save_data.get("equipments", {})
            self.update_organizations_list()
            self.status_var.set(f"Successfully loaded {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON file: {str(e)}")
            self.status_var.set("Error loading JSON file")

def main():
    root = tk.Tk()
    app = HOI4StatsGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 