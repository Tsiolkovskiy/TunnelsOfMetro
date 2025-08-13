#!/usr/bin/env python3
"""
Final test to verify all fixes are working
"""

import sys

def test_all_imports():
    """Test all critical imports"""
    try:
        print("Testing core imports...")
        from core.config import Config
        from core.game_engine import GameEngine
        print("✓ Core imports successful")
        
        print("Testing game state...")
        from systems.game_state import GameStateManager
        from utils.map_loader import MapLoader
        
        # Test the specific method that was failing
        map_loader = MapLoader()
        metro_map = map_loader.load_default_map()
        game_state = GameStateManager(metro_map)
        
        # This was the line causing the error
        visible_stations = game_state.get_visible_stations()
        print(f"✓ get_visible_stations() works - {len(visible_stations)} stations visible")
        
        print("Testing basic game creation...")
        config = Config()
        game = GameEngine(config)
        print("✓ Game engine created successfully")
        
        print("\n🎉 All tests passed! The game should now launch successfully.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_all_imports()
    if success:
        print("\n✅ Ready to launch! Try running:")
        print("   python main.py")
        print("   or")
        print("   python main_simple.py")
    else:
        print("\n❌ Still have issues. Check the error above.")
    
    sys.exit(0 if success else 1)