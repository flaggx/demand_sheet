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


class RouteViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Route Viewer - Demand Sheet Generator")
        self.root.geometry("800x700")
        
        self.data = None
        self.filtered_data = None
        
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
        ttk.Label(main_frame, text="Excel File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_path = tk.StringVar()
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(0, weight=1)
        ttk.Entry(file_frame, textvariable=self.file_path, state="readonly").grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(file_frame, text="Browse", command=self.browse_file).grid(row=0, column=1)
        
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
        
        # Data preview
        preview_frame = ttk.LabelFrame(main_frame, text="Data Preview", padding="10")
        preview_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Treeview for data display
        tree_frame = ttk.Frame(preview_frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
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
            self.load_data(filename)
    
    def load_data(self, filepath):
        try:
            # Try to read Excel file
            self.data = pd.read_excel(filepath)
            
            # Update status
            self.status_var.set(f"Loaded {len(self.data)} records from {os.path.basename(filepath)}")
            
            # Update filter dropdowns
            self.update_filters()
            
            # Display data
            self.display_data(self.data)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load Excel file:\n{str(e)}")
            self.status_var.set("Error loading file")
    
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
        self.display_data(filtered)
        self.status_var.set(f"Showing {len(filtered)} of {len(self.data)} records")
    
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
            self.display_data(self.data)
            self.status_var.set(f"Showing all {len(self.data)} records")
    
    def display_data(self, df):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if df is None or df.empty:
            return
        
        # Set up columns
        columns = list(df.columns)
        self.tree['columns'] = columns
        self.tree['show'] = 'headings'
        
        # Configure columns
        for col in columns:
            self.tree.heading(col, text=str(col))
            self.tree.column(col, width=100, minwidth=50)
        
        # Insert data
        for idx, row in df.iterrows():
            values = [str(val) if pd.notna(val) else "" for val in row]
            self.tree.insert('', tk.END, values=values)
    
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
                margin: 0.5in;
            }}
            body {{
                margin: 0;
            }}
            .no-print {{
                display: none;
            }}
        }}
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            color: #333;
        }}
        .header {{
            border-bottom: 3px solid #333;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .header-info {{
            margin-top: 10px;
            font-size: 14px;
        }}
        .filters {{
            background-color: #f5f5f5;
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        .filters strong {{
            margin-right: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #333;
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f0f0f0;
        }}
        .summary {{
            margin-top: 20px;
            padding: 10px;
            background-color: #e8f4f8;
            border-left: 4px solid #2196F3;
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
    
    <div class="summary">
        <strong>Summary:</strong> {len(working_df)} route(s) displayed
    </div>
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

