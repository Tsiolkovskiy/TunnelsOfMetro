#!/usr/bin/env python3
"""
Simple Metro Universe Strategy Game launcher
Minimal version for testing
"""

import pygame
import sys
import logging

def main():
    """Main game entry point"""
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Metro Universe Strategy Game...")
        
        # Test imports
        from core.config import Config
        logger.info("✓ Config imported")
        
        from core.game_engine import GameEngine
        logger.info("✓ GameEngine imported")
        
        # Initialize Pygame
        pygame.init()
        logger.info("✓ Pygame initialized")
        
        # Load configuration
        config = Config()
        logger.info("✓ Configuration loaded")
        
        # Create and run game engine
        game = GameEngine(config)
        logger.info("✓ Game engine created")
        
        game.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        pygame.quit()
        logger.info("Game shutdown complete")

if __name__ == "__main__":
    main()