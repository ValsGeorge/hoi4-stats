import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
from src.utils.melter import melt_save_file, is_binary_file, ensure_melted_saves_dir
from read_with_pyradox import load_save_file, save_to_json
import threading
import time
import hashlib

class CompareView:
    def __init__(self, parent, notebook):
        self.parent = parent
        self.notebook = notebook
        self.loaded_files = {}  # {file_id: {'path': path, 'data': data, 'name': display_name}}
        self.file_counter = 0
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
        
        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # Create the comparison tab
        self.compare_frame = ttk.Frame(notebook)
        notebook.add(self.compare_frame, text="Compare Files")
        
        self.create_widgets()
    
    def create_widgets(self):
        # File management frame
        self.file_frame = ttk.LabelFrame(self.compare_frame, text="Loaded Files", padding="10")
        self.file_frame.pack(fill="x", padx=10, pady=5)
        
        # Buttons for file operations
        btn_frame = ttk.Frame(self.file_frame)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="Add File", command=self.add_file).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected_file).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Compare", command=self.compare_files).pack(side="left", padx=5)
        
        # Progress bar for loading files
        self.progress_frame = ttk.Frame(self.file_frame)
        self.progress_frame.pack(fill="x", pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_var.set(0)
        self.progress_label = ttk.Label(self.progress_frame, text="Ready")
        self.progress_label.pack(side="top", fill="x")
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side="top", fill="x")
        
        # Listbox to display loaded files
        self.files_listbox_frame = ttk.Frame(self.file_frame)
        self.files_listbox_frame.pack(fill="both", expand=True, pady=5)
        
        self.files_listbox = tk.Listbox(self.files_listbox_frame, selectmode=tk.MULTIPLE, height=5)
        self.files_listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(self.files_listbox_frame, orient="vertical", command=self.files_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.files_listbox.config(yscrollcommand=scrollbar.set)
        
        # Comparison results frame
        self.results_frame = ttk.LabelFrame(self.compare_frame, text="Comparison Results", padding="10")
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create a notebook for comparison results
        self.results_notebook = ttk.Notebook(self.results_frame)
        self.results_notebook.pack(fill="both", expand=True)
        
        # Initial tab for instructions
        self.instructions_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.instructions_frame, text="Instructions")
        
        ttk.Label(self.instructions_frame, text="Add files to compare using the 'Add File' button.\n"
                                              "Select files and click 'Compare' to view the differences.", 
                 justify="center").pack(expand=True, pady=20)
    
    def add_file(self):
        """Add new files for comparison"""
        file_paths = filedialog.askopenfilenames(
            title="Select HOI4 Save Files",
            filetypes=[("HOI4 Save Files", "*.hoi4"), ("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if not file_paths:
            return
        
        # Start a thread to process all files
        threading.Thread(target=self._process_multiple_files, args=(file_paths,), daemon=True).start()
    
    def _process_multiple_files(self, file_paths):
        """Process multiple files in the background"""
        total_files = len(file_paths)
        for i, file_path in enumerate(file_paths):
            # Check if the file is already loaded
            skip_file = False
            for file_info in self.loaded_files.values():
                if file_info['path'] == file_path:
                    self.update_progress(
                        (i / total_files) * 100, 
                        f"Skipping already loaded file ({i+1}/{total_files}): {os.path.basename(file_path)}"
                    )
                    skip_file = True
                    break
            
            if skip_file:
                time.sleep(0.5)  # Brief pause to show skipped message
                continue
            
            # Update progress
            self.update_progress(
                (i / total_files) * 100, 
                f"Processing file {i+1}/{total_files}: {os.path.basename(file_path)}"
            )
            
            # Check if JSON or needs to be parsed
            if file_path.lower().endswith('.json'):
                self._load_json_file(file_path, i+1, total_files)
            else:
                self._load_hoi4_save(file_path, i+1, total_files)
        
        # Final update
        self.update_progress(100, f"Completed loading {total_files} files")
        time.sleep(1)  # Show completion message briefly
        self.update_progress(0, "Ready")
    
    def _load_hoi4_save(self, file_path, current_file=1, total_files=1):
        """Load and process a HOI4 save file with progress reporting"""
        try:
            file_name = os.path.basename(file_path)
            # Update UI
            self.update_progress(0, f"Processing {file_name} ({current_file}/{total_files})...")
            
            # Check if we already have a cached version of this file
            cache_path = self.check_cache(file_path)
            if cache_path:
                self.update_progress(30, f"Loading {file_name} from cache...")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.update_progress(100, f"Loaded {file_name} from cache")
                time.sleep(0.5)  # Brief pause to show completion
                self.finalize_file_load(file_path, data)
                return
                
            # No cache, process the file
            self.update_progress(10, f"Checking file type for {file_name}...")
            
            # Check if file is binary and melt if necessary
            if is_binary_file(file_path):
                self.update_progress(20, f"Melting binary file {file_name}...")
                melted_saves_dir = ensure_melted_saves_dir()
                output_path = os.path.join(melted_saves_dir, os.path.basename(file_path) + ".txt")
                success, melted_path = melt_save_file(file_path, output_path)
                if not success:
                    self.show_error(f"Failed to melt the binary file: {file_name}")
                    return
                file_path = melted_path
                
            # Define a progress callback
            def progress_callback(percent, message):
                # Scale the progress to fit within the overall progress (30% to 80%)
                overall = 30 + (percent * 0.5)
                self.update_progress(overall, f"{message} - {file_name} ({current_file}/{total_files})")
            
            # Parse the save file
            self.update_progress(30, f"Parsing {file_name}...")
            save_data = load_save_file(file_path, callback=progress_callback)
            
            # Convert pyradox Tree to dictionary
            self.update_progress(80, f"Converting data for {file_name}...")
            data = {}
            for key, value in save_data.items():
                if hasattr(value, 'to_python'):
                    data[key] = value.to_python()
                else:
                    data[key] = value
            
            # Save to cache
            self.update_progress(90, f"Saving {file_name} to cache...")
            cache_path = self.get_cache_path(file_path)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            
            self.update_progress(100, f"Completed processing {file_name}")
            time.sleep(0.5)  # Brief pause to show completion
            
            # Finalize loading
            self.finalize_file_load(file_path, data)
            
        except Exception as e:
            self.show_error(f"Failed to load file {os.path.basename(file_path)}: {str(e)}")
    
    def _load_json_file(self, file_path, current_file=1, total_files=1):
        """Load a JSON file for comparison"""
        try:
            file_name = os.path.basename(file_path)
            self.update_progress(0, f"Loading {file_name} ({current_file}/{total_files})...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                self.update_progress(50, f"Parsing JSON for {file_name}...")
                data = json.load(f)
            
            self.update_progress(100, f"Completed loading {file_name}")
            time.sleep(0.5)  # Brief pause to show completion
            
            # Finalize loading
            self.finalize_file_load(file_path, data)
            
        except Exception as e:
            self.show_error(f"Failed to load JSON file {os.path.basename(file_path)}: {str(e)}")
            self.update_progress(0, "Ready")
    
    def get_cache_path(self, file_path):
        """Generate a cache file path based on the input file's path and modification time"""
        file_stat = os.stat(file_path)
        file_hash = hashlib.md5((file_path + str(file_stat.st_mtime)).encode()).hexdigest()
        return os.path.join(self.cache_dir, file_hash + '.json')
    
    def check_cache(self, file_path):
        """Check if a valid cached version exists for the file"""
        cache_path = self.get_cache_path(file_path)
        if os.path.exists(cache_path):
            return cache_path
        return None
    
    def update_progress(self, value, text):
        """Update the progress bar and label (thread-safe)"""
        self.parent.root.after(0, lambda: self._update_progress_ui(value, text))
    
    def _update_progress_ui(self, value, text):
        """Update UI elements directly (called from main thread)"""
        self.progress_var.set(value)
        self.progress_label.config(text=text)
        self.parent.root.update_idletasks()
    
    def show_error(self, message):
        """Show error message (thread-safe)"""
        self.parent.root.after(0, lambda: messagebox.showerror("Error", message))
    
    def show_info(self, message):
        """Show info message (thread-safe)"""
        self.parent.root.after(0, lambda: messagebox.showinfo("Info", message))
    
    def finalize_file_load(self, file_path, data):
        """Add loaded file data to the UI (thread-safe)"""
        self.parent.root.after(0, lambda: self._finalize_file_load_ui(file_path, data))
    
    def _finalize_file_load_ui(self, file_path, data):
        """Finalize file loading in the UI thread"""
        # Add to loaded files
        file_id = self.file_counter
        self.file_counter += 1
        display_name = os.path.basename(file_path)
        self.loaded_files[file_id] = {
            'path': file_path,
            'data': data,
            'name': display_name
        }
        
        # Add to listbox
        self.files_listbox.insert(tk.END, display_name)
        
        # Reset progress
        self.progress_var.set(0)
        self.progress_label.config(text=f"Successfully loaded {display_name}")
        
        # Notify user
        self.show_info(f"File loaded: {display_name}")
    
    def remove_selected_file(self):
        """Remove selected files from the comparison"""
        selected_indices = self.files_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Info", "No files selected")
            return
        
        # Remove from end to beginning to avoid index issues
        for i in sorted(selected_indices, reverse=True):
            file_id = list(self.loaded_files.keys())[i]
            del self.loaded_files[file_id]
            self.files_listbox.delete(i)
        
        messagebox.showinfo("Success", "Selected files removed")
    
    def compare_files(self):
        """Compare the loaded files and display results"""
        selected_indices = self.files_listbox.curselection()
        if len(selected_indices) < 2:
            messagebox.showinfo("Info", "Select at least 2 files to compare")
            return
        
        # Clear previous comparison results
        for tab in self.results_notebook.tabs():
            self.results_notebook.forget(tab)
        
        # Get selected file data
        selected_files = {}
        for i in selected_indices:
            file_id = list(self.loaded_files.keys())[i]
            selected_files[file_id] = self.loaded_files[file_id]
        
        # Create tab for industrial organizations comparison
        self.compare_industrial_orgs(selected_files)
    
    def compare_industrial_orgs(self, selected_files):
        """Compare industrial organizations between files"""
        # Create a tab for this comparison
        orgs_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(orgs_frame, text="Industrial Organizations")
        
        # Create a treeview for the comparison
        columns = ["Organization", "Country"]
        for file_id, file_info in selected_files.items():
            columns.append(f"File: {file_info['name']}")
        
        tree = ttk.Treeview(orgs_frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(orgs_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Extract and compare organizations data
        all_orgs = {}  # {(org_name, country): {file_id: {unit_count, equipment_details}}}
        
        for file_id, file_info in selected_files.items():
            countries = file_info['data'].get('countries', {})
            
            for country_code, country_data in countries.items():
                if not isinstance(country_data, dict):
                    continue
                
                production = country_data.get('production', {})
                organizations = production.get('industrial_organisations', {})
                
                if not organizations:
                    continue
                
                for org_name, org_data in organizations.items():
                    if not isinstance(org_data, dict):
                        continue
                    
                    # Get the latest entry in history for this organization
                    history = org_data.get('history', [])
                    if not isinstance(history, list) or not history:
                        continue
                    
                    # Sort history by date if possible
                    try:
                        history = sorted(history, key=lambda x: x.get('data', {}).get('date', ''), reverse=True)
                    except Exception:
                        pass
                    
                    latest_entry = history[0]
                    equipment = latest_entry.get('equipment', {})
                    data = latest_entry.get('data', {})
                    
                    equipment_id = equipment.get('id')
                    equipment_type = equipment.get('type')
                    equipment_name = self.get_equipment_name(file_info['data'], equipment_id, equipment_type)
                    
                    org_key = (org_name, country_code)
                    if org_key not in all_orgs:
                        all_orgs[org_key] = {}
                    
                    all_orgs[org_key][file_id] = {
                        'units': data.get('units', 0),
                        'equipment': equipment_name,
                        'date': data.get('date', '---')
                    }
        
        # Populate the treeview
        for (org_name, country_code), file_data in all_orgs.items():
            row_values = [org_name, country_code]
            
            for file_id, file_info in selected_files.items():
                if file_id in file_data:
                    org_info = file_data[file_id]
                    row_values.append(f"{org_info['units']} {org_info['equipment']}")
                else:
                    row_values.append("N/A")
            
            tree.insert("", "end", values=row_values)
    
    def get_equipment_name(self, save_data, equipment_id, equipment_type):
        """Convert equipment ID and type to its name"""
        equipment_data = save_data.get("equipments", {})
        
        # Build equipment name map
        equipment_name_map = {}
        if equipment_data:
            for name, items in equipment_data.items():
                if isinstance(items, dict):
                    # Handle direct equipment entries
                    if "id" in items and isinstance(items["id"], dict):
                        item_id = items["id"].get("id")
                        item_type = items["id"].get("type")
                        if item_id is not None and item_type is not None:
                            equipment_name_map[(item_id, item_type)] = name
                elif isinstance(items, list):
                    # Handle list of equipment entries
                    for item in items:
                        if isinstance(item, dict):
                            item_id = item.get("id", {}).get("id")
                            item_type = item.get("id", {}).get("type")
                            if item_id is not None and item_type is not None:
                                equipment_name_map[(item_id, item_type)] = name
        
        # Try to find the name in the map
        name = equipment_name_map.get((equipment_id, equipment_type))
        if name:
            return name
        else:
            # Try to find the equipment directly in the equipment_data
            for key, value in equipment_data.items():
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