#!/usr/bin/env python3
"""
Simple test script to verify the project setup
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing project setup...")
    
    # Test Python version
    print(f"Python version: {sys.version}")
    
    # Test pygame import
    try:
        import pygame
        print(f"✓ Pygame available: {pygame.version.ver}")
    except ImportError as e:
        print(f"✗ Pygame not available: {e}")
        return False
    
    # Test project structure
    required_dirs = ['core', 'systems', 'data', 'ui', 'utils']
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✓ Directory exists: {dir_name}")
        else:
            print(f"✗ Directory missing: {dir_name}")
            return False
    
    # Test core modules
    try:
        from core.config import Config
        print("✓ Config module imported successfully")
        
        from utils.logger import setup_logger
        print("✓ Logger module imported successfully")
        
        config = Config()
        print(f"✓ Config initialized - Screen: {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
        
        logger = setup_logger()
        logger.info("✓ Logger test successful")
        
    except Exception as e:
        print(f"✗ Module import failed: {e}")
        return False
    
    print("\n✓ All tests passed! Project setup is complete.")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)