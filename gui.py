import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from typing import List
import threading
import openpyxl
from openpyxl.styles import PatternFill, Font
from equipment import format_game_date
from collections import defaultdict
from eq_definitions import EQ_TYPE

class AnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HOI4 Save Analyzer")
        self.root.geometry("800x600")
        
        # File type selection
        self.file_type = tk.StringVar(value="hoi4")
        self.setup_file_type_selector()
        
        # File list
        self.setup_file_list()
        
        # Buttons
        self.setup_buttons()
        
        # Progress area
        self.setup_progress_area()
        
        # Selected files
        self.selected_files = []
        
    def setup_file_type_selector(self):
        frame = ttk.LabelFrame(self.root, text="File Type", padding="5")
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Radiobutton(frame, text="HOI4 Saves (.hoi4)", 
                       variable=self.file_type, value="hoi4").pack(side=tk.LEFT)
        ttk.Radiobutton(frame, text="Melted Saves (.txt)", 
                       variable=self.file_type, value="txt").pack(side=tk.LEFT)
        ttk.Radiobutton(frame, text="JSON Files (.json)", 
                       variable=self.file_type, value="json").pack(side=tk.LEFT)
                       
    def setup_file_list(self):
        frame = ttk.LabelFrame(self.root, text="Selected Files", padding="5")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add listbox
        self.file_listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
    def setup_buttons(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(frame, text="Add Files", command=self.add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Clear All", command=self.clear_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Process Files", command=self.process_files).pack(side=tk.RIGHT, padx=5)
        
    def setup_progress_area(self):
        frame = ttk.LabelFrame(self.root, text="Progress", padding="5")
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(frame, textvariable=self.progress_var).pack(fill=tk.X)
        
        self.progress_bar = ttk.Progressbar(frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5,0))
        
    def add_files(self):
        filetypes = []
        if self.file_type.get() == "hoi4":
            filetypes = [("HOI4 Save Files", "*.hoi4")]
        elif self.file_type.get() == "txt":
            filetypes = [("Melted Save Files", "*.txt")]
        elif self.file_type.get() == "json":
            filetypes = [("JSON Files", "*.json")]
            
        files = filedialog.askopenfilenames(
            title="Select files",
            filetypes=filetypes
        )
        
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                self.file_listbox.insert(tk.END, os.path.basename(file))
                
    def remove_selected(self):
        selection = self.file_listbox.curselection()
        for index in reversed(selection):
            self.file_listbox.delete(index)
            self.selected_files.pop(index)
            
    def clear_files(self):
        self.file_listbox.delete(0, tk.END)
        self.selected_files.clear()
        
    def process_files(self):
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to process first.")
            return
            
        # Disable buttons during processing
        self.disable_buttons()
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self.process_files_thread)
        thread.start()
        
    def process_files_thread(self):
        try:
            total = len(self.selected_files)
            all_data = []
            
            for i, file in enumerate(self.selected_files, 1):
                # Update progress
                progress = (i / total) * 100
                self.root.after(0, self.update_progress, f"Processing {os.path.basename(file)}", progress)
                
                # Process file based on type
                data = None
                if self.file_type.get() == "hoi4":
                    data = self.process_hoi4_save(file)
                elif self.file_type.get() == "txt":
                    data = self.process_melted_save(file)
                elif self.file_type.get() == "json":
                    data = self.process_json(file)
                
                if data:
                    all_data.append(data)
            
            if all_data:
                self.create_combined_excel(all_data)
                self.root.after(0, self.update_progress, f"Processed {len(all_data)} files successfully!", 100)
            else:
                self.root.after(0, self.update_progress, "No data was processed!", 100)
                
        finally:
            self.root.after(0, self.enable_buttons)
    
    def process_json(self, file):
        """Process JSON file and return analysis data."""
        import equipment
        import buildings
        from excel_generator import create_excel_report
        
        base_name = os.path.splitext(os.path.basename(file))[0]
        
        # Run both analyses
        equipment_data = equipment.analyze_save_file(file)
        buildings_data = buildings.analyze_save_file(file)
        
        # Generate Excel report if we have data
        if equipment_data and buildings_data:
            create_excel_report(equipment_data, buildings_data, base_name)
        
        # Return equipment data for Excel generation
        return equipment_data

    def process_hoi4_save(self, file):
        """Process HOI4 save file and return analysis data."""
        from main import process_save_file
        # Generate JSON path
        base_name = os.path.splitext(os.path.basename(file))[0]
        json_path = os.path.join("melted_saves", f"{base_name}.json")
        # Process save
        if process_save_file(file):  # Remove json_path argument
            import equipment
            return equipment.analyze_save_file(json_path)
        return None
    
    def process_melted_save(self, file):
        """Process melted save file and return analysis data."""
        from main import process_save_file
        base_name = os.path.splitext(os.path.basename(file))[0]
        json_path = os.path.join("melted_saves", f"{base_name}.json")
        if process_save_file(file):  # Remove json_path argument
            import equipment
            return equipment.analyze_save_file(json_path)
        return None

    def create_combined_excel(self, all_data):
        """Create combined Excel file from multiple analyses."""
        try:
            wb = openpyxl.Workbook()
            wb.remove(wb.active)
            
            major_countries = ['USA', 'ENG', 'GER', 'ITA', 'SOV', 'JAP']

            # Custom function to convert any date format to sortable format
            def format_date_for_sort(date_str):
                if not date_str:
                    return ""
                    
                date_str = str(date_str).strip("' ")
                
                # Already in YYYY-MM-DD format
                if '-' in date_str and len(date_str) == 10:
                    return date_str
                    
                try:
                    # Try to parse various formats
                    if '/' in date_str:  # DD/MM/YYYY
                        day, month, year = map(int, date_str.split('/'))
                        return f"{year:04d}-{month:02d}-{day:02d}"
                    elif '-' in date_str:  # MMM-YY
                        month_str, year_str = date_str.split('-')
                        months = {'JAN':1, 'FEB':2, 'MAR':3, 'APR':4, 'MAY':5, 'JUN':6,
                                'JUL':7, 'AUG':8, 'SEP':9, 'OCT':10, 'NOV':11, 'DEC':12}
                        month = months[month_str.upper()]
                        year = 1900 + int(year_str) if int(year_str) > 50 else 2000 + int(year_str)
                        return f"{year:04d}-{month:02d}-01"
                except:
                    return date_str
                return date_str
            
            # Create sheets for each major country
            for country in major_countries:
                ws = wb.create_sheet(country)
                
                # Get equipment names specific to this country and map to types
                country_equipment = set()
                for data in all_data:
                    if country in data['country_data']:
                        # Map equipment names to their types using equipment_lines
                        country_data = data['country_data'][country]
                        for line in country_data.get('equipment_lines', []):
                            eq_name = line['equipment_name']
                            eq_type = EQ_TYPE.get(eq_name, eq_name)
                            country_equipment.add(eq_type)
                
                equipment_list = sorted(list(country_equipment))
                if not equipment_list:
                    continue  # Skip if country has no equipment
                
                # Setup headers using equipment types
                ws.cell(row=1, column=1, value='Date')
                for col, eq_type in enumerate(equipment_list, 2):
                    cell = ws.cell(row=1, column=col, value=eq_type)
                    cell.fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
                    cell.font = Font(color='FFFFFF', bold=True)
                
                # Add data rows mapping equipment names to types
                row = 2
                # Sort data by cleaned date string
                sorted_data = sorted(all_data, key=lambda x: format_date_for_sort(x.get('date', '')))
                for data in sorted_data:
                    if country in data['country_data']:
                        country_data = data['country_data'][country]
                        # Clean the date string before writing to cell
                        clean_date = data['date'].strip("' ") if data.get('date') else ''
                        ws.cell(row=row, column=1, value=clean_date)

                        # Create type-based factory counts from equipment lines
                        type_factories = defaultdict(int)
                        for line in country_data.get('equipment_lines', []):
                            eq_name = line['equipment_name']
                            eq_type = EQ_TYPE.get(eq_name, eq_name)
                            type_factories[eq_type] += line['active_factories']
                        
                        # Fill in factory counts by type
                        for col, eq_type in enumerate(equipment_list, 2):
                            factory_count = type_factories.get(eq_type, 0)
                            if factory_count > 0:
                                ws.cell(row=row, column=col, value=factory_count)
                        row += 1
                
                # Auto-adjust column widths
                for col in ws.columns:
                    max_length = 0
                    column = col[0].column_letter
                    for cell in col:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = (max_length + 2)
                    ws.column_dimensions[column].width = adjusted_width
            
            # Save combined Excel file
            excel_path = os.path.join('output', 'combined_production_analysis.xlsx')
            os.makedirs('output', exist_ok=True)
            wb.save(excel_path)
            print(f"Combined analysis saved to: {excel_path}")
            
        except Exception as e:
            print(f"Error creating combined Excel: {str(e)}")
            raise
    
    def update_progress(self, message, value):
        self.progress_var.set(message)
        self.progress_bar['value'] = value
        
    def disable_buttons(self):
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame) or isinstance(widget, ttk.LabelFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        child['state'] = 'disabled'
                        
    def enable_buttons(self):
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame) or isinstance(widget, ttk.LabelFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        child['state'] = 'normal'
