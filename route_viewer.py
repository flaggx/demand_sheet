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
        self.cycle_freq_combo = ttk.Combobox(filter_frame, textvariable=self.cycle_freq_var, state="readonly", width=30)
        self.cycle_freq_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # Bind filter changes
        self.service_day_var.trace('w', lambda *args: self.apply_filters())
        self.service_tech_var.trace('w', lambda *args: self.apply_filters())
        self.cycle_freq_var.trace('w', lambda *args: self.apply_filters())
        
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
        
        # Update Cycle Frequency
        if cycle_freq_col:
            values = ['All'] + sorted(self.data[cycle_freq_col].dropna().unique().tolist())
            self.cycle_freq_combo['values'] = values
        else:
            self.cycle_freq_combo['values'] = ['All']
    
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
        
        # Apply Cycle Frequency filter
        cycle_freq_col = self.find_column(['Cycle Frequency', 'cycle_frequency', 'CycleFrequency', 'Frequency', 'frequency', 'Cycle'])
        if cycle_freq_col and self.cycle_freq_var.get() != "All":
            filtered = filtered[filtered[cycle_freq_col] == self.cycle_freq_var.get()]
        
        self.filtered_data = filtered
        self.display_data(filtered)
        self.status_var.set(f"Showing {len(filtered)} of {len(self.data)} records")
    
    def clear_filters(self):
        self.service_day_var.set("All")
        self.service_tech_var.set("All")
        self.cycle_freq_var.set("All")
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
        # Get filter values for header
        service_day = self.service_day_var.get() if self.service_day_var.get() != "All" else "All Days"
        service_tech = self.service_tech_var.get() if self.service_tech_var.get() != "All" else "All Techs"
        cycle_freq = self.cycle_freq_var.get() if self.cycle_freq_var.get() != "All" else "All Frequencies"
        
        # Find column names
        service_day_col = self.find_column(['Service Day', 'service_day', 'ServiceDay', 'Day', 'day'])
        service_tech_col = self.find_column(['Service Tech', 'service_tech', 'ServiceTech', 'Tech', 'tech', 'Technician'])
        cycle_freq_col = self.find_column(['Cycle Frequency', 'cycle_frequency', 'CycleFrequency', 'Frequency', 'frequency', 'Cycle'])
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Route Demand Sheet</title>
    <style>
        @media print {{
            @page {{
                size: letter;
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
        
        # Add table headers
        for col in df.columns:
            html += f"                <th>{col}</th>\n"
        
        html += """            </tr>
        </thead>
        <tbody>
"""
        
        # Add table rows
        for idx, row in df.iterrows():
            html += "            <tr>\n"
            for val in row:
                display_val = str(val) if pd.notna(val) else ""
                html += f"                <td>{display_val}</td>\n"
            html += "            </tr>\n"
        
        html += """        </tbody>
    </table>
    
    <div class="summary">
        <strong>Summary:</strong> {len(df)} route(s) displayed
    </div>
</body>
</html>"""
        
        return html


def main():
    root = tk.Tk()
    app = RouteViewerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

