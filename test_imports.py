#!/usr/bin/env python3
"""
Test script to check if all imports work correctly
"""

import sys
from pathlib import Path

def test_imports():
    """Test all major imports"""
    try:
        print("Testing core imports...")
        from core.config import Config
        from core.game_engine import GameEngine
        print("✓ Core imports successful")
        
        print("Testing data imports...")
        from data.resources import ResourcePool
        from data.station import Station
        from data.faction import Faction
        from data.military_unit import MilitaryManager
        print("✓ Data imports successful")
        
        print("Testing system imports...")
        from systems.game_state import GameStateManager
        from systems.resource_production_system import ResourceProductionSystem
        from systems.metro_map import MetroMap
        print("✓ System imports successful")
        
        print("Testing utility imports...")
        from utils.logger import setup_logger
        from utils.map_loader import MapLoader
        print("✓ Utility imports successful")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)