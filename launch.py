"""
Metro Universe Strategy Game Launcher
Handles startup, error checking, and common issues
"""

import sys
import os
import logging
from pathlib import Path

def setup_logging():
    """Setup logging for the launcher"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "launcher.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def check_dependencies(logger):
    """Check if all required dependencies are available"""
    missing_deps = []
    
    try:
        import pygame
        logger.info(f"Pygame {pygame.version.ver} found")
    except ImportError:
        missing_deps.append("pygame")
    
    try:
        import numpy
        logger.info(f"NumPy {numpy.__version__} found")
    except ImportError:
        logger.warning("NumPy not found (optional dependency)")
    
    if missing_deps:
        logger.error(f"Missing required dependencies: {', '.join(missing_deps)}")
        logger.info("Run 'python setup.py' to install dependencies")
        return False
    
    return True

def check_game_files(logger):
    """Check if all required game files are present"""
    required_files = [
        "main.py",
        "core/config.py",
        "core/game_engine.py",
        "data/resources.py",
        "systems/game_state.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"Missing required game files: {', '.join(missing_files)}")
        return False
    
    logger.info("All required game files found")
    return True

def create_directories(logger):
    """Create necessary directories if they don't exist"""
    directories = [
        "saves",
        "logs",
        "audio/sfx",
        "audio/music"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")

def launch_game(logger):
    """Launch the main game"""
    try:
        logger.info("Starting Metro Universe Strategy Game...")
        
        # Import and run the main game
        from main import main
        main()
        
    except ImportError as e:
        logger.error(f"Failed to import main game module: {e}")
        return False
    except Exception as e:
        logger.error(f"Game crashed with error: {e}")
        logger.exception("Full traceback:")
        return False
    
    return True

def show_help():
    """Show help information"""
    help_text = """
Metro Universe Strategy Game Launcher

Usage:
  python launch.py          - Start the game
  python launch.py --help   - Show this help
  python launch.py --check  - Check installation

If you encounter issues:
1. Run 'python setup.py' to install dependencies
2. Check the logs/launcher.log file for error details
3. Ensure you have Python 3.8 or higher
4. Make sure all game files are present

For gameplay help, see README.md
"""
    print(help_text)

def check_installation(logger):
    """Check installation without launching the game"""
    logger.info("Checking installation...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error(f"Python 3.8+ required, found {sys.version}")
        return False
    
    logger.info(f"Python {sys.version} OK")
    
    # Check dependencies
    if not check_dependencies(logger):
        return False
    
    # Check game files
    if not check_game_files(logger):
        return False
    
    logger.info("Installation check passed!")
    return True

def main():
    """Main launcher function"""
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            show_help()
            return
        elif sys.argv[1] == "--check":
            logger = setup_logging()
            success = check_installation(logger)
            sys.exit(0 if success else 1)
    
    # Setup logging
    logger = setup_logging()
    
    try:
        logger.info("Metro Universe Strategy Game Launcher starting...")
        
        # Check installation
        if not check_installation(logger):
            logger.error("Installation check failed")
            logger.info("Run 'python setup.py' to fix installation issues")
            sys.exit(1)
        
        # Create directories
        create_directories(logger)
        
        # Launch game
        success = launch_game(logger)
        
        if success:
            logger.info("Game exited normally")
        else:
            logger.error("Game exited with errors")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
    except Exception as e:
        logger.error(f"Launcher error: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)

if __name__ == "__main__":
    main()