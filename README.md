# Demand Sheet - Route Viewer

Desktop application for viewing and printing route data from Excel sheets. Filters routes by service day, service tech, and cycle frequency.

## Features

- Load Excel files (.xlsx, .xls) or Google Sheets URLs
- Save frequently-used files/URLs as favorites with custom names
- Filter routes by:
  - Service Day
  - Service Tech
  - Cycle Frequency (supports multi-select)
- Preview filtered routes in browser
- Generate printable HTML pages for selected routes (landscape, monochrome-friendly)
- Chemical pick summary automatically calculated
- Export routes to HTML files for printing

## Installation

**Supported:** Windows 10 and Windows 11.

1. Install Python 3.8 or later from https://www.python.org/downloads/
   - **Important**: Check "Add Python to PATH" during installation
2. Double-click `RouteViewer.bat` to run the application
   - First time setup will happen automatically (may take a few minutes)
   - After setup, the application window will open
3. That's it! Just double-click `RouteViewer.bat` whenever you want to use the app.

See `SETUP_WINDOWS.md` for detailed deployment and troubleshooting.

## Usage

1. Double-click `RouteViewer.bat` to start the app.
2. Load your data:
   - Click "Browse" to select an Excel file, OR
   - Paste a Google Sheets URL in the file field and click "Load"
   - You can save frequently-used files/URLs as favorites with custom names
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

After exporting, the HTML file will open in your default browser. Use your browser's print function (Ctrl+P) to print the route sheet.
