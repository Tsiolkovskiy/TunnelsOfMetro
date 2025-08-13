#!/usr/bin/env python3
"""
Test to verify typing imports are fixed
"""

try:
    print("Testing game_state import...")
    from systems.game_state import GameStateManager
    print("✓ GameStateManager imported successfully")
    
    print("Testing basic game initialization...")
    from utils.map_loader import MapLoader
    
    # Load map
    map_loader = MapLoader()
    metro_map = map_loader.load_default_map()
    print("✓ Metro map loaded")
    
    # Create game state
    game_state = GameStateManager(metro_map)
    print("✓ GameStateManager created")
    
    # Test the method that was causing the error
    visible_stations = game_state.get_visible_stations()
    print(f"✓ get_visible_stations() works - found {len(visible_stations)} visible stations")
    
    print("\n🎉 Typing fix successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()