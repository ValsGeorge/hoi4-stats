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
        
        # Equipment Analysis Frame
        analysis_frame = ttk.LabelFrame(self.root, text="Equipment Analysis", padding="10")
        analysis_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Search and Filter
        filter_frame = ttk.Frame(analysis_frame)
        filter_frame.pack(fill="x", pady=5)
        
        ttk.Label(filter_frame, text="Creator:").pack(side="left", padx=5)
        self.creator_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.creator_var, width=10).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Search", command=self.filter_equipment).pack(side="left", padx=5)
        
        # Equipment Treeview
        self.tree = ttk.Treeview(analysis_frame, columns=("Name", "ID", "Type", "Creator", "Origin"), show="headings")
        self.tree.heading("Name", text="Name")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Creator", text="Creator")
        self.tree.heading("Origin", text="Origin")
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
            
            # Save to JSON
            json_path = os.path.splitext(file_path)[0] + ".json"
            if save_to_json(self.save_data, json_path):
                self.status_var.set(f"Successfully saved to {json_path}")
            else:
                self.status_var.set("Failed to save JSON file")
                
            # Extract equipment data
            self.equipment_data = self.save_data.get("equipments", {})
            print("Equipment data structure:", self.equipment_data)  # Debug print
            self.update_equipment_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process file: {str(e)}")
            self.status_var.set("Error processing file")
            
    def update_equipment_list(self):
        if not self.equipment_data:
            return
            
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add equipment items
        for equipment_name, items in self.equipment_data.items():
            if isinstance(items, list):  # Check if items is a list
                for item in items:
                    if isinstance(item, dict):  # Check if item is a dictionary
                        self.tree.insert("", "end", values=(
                            equipment_name,
                            item.get("id", {}).get("id", "---"),
                            item.get("id", {}).get("type", "---"),
                            item.get("creator", "---"),
                            item.get("origin", "---")
                        ))
                
    def filter_equipment(self):
        creator = self.creator_var.get().upper()
        if not creator:
            self.update_equipment_list()
            return
            
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add filtered items
        for equipment_name, items in self.equipment_data.items():
            if isinstance(items, list):  # Check if items is a list
                for item in items:
                    if isinstance(item, dict) and item.get("creator", "").upper() == creator:
                        self.tree.insert("", "end", values=(
                            equipment_name,
                            item.get("id", {}).get("id", "---"),
                            item.get("id", {}).get("type", "---"),
                            item.get("creator", "---"),
                            item.get("origin", "---")
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
                
            # Extract equipment data
            self.equipment_data = self.save_data.get("equipments", {}),
            print("Equipment data structure:", self.equipment_data)  # Debug print
            self.update_equipment_list()
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