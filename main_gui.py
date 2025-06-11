import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
import json
from src.utils.melter import melt_save_file, is_binary_file, ensure_melted_saves_dir
from read_with_pyradox import load_save_file, save_to_json, clear_cache
from compare_view import CompareView
import threading
import time
import hashlib

class HOI4StatsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HOI4 Stats Analyzer")
        self.root.geometry("900x700")
        
        self.save_data = None
        self.equipment_data = None
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
        
        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # Create a notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        
        # Create main tab
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Single File Analysis")
        
        # Initialize the compare view
        self.compare_view = CompareView(self, self.notebook)
        
        self.create_widgets()
        
    def create_widgets(self):
        # File Selection Frame
        file_frame = ttk.LabelFrame(self.main_tab, text="Save File", padding="10")
        file_frame.pack(fill="x", padx=10, pady=5)
        
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=50).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Load", command=self.load_file).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Load JSON", command=self.load_json).pack(side="left", padx=5)
        
        # Progress bar for file loading
        progress_frame = ttk.Frame(self.main_tab)
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_var.set(0)
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.pack(side="top", fill="x")
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side="top", fill="x")
        
        # Analysis Frame
        analysis_frame = ttk.LabelFrame(self.main_tab, text="Industrial Organizations History", padding="10")
        analysis_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Search and Filter
        filter_frame = ttk.Frame(analysis_frame)
        filter_frame.pack(fill="x", pady=5)
        
        ttk.Label(filter_frame, text="Country:").pack(side="left", padx=5)
        self.country_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.country_var, width=10).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Search", command=self.filter_organizations).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Clear Cache", command=self.clear_cache).pack(side="right", padx=5)
        
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
        
        # Start loading in a background thread
        threading.Thread(target=self._load_file_thread, args=(file_path,), daemon=True).start()
    
    def _load_file_thread(self, file_path):
        """Process file loading in a background thread"""
        try:
            self.update_progress(0, "Processing...")
            
            # Check for cached file
            cache_path = self.get_cache_path(file_path)
            if os.path.exists(cache_path):
                self.update_progress(30, "Loading from cache...")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.update_progress(100, "Loaded from cache")
                self.root.after(0, lambda: self.finalize_load(data))
                return
            
            # Check if file is binary and melt if necessary
            if is_binary_file(file_path):
                self.update_progress(10, "Melting binary file...")
                melted_saves_dir = ensure_melted_saves_dir()
                output_path = os.path.join(melted_saves_dir, os.path.basename(file_path) + ".txt")
                success, melted_path = melt_save_file(file_path, output_path)
                if not success:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to melt the binary file"))
                    self.update_progress(0, "Ready")
                    return
                file_path = melted_path
                
            # Parse the save file with progress updates
            self.update_progress(20, "Parsing save file...")
            
            def progress_callback(percent, message):
                # Calculate overall progress (parsing is 20-80% of total process)
                overall_percent = 20 + (percent * 0.6)  # Scale from 20-80%
                self.update_progress(overall_percent, message)
            
            save_data = load_save_file(file_path, callback=progress_callback)
            
            # Convert pyradox Tree to dictionary
            self.update_progress(80, "Converting data...")
            data = {}
            for key, value in save_data.items():
                if hasattr(value, 'to_python'):
                    data[key] = value.to_python()
                else:
                    data[key] = value
            
            # Save to cache
            self.update_progress(90, "Saving to cache...")
            cache_path = self.get_cache_path(file_path)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            
            # Save to JSON
            json_path = os.path.splitext(file_path)[0] + ".json"
            if save_to_json(data, json_path):
                self.update_status(f"Successfully saved to {json_path}")
            
            self.update_progress(100, "Complete")
            
            # Update the UI with the processed data
            self.root.after(0, lambda: self.finalize_load(data))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to process file: {str(e)}"))
            self.update_progress(0, "Error")
    
    def update_progress(self, value, text):
        """Update the progress bar (thread-safe)"""
        self.root.after(0, lambda: self._update_progress_ui(value, text))
    
    def _update_progress_ui(self, value, text):
        """Update progress UI directly from the main thread"""
        self.progress_var.set(value)
        self.progress_label.config(text=text)
        self.status_var.set(text)
        self.root.update_idletasks()
    
    def update_status(self, text):
        """Update the status bar (thread-safe)"""
        self.root.after(0, lambda: self.status_var.set(text))
    
    def finalize_load(self, data):
        """Process the loaded data in the main thread"""
        self.save_data = data
        self.equipment_data = self.save_data.get("equipments", {})
        self.update_organizations_list()
        self.status_var.set("Ready")
    
    def get_cache_path(self, file_path):
        """Generate a cache file path based on the input file path and modification time"""
        file_stat = os.stat(file_path)
        file_hash = hashlib.md5((file_path + str(file_stat.st_mtime)).encode()).hexdigest()
        return os.path.join(self.cache_dir, file_hash + '.json')
    
    def clear_cache(self):
        """Clear all cached files"""
        try:
            # Clear memory cache
            clear_cache()
            
            # Clear file cache
            cache_files = os.listdir(self.cache_dir)
            for file in cache_files:
                if file.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, file))
            
            messagebox.showinfo("Cache Cleared", f"Successfully cleared {len(cache_files)} cached files")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear cache: {str(e)}")
            
    def get_equipment_name(self, equipment_id, equipment_type):
        """Convert equipment ID and type to its name"""
        if not hasattr(self, 'equipment_name_map'):
            self.equipment_name_map = {}
            if self.equipment_data:
                for name, items in self.equipment_data.items():
                    if isinstance(items, dict):
                        # Handle direct equipment entries
                        if "id" in items and isinstance(items["id"], dict):
                            item_id = items["id"].get("id")
                            item_type = items["id"].get("type")
                            if item_id is not None and item_type is not None:
                                self.equipment_name_map[(item_id, item_type)] = name
                    elif isinstance(items, list):
                        # Handle list of equipment entries
                        for item in items:
                            if isinstance(item, dict):
                                item_id = item.get("id", {}).get("id")
                                item_type = item.get("id", {}).get("type")
                                if item_id is not None and item_type is not None:
                                    self.equipment_name_map[(item_id, item_type)] = name
            else:
                print("No equipment data available")
        
        # Try to find the name in the map
        name = self.equipment_name_map.get((equipment_id, equipment_type))
        if name:
            return name
        else:
            # Try to find the equipment directly in the equipment_data
            for key, value in self.equipment_data.items():
                if isinstance(value, dict) and "id" in value:
                    if value["id"].get("id") == equipment_id and value["id"].get("type") == equipment_type:
                        name = key
                        break
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and "id" in item:
                            if item["id"].get("id") == equipment_id and item["id"].get("type") == equipment_type:
                                name = key
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
        if not countries:
            print("No countries found in save data")
            return
            
        # Add organization items
        for country_code, country_data in countries.items():
            if not isinstance(country_data, dict):
                print(f"Invalid country_data type: {type(country_data)}")
                continue
                
            # Get industrial organizations from production
            production = country_data.get("production", {})
            organizations = production.get("industrial_organisations", {})
            if not organizations:
                continue
                
            for org_name, org_data in organizations.items():
                if not isinstance(org_data, dict):
                    print(f"Invalid org_data type: {type(org_data)}")
                    continue
                    
                history = org_data.get("history", [])
                if not isinstance(history, list):
                    continue
                    
                for entry in history:
                    if not isinstance(entry, dict):
                        print(f"Invalid entry type: {type(entry)}")
                        continue
                        
                    equipment = entry.get("equipment", {})
                    data = entry.get("data", {})
                    
                    equipment_id = equipment.get("id")
                    equipment_type = equipment.get("type")
                    
                    equipment_name = self.get_equipment_name(equipment_id, equipment_type)
                    
                    date = data.get("date", "---")
                    units = data.get("units", "---")
                    
                    # Skip if units is 0
                    if units == 0:
                        continue
                        
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
                    
                    # Skip if units is 0
                    if data.get("units", 0) == 0:
                        continue
                        
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
            
        self.update_progress(0, "Loading JSON file...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.update_progress(50, "Parsing JSON...")
                self.save_data = json.load(f)
                
            self.equipment_data = self.save_data.get("equipments", {})
            self.update_progress(90, "Updating display...")
            self.update_organizations_list()
            self.update_progress(100, "Complete")
            self.status_var.set(f"Successfully loaded {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON file: {str(e)}")
            self.update_progress(0, "Error")

def main():
    root = tk.Tk()
    app = HOI4StatsGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 