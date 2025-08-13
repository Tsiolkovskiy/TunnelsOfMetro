@echo off
echo Starting Metro Universe Strategy Game...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

REM Check if pygame is installed
python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo Pygame is not installed. Installing...
    pip install pygame
    if errorlevel 1 (
        echo Failed to install pygame. Please install manually:
        echo pip install pygame
        pause
        exit /b 1
    )
)

REM Run the game
python main.py

pause