# Demand Sheet - Route Viewer

Desktop application for viewing and printing route data from Excel sheets. Filters routes by service day, service tech, and cycle frequency.

## Features

- Load Excel files (.xlsx, .xls)
- Filter routes by:
  - Service Day
  - Service Tech
  - Cycle Frequency
- Preview filtered routes in a data table
- Generate printable HTML pages for selected routes
- Export routes to HTML files for printing

## Installation

1. Install Python 3.8 or higher
2. Install system dependencies for tkinter (GUI library):
   - **Arch Linux**: `sudo pacman -S tk`
   - **Ubuntu/Debian**: `sudo apt-get install python3-tk`
   - **Fedora**: `sudo dnf install python3-tkinter`
   - **macOS**: Usually pre-installed with Python
   - **Windows**: Usually pre-installed with Python
3. Create a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   ```
3. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # On Linux/Mac
   # or
   venv\Scripts\activate     # On Windows
   ```
4. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Activate the virtual environment (if not already activated):
   ```bash
   source venv/bin/activate
   ```

2. Run the application:
   ```bash
   python route_viewer.py
   ```
   
   Or use the launcher script:
   ```bash
   ./run.sh
   ```
   
   Or use the virtual environment's Python directly:
   ```bash
   ./venv/bin/python route_viewer.py
   ```

2. Click "Browse" to select an Excel file containing route data

3. The application will automatically detect columns for:
   - Service Day (looks for: "Service Day", "service_day", "ServiceDay", "Day", "day")
   - Service Tech (looks for: "Service Tech", "service_tech", "ServiceTech", "Tech", "tech", "Technician")
   - Cycle Frequency (looks for: "Cycle Frequency", "cycle_frequency", "CycleFrequency", "Frequency", "frequency", "Cycle")

4. Use the filter dropdowns to select specific values or "All" to show everything

5. Click "Preview Route" to see the filtered data in your browser

6. Click "Print/Export" to save a printable HTML file and open it in your browser for printing

## Excel File Format

Your Excel file should contain columns with route information. The application will automatically detect columns with names like:
- Service Day / Day
- Service Tech / Tech / Technician
- Cycle Frequency / Frequency / Cycle

Any other columns will be displayed in the preview and printed output.

## Printing

After exporting, the HTML file will open in your default browser. Use your browser's print function (Ctrl+P or Cmd+P) to print the route sheet.
