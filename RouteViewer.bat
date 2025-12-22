@echo off
REM Route Viewer - Demand Sheet Generator
REM This batch file automatically sets up and runs the application

setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ========================================
echo Route Viewer - Demand Sheet Generator
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.8 or later from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [2/4] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo [2/4] Virtual environment already exists.
)
echo.

REM Activate virtual environment
echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)
echo.

REM Upgrade pip
python -m pip install --upgrade pip --quiet

REM Install/update dependencies
echo [4/4] Installing dependencies...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    echo.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)
echo Dependencies installed successfully.
echo.

REM Run the application
echo ========================================
echo Starting Route Viewer...
echo ========================================
echo.
python route_viewer.py

REM If the application exits, pause so user can see any error messages
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)

endlocal

