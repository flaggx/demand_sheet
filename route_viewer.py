#!/usr/bin/env python3
"""
Desktop application for viewing and printing route data from Excel sheets.
Filters by service day, service tech, and cycle frequency.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import webbrowser
import tempfile
import urllib.request
import re
import json


class RouteViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Route Viewer - Demand Sheet Generator")
        self.root.geometry("800x700")
        
        self.data = None
        self.filtered_data = None
        self.favorites = {}  # Dictionary: alias -> path/URL
        self.favorites_file = Path.home() / ".demand_sheet_favorites.json"
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # File selection
        ttk.Label(main_frame, text="Excel File or Google Sheets URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_path = tk.StringVar()
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(0, weight=1)
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path)
        file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        file_entry.bind('<Return>', lambda e: self.load_from_path())
        ttk.Button(file_frame, text="Browse", command=self.browse_file).grid(row=0, column=1)
        ttk.Button(file_frame, text="Load", command=self.load_from_path).grid(row=0, column=2, padx=(5, 0))

        # Favorites section (saved file paths / URLs)
        ttk.Label(file_frame, text="Favorites:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.favorites_var = tk.StringVar()
        self.favorites_combo = ttk.Combobox(file_frame, textvariable=self.favorites_var, state="readonly", width=50)
        self.favorites_combo.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        ttk.Button(file_frame, text="Load Favorite", command=self.load_selected_favorite).grid(row=1, column=2, padx=(5, 0), pady=(5, 0))
        ttk.Label(file_frame, text="Alias:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.favorite_alias_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.favorite_alias_var, width=30).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=(5, 0))
        ttk.Button(file_frame, text="Save as Favorite", command=self.save_current_to_favorites).grid(row=2, column=2, padx=(5, 0), pady=(5, 0))
        ttk.Button(file_frame, text="Remove Favorite", command=self.remove_selected_favorite).grid(row=3, column=2, padx=(5, 0), pady=(5, 0))
        
        # After file/favorites UI is built, load any saved favorites
        self.load_favorites()

        # Filters section
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding="10")
        filter_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        filter_frame.columnconfigure(1, weight=1)
        
        # Service Day filter
        ttk.Label(filter_frame, text="Service Day:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.service_day_var = tk.StringVar(value="All")
        self.service_day_combo = ttk.Combobox(filter_frame, textvariable=self.service_day_var, state="readonly", width=30)
        self.service_day_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # Service Tech filter
        ttk.Label(filter_frame, text="Service Tech:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.service_tech_var = tk.StringVar(value="All")
        self.service_tech_combo = ttk.Combobox(filter_frame, textvariable=self.service_tech_var, state="readonly", width=30)
        self.service_tech_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # Cycle Frequency filter
        ttk.Label(filter_frame, text="Cycle Frequency:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.cycle_freq_var = tk.StringVar(value="All")
        # Use a multi-select listbox for cycle frequency so multiple options can be chosen
        self.cycle_freq_listbox = tk.Listbox(
            filter_frame,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            height=5
        )
        self.cycle_freq_listbox.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.cycle_freq_listbox.bind('<<ListboxSelect>>', lambda event: self.apply_filters())
        
        # Bind filter changes
        self.service_day_var.trace('w', lambda *args: self.apply_filters())
        self.service_tech_var.trace('w', lambda *args: self.apply_filters())
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Preview Route", command=self.preview_route).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Print/Export", command=self.print_route).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Filters", command=self.clear_filters).pack(side=tk.LEFT, padx=5)
        
        # Data confirmation area
        confirmation_frame = ttk.LabelFrame(main_frame, text="Sheet Status", padding="10")
        confirmation_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        confirmation_frame.columnconfigure(0, weight=1)
        
        self.confirmation_var = tk.StringVar(value="No data loaded")
        confirmation_label = ttk.Label(confirmation_frame, textvariable=self.confirmation_var, 
                                      font=('Arial', 10), foreground='#666666', wraplength=700)
        confirmation_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Please select an Excel file")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN).grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
            self.load_from_path()

    # ----- Favorites handling -----

    def get_default_favorites(self):
        """Return default favorites for new users"""
        return {
            "Main Sheet": ""  # User needs to set the URL/path
        }
    
    def load_favorites(self):
        """Load favorites from disk into memory and refresh the UI"""
        try:
            if self.favorites_file.exists():
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Handle migration from old list format to new dict format
                if isinstance(data, list):
                    # Convert old format: list of paths/URLs -> dict with paths as both key and value
                    self.favorites = {path: path for path in data}
                elif isinstance(data, dict):
                    self.favorites = {str(k): str(v) for k, v in data.items()}
                else:
                    self.favorites = {}
            else:
                # File doesn't exist - initialize with defaults for new users
                self.favorites = self.get_default_favorites()
                self.save_favorites()
        except Exception:
            # If anything goes wrong, initialize with defaults
            self.favorites = self.get_default_favorites()
        
        # If favorites dict is empty, initialize with defaults
        if not self.favorites:
            self.favorites = self.get_default_favorites()
            self.save_favorites()
        
        self.refresh_favorites_ui()

    def save_favorites(self):
        """Persist favorites dictionary to disk"""
        try:
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, indent=2)
        except Exception as e:
            messagebox.showwarning("Favorites", f"Failed to save favorites:\n{e}")

    def refresh_favorites_ui(self):
        """Update the favorites dropdown with current aliases"""
        if hasattr(self, "favorites_combo"):
            aliases = sorted(self.favorites.keys())
            self.favorites_combo["values"] = aliases
            # Keep selection if still valid
            current = self.favorites_var.get()
            if current in aliases:
                self.favorites_combo.set(current)
            elif aliases:
                self.favorites_combo.set(aliases[0])
            else:
                self.favorites_combo.set("")

    def save_current_to_favorites(self):
        """Save current path/URL as a favorite with an alias"""
        path_value = self.file_path.get().strip()
        if not path_value:
            messagebox.showwarning("Favorites", "Nothing to save. Enter a file path or URL first.")
            return
        
        alias = self.favorite_alias_var.get().strip()
        if not alias:
            messagebox.showwarning("Favorites", "Please enter an alias/name for this favorite.")
            return
        
        if alias in self.favorites:
            # Ask if user wants to overwrite
            if not messagebox.askyesno("Favorites", f"Alias '{alias}' already exists. Overwrite?"):
                return
        
        self.favorites[alias] = path_value
        self.save_favorites()
        self.refresh_favorites_ui()
        self.favorites_var.set(alias)
        self.favorite_alias_var.set("")  # Clear alias field
        messagebox.showinfo("Favorites", f"Saved '{alias}' to favorites.")

    def load_selected_favorite(self):
        """Load the currently selected favorite"""
        selected_alias = self.favorites_var.get().strip()
        if not selected_alias and self.favorites:
            selected_alias = sorted(self.favorites.keys())[0]
        if not selected_alias:
            messagebox.showwarning("Favorites", "No favorite selected.")
            return
        if selected_alias not in self.favorites:
            messagebox.showwarning("Favorites", f"Alias '{selected_alias}' not found.")
            return
        path_value = self.favorites[selected_alias]
        self.file_path.set(path_value)
        self.load_from_path()

    def remove_selected_favorite(self):
        """Remove the currently selected favorite"""
        selected_alias = self.favorites_var.get().strip()
        if not selected_alias:
            messagebox.showwarning("Favorites", "No favorite selected.")
            return
        if selected_alias in self.favorites:
            if messagebox.askyesno("Favorites", f"Remove '{selected_alias}' from favorites?"):
                del self.favorites[selected_alias]
                self.save_favorites()
                self.refresh_favorites_ui()
        else:
            messagebox.showwarning("Favorites", f"Alias '{selected_alias}' not found.")
    
    def is_google_sheets_url(self, url):
        """Check if the given string is a Google Sheets URL"""
        if not isinstance(url, str):
            return False
        patterns = [
            r'https?://docs\.google\.com/spreadsheets/.*',
            r'https?://drive\.google\.com/file/d/.*',
        ]
        return any(re.match(pattern, url.strip()) for pattern in patterns)
    
    def convert_google_sheets_url(self, url):
        """Convert Google Sheets URL to CSV export URL"""
        url = url.strip()
        
        # Handle different Google Sheets URL formats
        # Format 1: https://docs.google.com/spreadsheets/d/{ID}/edit#gid={GID}
        # Format 2: https://docs.google.com/spreadsheets/d/{ID}/edit?usp=sharing
        # Format 3: https://drive.google.com/file/d/{ID}/view?usp=sharing
        
        # Extract spreadsheet ID
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        if not match:
            # Try drive.google.com format
            match = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
        
        if not match:
            raise ValueError("Could not extract spreadsheet ID from URL")
        
        spreadsheet_id = match.group(1)
        
        # Extract GID if present
        gid_match = re.search(r'[#&]gid=(\d+)', url)
        gid = gid_match.group(1) if gid_match else '0'
        
        # Convert to CSV export URL
        export_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
        return export_url
    
    def download_google_sheets(self, url):
        """Download Google Sheets as CSV and return the file path"""
        export_url = self.convert_google_sheets_url(url)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Download the file
            urllib.request.urlretrieve(export_url, temp_path)
            return temp_path
        except Exception as e:
            os.unlink(temp_path)  # Clean up on error
            raise Exception(f"Failed to download Google Sheets: {str(e)}")
    
    def load_from_path(self):
        """Load data from file path or Google Sheets URL"""
        path = self.file_path.get().strip()
        if not path:
            messagebox.showwarning("No Path", "Please enter a file path or Google Sheets URL")
            return
        
        self.load_data(path)
    
    def load_data(self, filepath):
        try:
            temp_file = None
            
            # Check if it's a Google Sheets URL
            if self.is_google_sheets_url(filepath):
                self.status_var.set("Downloading Google Sheets...")
                self.root.update()  # Update UI to show status
                temp_file = self.download_google_sheets(filepath)
                filepath = temp_file
                display_name = "Google Sheets"
            else:
                display_name = os.path.basename(filepath)
            
            # Try to read Excel/CSV file
            if filepath.endswith('.csv'):
                self.data = pd.read_csv(filepath)
            else:
                self.data = pd.read_excel(filepath)
            
            # Update status
            self.status_var.set(f"Loaded {len(self.data)} records from {display_name}")
            
            # Update filter dropdowns
            self.update_filters()
            
            # Show confirmation
            self.show_confirmation()
            
            # Clean up temp file if it was created
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass  # Ignore cleanup errors
            
        except Exception as e:
            error_msg = str(e)
            messagebox.showerror("Error", f"Failed to load file:\n{error_msg}")
            self.status_var.set("Error loading file")
            # Clean up temp file on error
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    def update_filters(self):
        if self.data is None:
            return
        
        # Get unique values for each filter column
        # Try common column name variations
        service_day_col = self.find_column(['Service Day', 'service_day', 'ServiceDay', 'Day', 'day'])
        service_tech_col = self.find_column(['Service Tech', 'service_tech', 'ServiceTech', 'Tech', 'tech', 'Technician'])
        cycle_freq_col = self.find_column(['Cycle Frequency', 'cycle_frequency', 'CycleFrequency', 'Frequency', 'frequency', 'Cycle'])
        
        # Update Service Day
        if service_day_col:
            values = ['All'] + sorted(self.data[service_day_col].dropna().unique().tolist())
            self.service_day_combo['values'] = values
        else:
            self.service_day_combo['values'] = ['All']
        
        # Update Service Tech
        if service_tech_col:
            values = ['All'] + sorted(self.data[service_tech_col].dropna().unique().tolist())
            self.service_tech_combo['values'] = values
        else:
            self.service_tech_combo['values'] = ['All']
        
        # Update Cycle Frequency (column C fallback if name not found)
        if cycle_freq_col is None and self.data is not None and len(self.data.columns) >= 3:
            cycle_freq_col = self.data.columns[2]

        # Populate cycle frequency multi-select listbox
        self.cycle_freq_listbox.delete(0, tk.END)
        if cycle_freq_col:
            values = sorted(self.data[cycle_freq_col].dropna().unique().tolist())
            for v in values:
                self.cycle_freq_listbox.insert(tk.END, v)
            # Select all by default -> behaves like "All"
            if values:
                self.cycle_freq_listbox.select_set(0, tk.END)
            self.cycle_freq_var.set("All")
        else:
            self.cycle_freq_var.set("All")
    
    def find_column(self, possible_names):
        """Find a column by trying multiple possible names (case-insensitive)"""
        if self.data is None:
            return None
        
        for name in possible_names:
            # Try exact match first
            if name in self.data.columns:
                return name
            # Try case-insensitive match
            for col in self.data.columns:
                if str(col).lower() == name.lower():
                    return col
        return None

    def get_selected_cycle_freqs(self):
        """
        Return a list of selected cycle frequency values from the multi-select
        listbox. If all (or none) are selected, returns None to mean "All".
        Also keeps self.cycle_freq_var in sync for header text.
        """
        if not hasattr(self, "cycle_freq_listbox"):
            return None

        size = self.cycle_freq_listbox.size()
        if size == 0:
            self.cycle_freq_var.set("All")
            return None

        indices = list(self.cycle_freq_listbox.curselection())
        if not indices:
            # Nothing explicitly selected -> treat as "All"
            self.cycle_freq_var.set("All")
            return None

        all_indices = list(range(size))
        if len(indices) == len(all_indices):
            # All selected -> same as "All"
            self.cycle_freq_var.set("All")
            return None

        selected_values = [self.cycle_freq_listbox.get(i) for i in indices]

        if len(selected_values) == 1:
            self.cycle_freq_var.set(str(selected_values[0]))
        else:
            self.cycle_freq_var.set("Multiple")

        return selected_values
    
    def apply_filters(self):
        if self.data is None:
            return
        
        filtered = self.data.copy()
        
        # Apply Service Day filter
        service_day_col = self.find_column(['Service Day', 'service_day', 'ServiceDay', 'Day', 'day'])
        if service_day_col and self.service_day_var.get() != "All":
            filtered = filtered[filtered[service_day_col] == self.service_day_var.get()]
        
        # Apply Service Tech filter
        service_tech_col = self.find_column(['Service Tech', 'service_tech', 'ServiceTech', 'Tech', 'tech', 'Technician'])
        if service_tech_col and self.service_tech_var.get() != "All":
            filtered = filtered[filtered[service_tech_col] == self.service_tech_var.get()]
        
        # Apply Cycle Frequency filter (supports multi-select, column C fallback)
        cycle_freq_col = self.find_column(['Cycle Frequency', 'cycle_frequency', 'CycleFrequency', 'Frequency', 'frequency', 'Cycle'])
        if cycle_freq_col is None and self.data is not None and len(self.data.columns) >= 3:
            cycle_freq_col = self.data.columns[2]

        if cycle_freq_col:
            selected_freqs = self.get_selected_cycle_freqs()
            # If some (but not all) options are selected, filter by them
            if selected_freqs:
                filtered = filtered[filtered[cycle_freq_col].isin(selected_freqs)]
        
        self.filtered_data = filtered
        self.status_var.set(f"Showing {len(filtered)} of {len(self.data)} records")
        self.show_confirmation()
    
    def clear_filters(self):
        self.service_day_var.set("All")
        self.service_tech_var.set("All")
        self.cycle_freq_var.set("All")
        # Reset cycle frequency multi-select to "all selected"
        if hasattr(self, "cycle_freq_listbox"):
            self.cycle_freq_listbox.selection_clear(0, tk.END)
            if self.cycle_freq_listbox.size() > 0:
                self.cycle_freq_listbox.select_set(0, tk.END)
        if self.data is not None:
            self.filtered_data = self.data.copy()
            self.status_var.set(f"Showing all {len(self.data)} records")
            self.show_confirmation()
    
    def show_confirmation(self):
        """Show confirmation that data is loaded and format is correct"""
        if self.data is None or self.data.empty:
            self.confirmation_var.set("No data loaded")
            return
        
        # Find key columns to verify format
        service_day_col = self.find_column(['Service Day', 'service_day', 'ServiceDay', 'Day', 'day'])
        service_tech_col = self.find_column(['Service Tech', 'service_tech', 'ServiceTech', 'Tech', 'tech', 'Technician'])
        cycle_freq_col = self.find_column(['Cycle Frequency', 'cycle_frequency', 'CycleFrequency', 'Frequency', 'frequency', 'Cycle'])
        if cycle_freq_col is None and len(self.data.columns) >= 3:
            cycle_freq_col = self.data.columns[2]
        
        # Build confirmation message
        total_records = len(self.filtered_data) if self.filtered_data is not None else len(self.data)
        total_cols = len(self.data.columns)
        
        msg_parts = [f"✓ Sheet loaded successfully: {total_records} record(s), {total_cols} column(s)"]
        
        # Check for expected columns
        found_cols = []
        if service_day_col:
            found_cols.append("Service Day")
        if service_tech_col:
            found_cols.append("Service Tech")
        if cycle_freq_col:
            found_cols.append("Cycle Frequency")
        
        if found_cols:
            msg_parts.append(f"✓ Found filter columns: {', '.join(found_cols)}")
        else:
            msg_parts.append("⚠ Warning: Could not find expected filter columns")
        
        # Show column names
        col_names = list(self.data.columns)[:10]  # Show first 10 columns
        if len(self.data.columns) > 10:
            col_names.append(f"... and {len(self.data.columns) - 10} more")
        msg_parts.append(f"Columns: {', '.join(str(c) for c in col_names)}")
        
        self.confirmation_var.set("\n".join(msg_parts))
    
    def preview_route(self):
        data = self.filtered_data if self.filtered_data is not None else self.data
        if data is None or data.empty:
            messagebox.showwarning("No Data", "Please load data and apply filters first.")
            return
        
        html_content = self.generate_html(data)
        
        # Save to temp file and open in browser
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            temp_path = f.name
        
        webbrowser.open(f'file://{temp_path}')
        self.status_var.set("Preview opened in browser")
    
    def print_route(self):
        data = self.filtered_data if self.filtered_data is not None else self.data
        if data is None or data.empty:
            messagebox.showwarning("No Data", "Please load data and apply filters first.")
            return
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Save Printable Route",
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        
        if filename:
            html_content = self.generate_html(data)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Open in browser for printing
            webbrowser.open(f'file://{os.path.abspath(filename)}')
            self.status_var.set(f"Route saved to {os.path.basename(filename)} - Use browser print function")
            messagebox.showinfo("Success", f"Route saved!\n\nOpen the file in your browser and use File > Print or Ctrl+P to print.")
    
    def generate_html(self, df):
        """Generate printable HTML from filtered data"""
        # Find column names
        service_day_col = self.find_column(['Service Day', 'service_day', 'ServiceDay', 'Day', 'day'])
        service_tech_col = self.find_column(['Service Tech', 'service_tech', 'ServiceTech', 'Tech', 'tech', 'Technician'])
        cycle_freq_col = self.find_column(['Cycle Frequency', 'cycle_frequency', 'CycleFrequency', 'Frequency', 'frequency', 'Cycle'])
        if cycle_freq_col is None and self.data is not None and len(self.data.columns) >= 3:
            cycle_freq_col = self.data.columns[2]

        # Get filter values for header. If "All" is selected but the data only
        # contains a single unique value for that field, show that value
        # instead of "All ...".
        if self.service_day_var.get() != "All":
            service_day = self.service_day_var.get()
        elif service_day_col and not df.empty:
            unique_days = df[service_day_col].dropna().unique()
            service_day = str(unique_days[0]) if len(unique_days) == 1 else "All Days"
        else:
            service_day = "All Days"

        if self.service_tech_var.get() != "All":
            service_tech = self.service_tech_var.get()
        elif service_tech_col and not df.empty:
            unique_techs = df[service_tech_col].dropna().unique()
            service_tech = str(unique_techs[0]) if len(unique_techs) == 1 else "All Techs"
        else:
            service_tech = "All Techs"

        # Cycle frequency header reflects multi-select: list selected items,
        # or "All Frequencies" when all/none are explicitly chosen.
        selected_cycle_freqs = self.get_selected_cycle_freqs()
        if not selected_cycle_freqs:
            if cycle_freq_col and not df.empty:
                unique_freqs = df[cycle_freq_col].dropna().unique()
                cycle_freq = str(unique_freqs[0]) if len(unique_freqs) == 1 else "All Frequencies"
            else:
                cycle_freq = "All Frequencies"
        else:
            if len(selected_cycle_freqs) == 1:
                cycle_freq = str(selected_cycle_freqs[0])
            else:
                cycle_freq = ", ".join(str(v) for v in selected_cycle_freqs)

        # Work on a copy where we drop columns that have no data (only headers)
        working_df = df.copy()
        non_empty_columns = []
        for col in working_df.columns:
            series = working_df[col]
            # Treat NaN and empty/whitespace-only strings as empty
            non_empty_mask = series.notna() & series.astype(str).str.strip().ne("")
            if non_empty_mask.any():
                non_empty_columns.append(col)

        # If all columns are empty for some reason, keep the original columns
        # so the table is still structurally valid.
        if non_empty_columns:
            working_df = working_df[non_empty_columns]

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Route Demand Sheet</title>
    <style>
        @media print {{
            @page {{
                size: letter landscape;
                margin: 0.3in;
            }}
            body {{
                margin: 0;
                padding: 0;
            }}
            .no-print {{
                display: none;
            }}
            /* Scale content to fit page */
            html {{
                width: 100%;
                height: 100%;
            }}
            body {{
                width: 100%;
                transform-origin: top left;
            }}
            /* Monochrome-friendly print styles */
            * {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .header {{
                margin-bottom: 10px !important;
                padding-bottom: 5px !important;
            }}
            .header h1 {{
                font-size: 18px !important;
            }}
            .header-info {{
                font-size: 11px !important;
            }}
            .filters {{
                background-color: white !important;
                border: 2px solid #000 !important;
                padding: 8px !important;
                margin-bottom: 10px !important;
                font-size: 11px !important;
            }}
            table {{
                width: 100% !important;
                table-layout: auto !important;
                font-size: 9px !important;
                page-break-inside: auto;
            }}
            th {{
                background-color: #e0e0e0 !important;
                color: #000 !important;
                border: 1px solid #000 !important;
                padding: 6px 4px !important;
                font-size: 9px !important;
            }}
            td {{
                padding: 4px !important;
                font-size: 9px !important;
                word-wrap: break-word;
            }}
            tr {{
                page-break-inside: avoid;
                page-break-after: auto;
            }}
            tr:nth-child(even) {{
                background-color: #f5f5f5 !important;
            }}
            .summary {{
                background-color: white !important;
                border: 2px solid #000 !important;
                border-left: 4px solid #000 !important;
                padding: 8px !important;
                margin-top: 10px !important;
                font-size: 11px !important;
            }}
        }}
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            color: #000;
        }}
        .header {{
            border-bottom: 3px solid #000;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            color: #000;
        }}
        .header-info {{
            margin-top: 10px;
            font-size: 14px;
            color: #000;
        }}
        .filters {{
            background-color: #f5f5f5;
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 5px;
            border: 2px solid #666;
        }}
        .filters strong {{
            margin-right: 10px;
            color: #000;
        }}
        table {{
            width: 100%;
            max-width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            border: 1px solid #000;
            table-layout: auto;
        }}
        th {{
            background-color: #e0e0e0;
            color: #000;
            padding: 10px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #000;
            word-wrap: break-word;
        }}
        td {{
            padding: 8px;
            border: 1px solid #666;
            border-bottom: 1px solid #666;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        tr:nth-child(even) {{
            background-color: #f5f5f5;
        }}
        tr:hover {{
            background-color: #f0f0f0;
        }}
        .summary {{
            margin-top: 20px;
            padding: 10px;
            background-color: white;
            border: 2px solid #000;
            border-left: 4px solid #000;
        }}
        .summary strong {{
            color: #000;
        }}
        .no-print {{
            margin-bottom: 20px;
            padding: 10px;
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="no-print">
        <strong>Print Instructions:</strong> Use your browser's print function (Ctrl+P or Cmd+P) to print this page.
    </div>
    
    <div class="header">
        <h1>Route Demand Sheet</h1>
        <div class="header-info">
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            Total Records: {len(df)}
        </div>
    </div>
    
    <div class="filters">
        <strong>Filters Applied:</strong>
        Service Day: {service_day} | 
        Service Tech: {service_tech} | 
        Cycle Frequency: {cycle_freq}
    </div>
    
    <table>
        <thead>
            <tr>
"""
        
        # Add table headers (only for columns that have data)
        for col in working_df.columns:
            html += f"                <th>{col}</th>\n"
        
        html += """            </tr>
        </thead>
        <tbody>
"""
        
        # Add table rows for the filtered, non-empty columns
        for idx, row in working_df.iterrows():
            html += "            <tr>\n"
            for val in row:
                display_val = str(val) if pd.notna(val) else ""
                html += f"                <td>{display_val}</td>\n"
            html += "            </tr>\n"
        
        html += """        </tbody>
    </table>
"""

        # Build a chemical pick summary based on numeric columns.
        # We treat any remaining numeric columns (after filtering out the
        # obvious non-chemical fields) as "chemicals" and total them.
        numeric_df = working_df.select_dtypes(include="number")

        # Try to drop obvious non-chemical numeric columns if they exist.
        non_chemical_candidates = [
            service_day_col,
            service_tech_col,
            cycle_freq_col,
        ]
        for col in non_chemical_candidates:
            if col is not None and col in numeric_df.columns:
                numeric_df = numeric_df.drop(columns=[col])

        if not numeric_df.empty and len(numeric_df.columns) > 0:
            totals = numeric_df.sum(numeric_only=True)
            html += '    <div class="summary">\n'
            html += '        <strong>Chemical Pick Summary:</strong><br>\n'
            for chem_name, total in totals.items():
                html += f"        {chem_name}: {total}<br>\n"
            html += "    </div>\n"

        html += "</body>\n</html>"
        
        return html


def main():
    root = tk.Tk()
    app = RouteViewerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

