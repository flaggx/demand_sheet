# Windows Deployment Guide

## Quick Start for End Users

### Option 1: Simple Double-Click (Recommended)

1. **Install Python** (if not already installed):
   - Download Python 3.8 or later from https://www.python.org/downloads/
   - During installation, **check the box** "Add Python to PATH"
   - Click "Install Now"

2. **Run the Application**:
   - Double-click `RouteViewer.bat`
   - The first time, it will set up everything automatically (may take a few minutes)
   - After setup, the application window will open

3. **That's it!** Just double-click `RouteViewer.bat` whenever you want to use the app.

---

## What the Batch File Does

The `RouteViewer.bat` file automatically:
- ✅ Checks if Python is installed
- ✅ Creates a virtual environment (first time only)
- ✅ Installs all required dependencies
- ✅ Launches the application

**No technical knowledge required!** Just double-click and use.

---

## Troubleshooting

### "Python is not installed or not in PATH"
- Install Python from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation
- Restart your computer after installing Python

### "Failed to install dependencies"
- Check your internet connection
- Try running `RouteViewer.bat` again
- Make sure Windows Firewall isn't blocking Python

### Application won't start
- Make sure you have Python 3.8 or later installed
- Try running `RouteViewer.bat` from Command Prompt to see error messages
- Check that all files are in the same folder

---

## For IT Administrators

### Silent Installation
You can deploy this application by:
1. Copying the entire folder to the target location
2. Ensuring Python 3.8+ is installed system-wide
3. Users can then run `RouteViewer.bat` directly

### Network Deployment
- The application stores user favorites in `%USERPROFILE%\.demand_sheet_favorites.json`
- Each user will have their own favorites
- No shared configuration files needed

### Requirements
- Windows 7 or later
- Python 3.8 or later
- Internet connection (for first-time dependency installation)

---

## Files Included

- `RouteViewer.bat` - Main launcher (double-click this!)
- `route_viewer.py` - Application code
- `requirements.txt` - Python dependencies
- `SETUP_WINDOWS.md` - This file

---

## Support

If you encounter issues:
1. Check that Python is installed: Open Command Prompt and type `python --version`
2. Make sure all files are in the same folder
3. Try running `RouteViewer.bat` from Command Prompt to see detailed error messages

