#!/usr/bin/env python3
"""
Complete launch test - simulates the full game startup process
"""

import sys
import pygame

def test_complete_startup():
    """Test the complete game startup process"""
    try:
        print("🚀 Testing complete game startup process...")
        print()
        
        # Step 1: Test all critical imports
        print("1️⃣ Testing imports...")
        from core.config import Config
        from core.game_engine import GameEngine
        from utils.logger import setup_logger
        print("   ✓ All imports successful")
        
        # Step 2: Test pygame initialization
        print("2️⃣ Testing Pygame initialization...")
        pygame.init()
        print("   ✓ Pygame initialized")
        
        # Step 3: Test configuration
        print("3️⃣ Testing configuration...")
        config = Config()
        print("   ✓ Configuration loaded")
        
        # Step 4: Test logger setup
        print("4️⃣ Testing logger setup...")
        logger = setup_logger()
        print("   ✓ Logger initialized")
        
        # Step 5: Test game engine creation (but don't run)
        print("5️⃣ Testing game engine creation...")
        game = GameEngine(config)
        print("   ✓ Game engine created")
        
        # Step 6: Test that all systems are initialized
        print("6️⃣ Testing system initialization...")
        assert game.metro_map is not None, "Metro map not initialized"
        assert game.game_state is not None, "Game state not initialized"
        assert game.settings_system is not None, "Settings system not initialized"
        assert game.audio_system is not None, "Audio system not initialized"
        assert game.visual_effects is not None, "Visual effects not initialized"
        assert game.render_optimizer is not None, "Render optimizer not initialized"
        print("   ✓ All systems initialized")
        
        # Step 7: Test basic functionality
        print("7️⃣ Testing basic functionality...")
        game_state_data = game.game_state.get_game_state()
        assert isinstance(game_state_data, dict), "Game state should return dict"
        assert "current_turn" in game_state_data, "Game state missing turn info"
        print("   ✓ Basic functionality working")
        
        # Step 8: Cleanup
        print("8️⃣ Testing cleanup...")
        game.shutdown()
        pygame.quit()
        print("   ✓ Cleanup successful")
        
        print()
        print("🎉 COMPLETE SUCCESS! The game is ready to launch!")
        print()
        print("✅ You can now run the game with:")
        print("   python main.py")
        print("   or")
        print("   python main_simple.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during startup test: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("💡 Try running the individual test scripts to isolate the issue:")
        print("   python test_all_typing.py")
        print("   python fix_all_typing.py")
        return False

if __name__ == "__main__":
    success = test_complete_startup()
    sys.exit(0 if success else 1)