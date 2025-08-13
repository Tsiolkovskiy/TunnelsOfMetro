@echo off
echo Starting Metro Universe Strategy Game (Simple Version)...

REM Try different Python commands
if exist "%~dp0\.venv\Scripts\python.exe" (
    echo Using virtual environment Python...
    "%~dp0\.venv\Scripts\python.exe" main_simple.py
) else if exist "python.exe" (
    echo Using system Python...
    python.exe main_simple.py
) else (
    echo Using py launcher...
    py main_simple.py
)

pause