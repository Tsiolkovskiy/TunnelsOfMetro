#!/usr/bin/env python3
"""
Test for circular import issues
"""

try:
    print("Testing ResourceProductionSystem import...")
    from systems.resource_production_system import ResourceProductionSystem
    print("✓ ResourceProductionSystem imported successfully")
    
    print("Testing GameStateManager import...")
    from systems.game_state import GameStateManager
    print("✓ GameStateManager imported successfully")
    
    print("Testing SaveSystem import...")
    from systems.save_system import SaveSystem
    print("✓ SaveSystem imported successfully")
    
    print("Testing LoadSystem import...")
    from systems.load_system import LoadSystem
    print("✓ LoadSystem imported successfully")
    
    print("\n🎉 All imports successful - no circular import issues!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()