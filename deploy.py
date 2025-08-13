"""
Deployment Script for Metro Universe Strategy Game
Creates distribution packages and performs final checks
"""

import os
import sys
import shutil
import zipfile
import logging
from pathlib import Path
from datetime import datetime

def setup_logging():
    """Setup logging for deployment"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def create_distribution_directory(logger):
    """Create distribution directory structure"""
    dist_dir = Path("dist")
    
    # Clean existing distribution
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        logger.info("Cleaned existing distribution directory")
    
    # Create new distribution structure
    dist_dir.mkdir()
    game_dir = dist_dir / "metro_strategy_game"
    game_dir.mkdir()
    
    logger.info("Created distribution directory structure")
    return game_dir

def copy_game_files(game_dir, logger):
    """Copy game files to distribution directory"""
    # Files and directories to include
    include_files = [
        "main.py",
        "launch.py",
        "setup.py",
        "requirements.txt",
        "README.md",
        "USER_GUIDE.md"
    ]
    
    include_dirs = [
        "core",
        "data", 
        "systems",
        "ui",
        "utils",
        "tests"
    ]
    
    # Copy files
    for file_name in include_files:
        src = Path(file_name)
        if src.exists():
            shutil.copy2(src, game_dir / file_name)
            logger.info(f"Copied {file_name}")
        else:
            logger.warning(f"File not found: {file_name}")
    
    # Copy directories
    for dir_name in include_dirs:
        src_dir = Path(dir_name)
        if src_dir.exists():
            shutil.copytree(src_dir, game_dir / dir_name)
            logger.info(f"Copied directory {dir_name}")
        else:
            logger.warning(f"Directory not found: {dir_name}")
    
    # Create empty directories for runtime
    runtime_dirs = ["saves", "logs", "audio/sfx", "audio/music"]
    for dir_path in runtime_dirs:
        (game_dir / dir_path).mkdir(parents=True, exist_ok=True)
        # Create .gitkeep files to preserve empty directories
        (game_dir / dir_path / ".gitkeep").touch()
    
    logger.info("Created runtime directories")

def run_tests(game_dir, logger):
    """Run tests on the distribution"""
    logger.info("Running tests on distribution...")
    
    # Change to distribution directory
    original_cwd = os.getcwd()
    os.chdir(game_dir)
    
    try:
        # Run integration tests
        import subprocess
        result = subprocess.run([sys.executable, "test_integration.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✓ Integration tests passed")
            return True
        else:
            logger.error("✗ Integration tests failed")
            logger.error(result.stdout)
            logger.error(result.stderr)
            return False
    
    except Exception as e:
        logger.error(f"Failed to run tests: {e}")
        return False
    
    finally:
        os.chdir(original_cwd)

def create_zip_package(dist_dir, logger):
    """Create ZIP package for distribution"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"metro_strategy_game_v1.0_{timestamp}.zip"
    zip_path = dist_dir / zip_name
    
    logger.info(f"Creating ZIP package: {zip_name}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        game_dir = dist_dir / "metro_strategy_game"
        
        for root, dirs, files in os.walk(game_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(dist_dir)
                zipf.write(file_path, arc_path)
    
    logger.info(f"ZIP package created: {zip_path}")
    return zip_path

def create_installer_script(game_dir, logger):
    """Create installer script for the distribution"""
    installer_content = '''#!/usr/bin/env python3
"""
Metro Universe Strategy Game Installer
Automated installation script
"""

import sys
import subprocess
import os
from pathlib import Path

def main():
    print("=" * 50)
    print("Metro Universe Strategy Game Installer")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"Error: Python 3.8+ required, found {sys.version}")
        return False
    
    print(f"Python {sys.version} - OK")
    
    # Run setup
    try:
        print("Running setup...")
        result = subprocess.run([sys.executable, "setup.py"], check=True)
        print("Setup completed successfully!")
    except subprocess.CalledProcessError:
        print("Setup failed!")
        return False
    
    # Instructions
    print("\\n" + "=" * 50)
    print("Installation Complete!")
    print("=" * 50)
    print("To start the game:")
    print("  python launch.py")
    print("\\nFor help:")
    print("  See README.md and USER_GUIDE.md")
    print("\\nEnjoy the game!")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
'''
    
    installer_path = game_dir / "install.py"
    with open(installer_path, 'w') as f:
        f.write(installer_content)
    
    logger.info("Created installer script")

def generate_deployment_info(game_dir, logger):
    """Generate deployment information file"""
    info_content = f"""Metro Universe Strategy Game - Deployment Information

Version: 1.0.0
Build Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Python Version: {sys.version}

Installation Instructions:
1. Extract all files to a directory
2. Run: python install.py
3. Start game: python launch.py

System Requirements:
- Python 3.8 or higher
- Pygame 2.0 or higher
- NumPy (optional, for enhanced audio)
- 100 MB free disk space
- 512 MB RAM minimum

Files Included:
- Game source code and assets
- Documentation (README.md, USER_GUIDE.md)
- Setup and launcher scripts
- Integration tests
- Example save directory structure

Support:
- Check README.md for basic help
- See USER_GUIDE.md for detailed gameplay information
- Run test_integration.py to verify installation
- Check logs/launcher.log for error details

Enjoy playing Metro Universe Strategy Game!
"""
    
    info_path = game_dir / "DEPLOYMENT_INFO.txt"
    with open(info_path, 'w') as f:
        f.write(info_content)
    
    logger.info("Generated deployment information")

def main():
    """Main deployment function"""
    logger = setup_logging()
    
    logger.info("Starting deployment process...")
    
    try:
        # Create distribution directory
        game_dir = create_distribution_directory(logger)
        
        # Copy game files
        copy_game_files(game_dir, logger)
        
        # Create installer script
        create_installer_script(game_dir, logger)
        
        # Generate deployment info
        generate_deployment_info(game_dir, logger)
        
        # Run tests on distribution
        if not run_tests(game_dir, logger):
            logger.error("Tests failed - deployment aborted")
            return False
        
        # Create ZIP package
        zip_path = create_zip_package(game_dir.parent, logger)
        
        logger.info("=" * 60)
        logger.info("Deployment completed successfully!")
        logger.info("=" * 60)
        logger.info(f"Distribution directory: {game_dir}")
        logger.info(f"ZIP package: {zip_path}")
        logger.info("Ready for distribution!")
        
        return True
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)