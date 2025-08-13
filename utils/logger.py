"""
Logging utilities
Centralized logging configuration for the game
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(
    name: str = "metro_game",
    level: int = logging.INFO,
    log_file: str = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up centralized logging for the game
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        console_output: Whether to output to console
        
    Returns:
        Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        # Default log file with timestamp
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_log_file = logs_dir / f"metro_game_{timestamp}.log"
        
        file_handler = logging.FileHandler(default_log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.info("Logging system initialized")
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance"""
    if name is None:
        name = "metro_game"
    return logging.getLogger(name)