import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import re
import os
import pickle
import threading
import concurrent.futures
import multiprocessing
import subprocess
import tempfile
import shutil
import logging
import datetime
import sys
import uuid
from equipment_name_finder import find_equipment_mappings
from src.utils.melter import melt_save_file, is_binary_file, ensure_melted_saves_dir

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, f"hoi4_reader_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HOI4MIOReader:
    def __init__(self, root):
        # Log application start
        logger.info("Starting HOI4 MIO Reader application")
        
        self.root = root
        self.root.title("HOI4 Soviet MIO Production Reader")
        self.root.geometry("900x700")  # Increased height for comparison view
        
        # Equipment name mappings
        self.equipment_mappings = {}
        
        # Create frame for file selection
        file_frame = ttk.Frame(root, padding="10")
        file_frame.pack(fill=tk.X)
        
        ttk.Button(file_frame, text="Select HOI4 Save File(s)", command=self.select_files).pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(file_frame, text="No files selected")
        self.file_label.pack(side=tk.LEFT, padx=5)
        
        # Add options frame
        options_frame = ttk.LabelFrame(root, text="Processing Options", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Cache options
        self.use_cache_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Use cache (faster for repeated files)", 
                        variable=self.use_cache_var).pack(side=tk.LEFT, padx=5)
        
        # Multi-processing options
        self.use_multiprocessing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Use multiprocessing", 
                        variable=self.use_multiprocessing_var).pack(side=tk.LEFT, padx=5)
        
        # Comparison mode toggle
        self.comparison_mode_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Compare multiple saves", 
                        variable=self.comparison_mode_var).pack(side=tk.LEFT, padx=5)
        
        # Use melt.exe for binary files
        self.use_melt_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Use melt.exe for binary files", 
                       variable=self.use_melt_var).pack(side=tk.LEFT, padx=5)
        
        # Create notebook for tabs (regular view and comparison view)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Regular view tab
        results_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(results_frame, text="Production History")
        
        # Create tree view for regular view
        self.tree = ttk.Treeview(results_frame)
        self.tree["columns"] = ("save_date", "organization", "equipment", "date", "units")
        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("save_date", anchor=tk.W, width=100)
        self.tree.column("organization", anchor=tk.W, width=150)
        self.tree.column("equipment", anchor=tk.W, width=200)  # Increased width for equipment
        self.tree.column("date", anchor=tk.W, width=100)
        self.tree.column("units", anchor=tk.W, width=80)
        
        self.tree.heading("#0", text="", anchor=tk.W)
        self.tree.heading("save_date", text="Save Date", anchor=tk.W)
        self.tree.heading("organization", text="Organization", anchor=tk.W)
        self.tree.heading("equipment", text="Equipment", anchor=tk.W)
        self.tree.heading("date", text="Production Date", anchor=tk.W)
        self.tree.heading("units", text="Units", anchor=tk.W)
        
        # Add scrollbar for regular view
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Comparison view tab
        comparison_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(comparison_frame, text="Comparison View")
        
        # Create tree view for comparison - organized by org then save date
        self.comparison_tree = ttk.Treeview(comparison_frame)
        self.comparison_tree["columns"] = ("save_date", "equipment", "date", "units", "change")
        self.comparison_tree.column("#0", width=150, stretch=tk.YES)  # Organization in hierarchy
        self.comparison_tree.column("save_date", anchor=tk.W, width=100)
        self.comparison_tree.column("equipment", anchor=tk.W, width=200)  # Increased width for equipment
        self.comparison_tree.column("date", anchor=tk.W, width=100)
        self.comparison_tree.column("units", anchor=tk.W, width=80)
        self.comparison_tree.column("change", anchor=tk.W, width=80)
        
        self.comparison_tree.heading("#0", text="Organization", anchor=tk.W)
        self.comparison_tree.heading("save_date", text="Save Date", anchor=tk.W)
        self.comparison_tree.heading("equipment", text="Equipment", anchor=tk.W)
        self.comparison_tree.heading("date", text="Production Date", anchor=tk.W)
        self.comparison_tree.heading("units", text="Units", anchor=tk.W)
        self.comparison_tree.heading("change", text="Change", anchor=tk.W)
        
        # Add scrollbar for comparison view
        comp_scrollbar = ttk.Scrollbar(comparison_frame, orient=tk.VERTICAL, command=self.comparison_tree.yview)
        self.comparison_tree.configure(yscrollcommand=comp_scrollbar.set)
        comp_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.comparison_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Selected files
        self.selected_files = []
        
        # Export button
        ttk.Button(file_frame, text="Export Results", command=self.export_results).pack(side=tk.RIGHT, padx=5)
        
        # Add Melt & Save button
        ttk.Button(file_frame, text="Melt & Save Binary File", command=self.melt_and_save_file).pack(side=tk.RIGHT, padx=5)
        
        # Add new Melt Multiple Files button
        ttk.Button(file_frame, text="Melt Multiple Files", command=self.melt_multiple_files).pack(side=tk.RIGHT, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        self.progress.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create cache directory if it doesn't exist
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # Create melted_saves directory if it doesn't exist
        self.melted_saves_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "melted_saves")
        if not os.path.exists(self.melted_saves_dir):
            os.makedirs(self.melted_saves_dir)
        
        # Temp directory for melted files
        self.temp_dir = tempfile.mkdtemp(prefix="hoi4_melted_")
        
        # Data storage for comparison
        self.all_save_data = {}  # Format: {save_date: {org_name: [entries]}}
        
        # Track melted files to clean up
        self.melted_files = []
    
    def __del__(self):
        # Clean up temporary files when the app is closed
        for temp_file in self.melted_files:
            try:
                os.remove(temp_file)
            except:
                pass
        
        # Clean up temp directory
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    def melt_hoi4_save(self, file_path, save_permanently=False):
        """Use melt.exe to convert binary HOI4 saves to readable format"""
        try:
            # Skip if not using melt
            if not self.use_melt_var.get():
                logger.info(f"Melt disabled by user preference for {file_path}")
                return file_path
            
            # Check if file is binary
            if not is_binary_file(file_path):
                logger.info(f"File appears to be text already: {file_path}")
                return file_path  # Already readable text
            
            # File is binary, need to melt it
            logger.info(f"File appears to be binary, attempting to melt: {file_path}")
            self.status_var.set(f"Melting binary save file: {os.path.basename(file_path)}")
            self.root.update_idletasks()
            
            # Create output file path
            if save_permanently:
                # Create a .melted file in the same directory as the original
                output_file = file_path + ".melted"
                logger.info(f"Will save melted file permanently to: {output_file}")
            else:
                # Use temp directory
                output_file = os.path.join(self.temp_dir, os.path.basename(file_path) + ".melted")
                logger.info(f"Will save melted file temporarily to: {output_file}")
            
            # Melt the file using the melter module
            success, melted_path = melt_save_file(file_path, output_file)
            
            if success:
                if not save_permanently:
                    self.melted_files.append(melted_path)  # Add to cleanup list only if temporary
                success_msg = f"Successfully melted: {os.path.basename(file_path)}"
                logger.info(success_msg)
                self.status_var.set(success_msg)
                return melted_path
            else:
                error_msg = f"Failed to melt file: {os.path.basename(file_path)}"
                logger.error(error_msg)
                self.status_var.set(error_msg)
                return file_path
                
        except Exception as e:
            error_msg = f"Error melting file: {str(e)}"
            logger.exception(error_msg)
            self.status_var.set(error_msg)
            return file_path  # Return original path on error
    
    def melt_and_save_file(self):
        """Prompt user to select a HOI4 save file, melt it, and save the result"""
        logger.info("User requested to melt and save a binary file")
        file_path = filedialog.askopenfilename(
            title="Select HOI4 Save File to Melt",
            filetypes=[("HOI4 Save Files", "*.hoi4"), ("All Files", "*.*")]
        )
        
        if not file_path:
            logger.info("User cancelled file selection")
            return
            
        logger.info(f"User selected file: {file_path}")
        
        # Default save path in the melted_saves folder with same name
        base_name = os.path.basename(file_path)
        default_save_path = os.path.join(self.melted_saves_dir, base_name + ".txt")
        
        # Check if file is binary
        if not is_binary_file(file_path):
            msg = f"File is already in text format, no need to melt: {os.path.basename(file_path)}"
            logger.info(msg)
            self.status_var.set(msg)
            return
                
        logger.info("File appears to be binary, prompting for save location")
        
        # Ask where to save the melted file
        save_path = filedialog.asksaveasfilename(
            title="Save Melted File As",
            defaultextension=".txt",
            initialfile=os.path.basename(file_path) + ".txt",
            initialdir=self.melted_saves_dir,
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if not save_path:
            logger.info("User cancelled save location selection")
            return
            
        logger.info(f"User selected save location: {save_path}")
        
        # Melt the file
        self.status_var.set(f"Melting binary save file: {os.path.basename(file_path)}")
        self.progress.start()
        self.root.update_idletasks()
        
        success, melted_path = melt_save_file(file_path, save_path)
        self.progress.stop()
        
        if success:
            success_msg = f"Successfully melted and saved to: {save_path}"
            logger.info(success_msg)
            self.status_var.set(success_msg)
            messagebox.showinfo("Success", success_msg)
        else:
            error_msg = f"Failed to melt file: {file_path}"
            logger.error(error_msg)
            self.status_var.set(error_msg)
            messagebox.showerror("Error", f"Failed to melt file. See log for details.")
            
    def melt_multiple_files(self):
        """Melt multiple HOI4 save files at once, saving to melted_saves folder"""
        logger.info("User requested to melt multiple files")
        file_paths = filedialog.askopenfilenames(
            title="Select HOI4 Save Files to Melt",
            filetypes=[("HOI4 Save Files", "*.hoi4"), ("All Files", "*.*")]
        )
        
        if not file_paths:
            logger.info("User cancelled file selection")
            return
            
        logger.info(f"User selected {len(file_paths)} files")
        
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Melting Progress")
        progress_window.geometry("400x250")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Add widgets to progress window
        ttk.Label(progress_window, text="Melting files...").pack(pady=10)
        
        # Current file label
        current_file_var = tk.StringVar(value="")
        ttk.Label(progress_window, textvariable=current_file_var).pack(pady=5)
        
        # Progress bar for current file
        file_progress = ttk.Progressbar(progress_window, orient=tk.HORIZONTAL, mode='indeterminate')
        file_progress.pack(fill=tk.X, padx=20, pady=5)
        
        # Overall progress
        progress_label = ttk.Label(progress_window, text="0 / 0 files processed")
        progress_label.pack(pady=5)
        overall_progress = ttk.Progressbar(progress_window, orient=tk.HORIZONTAL, length=360, mode='determinate')
        overall_progress.pack(fill=tk.X, padx=20, pady=5)
        
        # Status text
        status_text = tk.Text(progress_window, height=5, width=40, wrap=tk.WORD)
        status_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Function to append to status text
        def add_status(msg):
            status_text.configure(state=tk.NORMAL)
            status_text.insert(tk.END, msg + "\n")
            status_text.see(tk.END)
            status_text.configure(state=tk.DISABLED)
            progress_window.update()
        
        # Configure status text
        status_text.configure(state=tk.DISABLED)
        
        # Start processing
        file_progress.start()
        total_files = len(file_paths)
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        # Ensure the melted_saves directory exists
        if not os.path.exists(self.melted_saves_dir):
            os.makedirs(self.melted_saves_dir)
            
        try:
            # Process each file
            for i, file_path in enumerate(file_paths):
                try:
                    base_name = os.path.basename(file_path)
                    current_file_var.set(f"Processing: {base_name}")
                    progress_label.config(text=f"{i} / {total_files} files processed")
                    overall_progress["value"] = (i / total_files) * 100
                    progress_window.update()
                    
                    # Check if file is binary
                    if not is_binary_file(file_path):
                        add_status(f"Skipped {base_name}: already in text format")
                        skip_count += 1
                        continue
                    
                    # Define output path
                    output_path = os.path.join(self.melted_saves_dir, base_name + ".txt")
                    
                    # Melt the file
                    success, melted_path = melt_save_file(file_path, output_path)
                    
                    if success:
                        add_status(f"Successfully melted: {base_name}")
                        success_count += 1
                    else:
                        add_status(f"Failed to melt: {base_name}")
                        fail_count += 1
                        
                except Exception as e:
                    logger.exception(f"Error processing {file_path}")
                    add_status(f"Error with {os.path.basename(file_path)}: {str(e)}")
                    fail_count += 1
            
            # Update final progress
            progress_label.config(text=f"{total_files} / {total_files} files processed")
            overall_progress["value"] = 100
            
            # Display final summary
            file_progress.stop()
            summary = f"Completed: {success_count} successful, {skip_count} skipped, {fail_count} failed"
            current_file_var.set(summary)
            
            # Add a close button
            ttk.Button(progress_window, text="Close", 
                      command=progress_window.destroy).pack(pady=10)
                      
        except Exception as e:
            logger.exception("Error in batch processing")
            add_status(f"Error in batch processing: {str(e)}")
            file_progress.stop()
    
    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Select HOI4 Save Files",
            filetypes=[("HOI4 Save Files", "*.hoi4"), ("All Files", "*.*")]
        )
        if files:
            self.selected_files = files
            self.file_label.config(text=f"{len(files)} file(s) selected")
            
            # Start processing in a separate thread to keep UI responsive
            self.progress.start()
            threading.Thread(target=self.process_files, daemon=True).start()
    
    def get_cache_path(self, file_path):
        """Generate a cache file path based on the input file."""
        # Create a unique identifier for the file (based on filename, size, and modification time)
        file_stat = os.stat(file_path)
        cache_key = f"{os.path.basename(file_path)}_{file_stat.st_size}_{file_stat.st_mtime}"
        import hashlib
        cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
        return os.path.join(cache_dir, f"{cache_key_hash}.cache")
    
    def extract_save_date(self, file_path):
        """Extract the save game date from the beginning of the file"""
        try:
            # Try to melt the file first if it's binary
            readable_path = self.melt_hoi4_save(file_path) if self.use_melt_var.get() else file_path
            
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(readable_path, 'r', encoding=encoding, errors='ignore') as file:
                        # Read first few lines (where date is typically located)
                        header = file.read(1000)
                        
                        # Try different date patterns that might be in the save file
                        date_patterns = [
                            r'date\s*=\s*"([^"]+)"',  # Standard date format
                            r'date\s*=\s*(\d{4}\.\d{1,2}\.\d{1,2})',  # Date without quotes
                            r'date\s*=\s*(\d{4})',  # Just the year
                            r'date\s*=\s*(\d{4}\.\d{1,2})',  # Year and month
                        ]
                        
                        for pattern in date_patterns:
                            date_match = re.search(pattern, header)
                            if date_match:
                                return date_match.group(1)
                        
                        # If no date found in the first 1000 characters, try reading more
                        file.seek(0)
                        header = file.read(5000)
                        for pattern in date_patterns:
                            date_match = re.search(pattern, header)
                            if date_match:
                                return date_match.group(1)
                except Exception as e:
                    logger.debug(f"Error reading file with {encoding} encoding: {str(e)}")
                    continue
            
            # If we couldn't find a date, use a generic placeholder
            logger.warning(f"Could not extract date from {file_path}")
            return "Unknown Date"
        except Exception as e:
            logger.error(f"Error extracting save date: {str(e)}")
            return "Unknown Date"
    
    def extract_balanced_block(self, content, start_pos):
        """Extract a block enclosed in balanced curly braces"""
        if start_pos >= len(content) or content[start_pos] != '{':
            return ""
            
        brace_level = 1
        end_pos = start_pos + 1
        
        for i in range(start_pos + 1, len(content)):
            if content[i] == '{':
                brace_level += 1
            elif content[i] == '}':
                brace_level -= 1
                if brace_level == 0:
                    end_pos = i
                    break
        
        if brace_level > 0:
            # Unbalanced braces
            return ""
            
        # Return the content inside the braces
        return content[start_pos + 1:end_pos]
    
    def direct_scan_for_mios(self, file_path):
        """
        Direct scan for any SOV_*_organization blocks, regardless of file structure
        Returns a dictionary of {org_name: [history_entries]}
        """
        result = {}
        
        # Try to melt the file first if it's binary
        readable_path = self.melt_hoi4_save(file_path) if self.use_melt_var.get() else file_path
        
        # Try different encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                self.status_var.set(f"Scanning with {encoding} encoding...")
                self.root.update_idletasks()
                
                # Pattern for finding SOV org declarations
                sov_pattern = re.compile(r'(SOV_[a-zA-Z0-9_]+_organization)\s*=\s*\{')
                history_pattern = re.compile(r'history\s*=\s*\{')
                
                with open(readable_path, 'r', encoding=encoding, errors='ignore') as file:
                    content = file.read()
                    
                    # First check if there are any SOV mentions at all
                    if 'SOV_' not in content:
                        self.status_var.set(f"No 'SOV_' string found in file with {encoding} encoding.")
                        continue
                    
                    # Find all SOV org declarations
                    for match in sov_pattern.finditer(content):
                        org_name = match.group(1)
                        start_pos = match.end() - 1  # Position of the opening {
                        
                        # Extract the entire organization block
                        org_content = self.extract_balanced_block(content, start_pos)
                        if not org_content:
                            continue
                        
                        # Find history entries in this organization
                        history_entries = []
                        history_matches = history_pattern.finditer(org_content)
                        
                        for h_match in history_matches:
                            h_start_pos = h_match.end()
                            history_block = self.extract_balanced_block(org_content, h_start_pos - 1)
                            
                            if history_block:
                                # Extract equipment info
                                equip_match = re.search(r'equipment\s*=\s*\{\s*id\s*=\s*(\d+)\s*type\s*=\s*(\d+)', history_block)
                                if equip_match:
                                    equip_id = equip_match.group(1)
                                    equip_type = equip_match.group(2)
                                    
                                    # Extract data block
                                    data_match = re.search(r'data\s*=\s*\{([^}]+)\}', history_block)
                                    if data_match:
                                        data_content = data_match.group(1)
                                        
                                        # Parse date and units
                                        date_match = re.search(r'date\s*=\s*"([^"]+)"', data_content)
                                        date = date_match.group(1) if date_match else "Initial"
                                        
                                        units_match = re.search(r'units\s*=\s*(\d+)', data_content)
                                        units = units_match.group(1) if units_match else "0"
                                        
                                        # Add to history entries
                                        history_entries.append({
                                            "equipment_id": equip_id,
                                            "equipment_type": equip_type,
                                            "date": date,
                                            "units": units
                                        })
                        
                        # Add this organization to results
                        result[org_name] = history_entries
                        
                        # Update status periodically
                        if len(result) % 5 == 0:
                            self.status_var.set(f"Found {len(result)} Soviet MIOs so far...")
                            self.root.update_idletasks()
                
                # If we found organizations, break out of the encoding loop
                if result:
                    break
                    
            except Exception as e:
                self.status_var.set(f"Error with {encoding} encoding: {str(e)}")
                self.root.update_idletasks()
        
        return result
    
    def process_files(self):
        try:
            self.status_var.set("Processing files...")
            self.root.update_idletasks()
            
            # Clear previous results
            for item in self.tree.get_children():
                self.tree.delete(item)
            for item in self.comparison_tree.get_children():
                self.comparison_tree.delete(item)
            
            # Clear comparison data
            self.all_save_data = {}
            
            total_orgs = 0
            total_history_entries = 0
            
            for file_path in self.selected_files:
                try:
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                    self.status_var.set(f"Reading {os.path.basename(file_path)} ({file_size:.1f} MB)...")
                    self.root.update_idletasks()
                    
                    # Extract the save date early for displaying in the tree view
                    save_date = self.extract_save_date(file_path)
                    
                    # Get equipment mappings from the file
                    readable_path = self.melt_hoi4_save(file_path) if self.use_melt_var.get() else file_path
                    print("DEBUG: About to get equipment mappings")
                    new_mappings = find_equipment_mappings(readable_path)
                    print(f"DEBUG: Got {len(new_mappings)} new mappings")
                    
                    # Print all mappings for debugging
                    # print("DEBUG: NEW MAPPINGS:")
                    # for name, (id_val, type_val) in new_mappings.items():
                    #     print(f"DEBUG: {name} -> (ID:{id_val}, Type:{type_val})")
                    
                    # Update the mappings
                    print(f"DEBUG: Current mappings count before update: {len(self.equipment_mappings)}")
                    self.equipment_mappings.update(new_mappings)
                    print(f"DEBUG: Total mappings after update: {len(self.equipment_mappings)}")
                    print("DEBUG: ALL MAPPINGS AFTER UPDATE:")
                    for name, (id_val, type_val) in self.equipment_mappings.items():
                        print(f"DEBUG: {name} -> (ID:{id_val}, Type:{type_val})")
                    
                    # Create a placeholder for this save's data in the comparison structure
                    if save_date not in self.all_save_data:
                        self.all_save_data[save_date] = {}
                    
                    # Try to use cache if enabled
                    cache_path = self.get_cache_path(file_path)
                    if self.use_cache_var.get() and os.path.exists(cache_path):
                        self.status_var.set(f"Loading from cache: {os.path.basename(file_path)}")
                        self.root.update_idletasks()
                        
                        try:
                            with open(cache_path, 'rb') as cache_file:
                                all_entries = pickle.load(cache_file)
                                
                            # Add entries to tree view
                            for entry in all_entries:
                                total_history_entries += 1
                                # Count unique organizations
                                if entry.get("is_first_entry", False):
                                    total_orgs += 1
                                    
                                # Add to regular tree view with save date
                                display_text = f"{entry.get('equipment_name', 'Unknown')} (ID:{entry['equipment_id']}, Type:{entry['equipment_type']})"
                                self.tree.insert("", tk.END, values=(
                                    save_date,
                                    entry["org_name"],
                                    display_text,
                                    entry["date"],
                                    entry["units"]
                                ))
                                
                                # Also store for comparison view
                                org_name = entry["org_name"]
                                if org_name not in self.all_save_data[save_date]:
                                    self.all_save_data[save_date][org_name] = []
                                self.all_save_data[save_date][org_name].append(entry)
                                
                            self.status_var.set(f"Loaded {len(all_entries)} entries from cache for {os.path.basename(file_path)}")
                            continue  # Skip to next file
                        except Exception as e:
                            self.status_var.set(f"Cache error: {str(e)}. Re-processing file.")
                    
                    # Direct scan for Soviet MIOs
                    print("DEBUG: Starting MIO scan")
                    mios_found = self.direct_scan_for_mios(file_path)
                    print(f"DEBUG: Found {len(mios_found)} MIOs")
                    
                    if mios_found:
                        print("DEBUG: Processing found MIOs")
                        all_entries = []
                        
                        for org_name, history_entries in mios_found.items():
                            print(f"DEBUG: Processing org: {org_name}")
                            # Get a display name for the organization
                            display_name = org_name.replace("SOV_", "").replace("_organization", "").replace("_", " ").title()
                            
                            # Make sure this org exists in the comparison data structure
                            if display_name not in self.all_save_data[save_date]:
                                self.all_save_data[save_date][display_name] = []
                            
                            # Mark the first entry for this organization
                            first_entry = True
                            
                            # Add history entries to the tree
                            if history_entries:
                                print(f"DEBUG: Processing {len(history_entries)} history entries")
                                for entry in history_entries:
                                    # Get equipment name if available
                                    equip_id = entry.get("equipment_id", "N/A")
                                    equip_type = entry.get("equipment_type", "N/A")
                                    
                                    print(f"DEBUG: Processing equipment ID={equip_id}, Type={equip_type}")
                                    
                                    # Convert to integers for comparison
                                    try:
                                        equip_id_int = int(equip_id)
                                        equip_type_int = int(equip_type)
                                        print(f"DEBUG: Converted to integers: ID={equip_id_int}, Type={equip_type_int}")
                                        
                                        equip_name = "Unknown"
                                        
                                        # Look up equipment name by ID and type
                                        for name, (id_val, type_val) in self.equipment_mappings.items():
                                            if id_val == equip_id_int and type_val == equip_type_int:
                                                equip_name = name
                                                print(f"DEBUG: Found exact match: {name}")
                                                break
                                        
                                        # If not found, try to find by ID only
                                        if equip_name == "Unknown":
                                            print("DEBUG: No exact match, trying ID only")
                                            for name, (id_val, type_val) in self.equipment_mappings.items():
                                                if id_val == equip_id_int:
                                                    equip_name = name
                                                    print(f"DEBUG: Found ID-only match: {name}")
                                                    break
                                        
                                        print(f"DEBUG: Final equipment name: {equip_name}")
                                        
                                    except ValueError as e:
                                        print(f"DEBUG: Error converting to integers: {str(e)}")
                                        equip_name = "Unknown"
                                    
                                    # Create an entry for our data structure
                                    entry_data = {
                                        "org_name": display_name,
                                        "equipment_id": equip_id,
                                        "equipment_type": equip_type,
                                        "equipment_name": equip_name,
                                        "date": entry.get("date", "Initial"),
                                        "units": entry.get("units", "0")
                                    }
                                    
                                    # Mark first entry for this organization
                                    if first_entry:
                                        entry_data["is_first_entry"] = True
                                        first_entry = False
                                        total_orgs += 1
                                    
                                    # Add to the list of all entries
                                    all_entries.append(entry_data)
                                    total_history_entries += 1
                                    
                                    # Add to tree view with save date and equipment name
                                    display_text = f"{equip_name} (ID:{equip_id}, Type:{equip_type})" if equip_name != "Unknown" else f"ID:{equip_id}, Type:{equip_type}"
                                    print(f"DEBUG: Display text: {display_text}")
                                    
                                    # Insert into tree view
                                    print("DEBUG: Inserting into tree")
                                    item = self.tree.insert("", tk.END, values=(
                                        save_date,
                                        display_name,
                                        display_text,
                                        entry.get("date", "Initial"),
                                        entry.get("units", "0")
                                    ))
                                    
                                    # Also store for comparison view
                                    self.all_save_data[save_date][display_name].append(entry_data)
                            else:
                                # Organization with no history entries
                                entry_data = {
                                    "org_name": display_name,
                                    "equipment_id": "N/A",
                                    "equipment_type": "N/A",
                                    "date": "N/A",
                                    "units": "N/A",
                                    "is_first_entry": True
                                }
                                all_entries.append(entry_data)
                                total_orgs += 1
                                
                                self.tree.insert("", tk.END, values=(
                                    save_date,
                                    display_name,
                                    "No history",
                                    "-",
                                    "-"
                                ))
                                
                                # Also store for comparison view
                                self.all_save_data[save_date][display_name].append(entry_data)
                        
                        # Cache results
                        if self.use_cache_var.get() and all_entries:
                            try:
                                with open(cache_path, 'wb') as cache_file:
                                    pickle.dump(all_entries, cache_file)
                            except Exception as e:
                                self.status_var.set(f"Warning: Couldn't save cache: {str(e)}")
                    else:
                        self.status_var.set("No Soviet MIOs found in this file.")
                        self.tree.insert("", tk.END, values=(
                            save_date,
                            "No Soviet MIOs found",
                            "Try checking the file",
                            "manually for",
                            "SOV_ strings"
                        ))
                
                except Exception as e:
                    self.status_var.set(f"Error processing {os.path.basename(file_path)}: {str(e)}")
                    continue
            
            if total_orgs == 0:
                self.status_var.set("No organizations found.")
            else:
                self.status_var.set(f"Done. Found {total_orgs} Soviet organizations with {total_history_entries} production history entries.")
                
                # Build the comparison view if we have data from multiple saves
                if len(self.all_save_data) > 1 and self.comparison_mode_var.get():
                    self.build_comparison_view()
        
        finally:
            # Stop the progress bar
            self.progress.stop()
    
    def build_comparison_view(self):
        """Build the comparison view to compare data from multiple save files"""
        self.status_var.set("Building comparison view...")
        self.root.update_idletasks()
        
        # Start by getting all unique organizations across all save files
        all_orgs = set()
        for save_date, orgs in self.all_save_data.items():
            all_orgs.update(orgs.keys())
        
        # Get a sorted list of save dates (chronological if possible)
        save_dates = sorted(self.all_save_data.keys())
        
        # For each organization, add entries from each save
        for org_name in sorted(all_orgs):
            # Create parent node for this organization
            org_node = self.comparison_tree.insert("", tk.END, text=org_name, open=True)
            
            # Track the last units count to calculate changes
            last_units = {}  # Format: {equipment_id: units}
            
            # Add data for each save
            for save_date in save_dates:
                if org_name in self.all_save_data[save_date]:
                    # Create a save date node
                    save_node = self.comparison_tree.insert(org_node, tk.END, text=save_date, open=True)
                    
                    # Add all entries for this org in this save
                    for entry in self.all_save_data[save_date][org_name]:
                        equipment_id = entry.get("equipment_id", "N/A")
                        equipment_type = entry.get("equipment_type", "N/A")
                        prod_date = entry.get("date", "N/A")
                        units = entry.get("units", "0")
                        
                        # Calculate change from previous save
                        change = ""
                        if equipment_id != "N/A":
                            equip_key = f"{equipment_id}_{equipment_type}"
                            current_units = int(units) if units.isdigit() else 0
                            
                            if equip_key in last_units:
                                prev_units = last_units[equip_key]
                                delta = current_units - prev_units
                                if delta > 0:
                                    change = f"+{delta}"
                                elif delta < 0:
                                    change = str(delta)
                                else:
                                    change = "0"
                            
                            # Update for next comparison
                            last_units[equip_key] = current_units
                        
                        # Get equipment name if available
                        equip_name = "Unknown"
                        try:
                            equipment_id_int = int(equipment_id)
                            equipment_type_int = int(equipment_type)
                            
                            # Print the equipment ID and type we're looking for
                            print(f"Looking for equipment in comparison: ID={equipment_id}, Type={equipment_type}")
                            
                            # Print all mappings for this ID
                            print(f"All mappings with ID {equipment_id_int}:")
                            for name, (id_val, type_val) in self.equipment_mappings.items():
                                if id_val == equipment_id_int:
                                    print(f"  {name} -> (ID:{id_val}, Type:{type_val})")
                                    if type_val == equipment_type_int:
                                        equip_name = name
                                        print(f"  FOUND MATCH: {name}")
                            
                            # If not found, try to find by ID only
                            if equip_name == "Unknown":
                                for name, (id_val, type_val) in self.equipment_mappings.items():
                                    if id_val == equipment_id_int:
                                        equip_name = name
                                        print(f"  FOUND MATCH BY ID ONLY: {name}")
                                        break
                        except ValueError:
                            print(f"Could not convert ID or type to integer in comparison: ID={equipment_id}, Type={equipment_type}")
                        
                        print(f"Final equipment name in comparison: {equip_name}")
                        
                        display_text = f"{equip_name} (ID:{equipment_id}, Type:{equipment_type})" if equip_name != "Unknown" else f"ID:{equipment_id}, Type:{equipment_type}"
                        print(f"Displaying in comparison tree: {display_text}")
                        self.comparison_tree.insert(save_node, tk.END, text="", values=(
                            save_date,
                            display_text,
                            prod_date,
                            units,
                            change
                        ))
                else:
                    # Organization doesn't exist in this save
                    self.comparison_tree.insert(org_node, tk.END, text=save_date, values=(
                        save_date,
                        "N/A",
                        "N/A",
                        "N/A",
                        "-"
                    ))
        
        self.status_var.set("Comparison view built successfully.")
        # Switch to the comparison tab
        self.notebook.select(1)
    
    def export_results(self):
        if not self.tree.get_children():
            self.status_var.set("No data to export")
            return
        
        export_file = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if export_file:
            try:
                with open(export_file, 'w', newline='') as csvfile:
                    # Include save date in the export
                    csvfile.write("Save Date,Organization,Equipment,Production Date,Units\n")
                    for item_id in self.tree.get_children():
                        values = self.tree.item(item_id)['values']
                        csv_line = ','.join([f'"{str(v)}"' for v in values])
                        csvfile.write(f"{csv_line}\n")
                
                self.status_var.set(f"Results exported to {export_file}")
            except Exception as e:
                self.status_var.set(f"Error exporting results: {str(e)}")


if __name__ == "__main__":
    # Ensure multiprocessing works properly on Windows
    multiprocessing.freeze_support()
    
    root = tk.Tk()
    app = HOI4MIOReader(root)
    root.mainloop() 