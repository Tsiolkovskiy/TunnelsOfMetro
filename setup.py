"""
Setup script for Metro Universe Strategy Game
Handles installation and dependency management
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True

def install_dependencies():
    """Install required dependencies"""
    dependencies = [
        "pygame>=2.0.0",
        "numpy>=1.19.0"
    ]
    
    print("Installing dependencies...")
    
    for dep in dependencies:
        try:
            print(f"Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✓ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {dep}: {e}")
            return False
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        "saves",
        "audio/sfx",
        "audio/music",
        "logs"
    ]
    
    print("Creating directories...")
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def verify_installation():
    """Verify that all components are working"""
    print("Verifying installation...")
    
    try:
        import pygame
        print(f"✓ Pygame {pygame.version.ver} is available")
    except ImportError:
        print("✗ Pygame is not available")
        return False
    
    try:
        import numpy
        print(f"✓ NumPy {numpy.__version__} is available")
    except ImportError:
        print("⚠ NumPy is not available (optional)")
    
    # Check if main game file exists
    if Path("main.py").exists():
        print("✓ Main game file found")
    else:
        print("✗ Main game file not found")
        return False
    
    return True

def main():
    """Main setup function"""
    print("=" * 50)
    print("Metro Universe Strategy Game - Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("\nSetup failed during dependency installation")
        return False
    
    # Create directories
    create_directories()
    
    # Verify installation
    if not verify_installation():
        print("\nSetup completed with warnings")
        return False
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("=" * 50)
    print("\nTo start the game, run:")
    print("  python main.py")
    print("\nFor help and controls, see README.md")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)