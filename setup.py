#!/usr/bin/env python3
"""
Setup script for Metro Universe Strategy Game
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("Installing requirements...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✓ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    dirs = ["logs", "saves"]
    
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✓ Created directory: {dir_name}")

def main():
    """Main setup function"""
    print("Metro Universe Strategy Game - Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8+ is required")
        sys.exit(1)
    
    print(f"✓ Python version: {sys.version}")
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Test setup
    print("\nTesting setup...")
    try:
        import pygame
        print(f"✓ Pygame version: {pygame.version.ver}")
    except ImportError:
        print("✗ Pygame import failed")
        sys.exit(1)
    
    print("\n✓ Setup complete! You can now run the game with:")
    print("  python main.py")
    print("  or")
    print("  run_game.bat (on Windows)")

if __name__ == "__main__":
    main()