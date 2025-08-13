#!/usr/bin/env python3
"""
Metro Universe Strategy Game
Main entry point for the game
"""

import pygame
import sys
import logging
from pathlib import Path

# Import game modules
from core.game_engine import GameEngine
from core.config import Config
from utils.logger import setup_logger


def main():
    """Main game entry point"""
    # Setup logging
    logger = setup_logger()
    logger.info("Starting Metro Universe Strategy Game")
    
    try:
        # Initialize Pygame
        pygame.init()
        logger.info("Pygame initialized successfully")
        
        # Load configuration
        config = Config()
        logger.info("Configuration loaded")
        
        # Create and run game engine
        game = GameEngine(config)
        game.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        pygame.quit()
        logger.info("Game shutdown complete")


if __name__ == "__main__":
    main()