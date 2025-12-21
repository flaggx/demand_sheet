#!/bin/bash
# Launcher script for Route Viewer application

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the application
python3 route_viewer.py

