"""
Game Configuration
Centralized configuration management for game settings and constants
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any


class Config:
    """Game configuration manager"""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration"""
        self.logger = logging.getLogger(__name__)
        self.config_file = Path(config_file)
        
        # Default configuration values
        self._defaults = {
            # Display settings
            "SCREEN_WIDTH": 800,
            "SCREEN_HEIGHT": 600,
            "TARGET_FPS": 30,
            "GAME_TITLE": "Metro Universe Strategy Game",
            
            # Game settings
            "INITIAL_RESOURCES": {
                "food": 100,
                "clean_water": 50,
                "scrap": 75,
                "medicine": 25,
                "mgr_rounds": 50
            },
            
            # UI Colors (RGB tuples)
            "COLORS": {
                "BLACK": (0, 0, 0),
                "WHITE": (255, 255, 255),
                "RED": (255, 0, 0),
                "GREEN": (0, 255, 0),
                "BLUE": (0, 0, 255),
                "GRAY": (128, 128, 128),
                "DARK_GRAY": (64, 64, 64),
                "YELLOW": (255, 255, 0),
                "ORANGE": (255, 165, 0)
            },
            
            # Gameplay constants
            "SCOUT_FUEL_COST": 10,
            "ATTACK_AMMO_COST": 50,
            "TRADE_AMMO_COST": 20,
            "TRADE_FOOD_GAIN": 10,
            "ATTACK_SUCCESS_CHANCE": 0.5,
            
            # Map settings
            "STATION_RADIUS": 10,
            "STATION_NAME_OFFSET": 15,
            "TUNNEL_WIDTH": 2
        }
        
        # Load configuration
        self._load_config()
        
    def _load_config(self):
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    
                # Merge with defaults
                self._config = self._defaults.copy()
                self._config.update(user_config)
                
                self.logger.info(f"Configuration loaded from {self.config_file}")
                
            except Exception as e:
                self.logger.warning(f"Failed to load config file: {e}. Using defaults.")
                self._config = self._defaults.copy()
        else:
            self.logger.info("No config file found. Using defaults.")
            self._config = self._defaults.copy()
            self._save_config()
            
    def _save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save config file: {e}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self._config[key] = value
        
    def save(self):
        """Save configuration to file"""
        self._save_config()
        
    # Property accessors for common values
    @property
    def SCREEN_WIDTH(self) -> int:
        return self._config["SCREEN_WIDTH"]
        
    @property
    def SCREEN_HEIGHT(self) -> int:
        return self._config["SCREEN_HEIGHT"]
        
    @property
    def TARGET_FPS(self) -> int:
        return self._config["TARGET_FPS"]
        
    @property
    def GAME_TITLE(self) -> str:
        return self._config["GAME_TITLE"]
        
    @property
    def COLORS(self) -> Dict[str, tuple]:
        return self._config["COLORS"]
        
    @property
    def INITIAL_RESOURCES(self) -> Dict[str, int]:
        return self._config["INITIAL_RESOURCES"]