"""
Integration Test Suite for Metro Universe Strategy Game
Tests complete game functionality and system integration
"""

import sys
import os
import logging
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

def setup_test_logging():
    """Setup logging for integration tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_imports():
    """Test that all major modules can be imported"""
    logger = logging.getLogger(__name__)
    logger.info("Testing module imports...")
    
    try:
        # Core modules
        from core.config import Config
        from core.game_engine import GameEngine
        logger.info("✓ Core modules imported successfully")
        
        # Data modules
        from data.resources import ResourcePool
        from data.station import Station
        from data.faction import Faction, GovernmentType, Ideology
        from data.military_unit import MilitaryManager
        logger.info("✓ Data modules imported successfully")
        
        # System modules
        from systems.game_state import GameStateManager
        from systems.metro_map import MetroMap
        from systems.diplomacy_system import DiplomacySystem
        from systems.trade_system import TradeSystem
        from systems.combat_system import CombatSystem
        from systems.victory_system import VictorySystem
        from systems.ai_system import AISystem
        from systems.audio_system import AudioSystem
        from systems.visual_effects import VisualEffectsSystem
        logger.info("✓ System modules imported successfully")
        
        # UI modules
        from ui.hud import HUD
        from ui.map_view import MapView
        from ui.message_system import MessageSystem
        logger.info("✓ UI modules imported successfully")
        
        # Utility modules
        from utils.map_loader import MapLoader
        from utils.performance_profiler import PerformanceProfiler
        from utils.render_optimizer import RenderOptimizer
        logger.info("✓ Utility modules imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False

def test_game_initialization():
    """Test game initialization without starting the main loop"""
    logger = logging.getLogger(__name__)
    logger.info("Testing game initialization...")
    
    try:
        from core.config import Config
        from core.game_engine import GameEngine
        
        # Create config
        config = Config()
        logger.info("✓ Config created successfully")
        
        # Initialize game engine (but don't run)
        game = GameEngine(config)
        logger.info("✓ Game engine initialized successfully")
        
        # Check that all systems are initialized
        assert game.metro_map is not None, "Metro map not initialized"
        assert game.game_state is not None, "Game state not initialized"
        assert game.settings_system is not None, "Settings system not initialized"
        assert game.audio_system is not None, "Audio system not initialized"
        assert game.visual_effects is not None, "Visual effects not initialized"
        
        logger.info("✓ All game systems initialized successfully")
        
        # Test shutdown
        game.shutdown()
        logger.info("✓ Game shutdown successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Game initialization failed: {e}")
        return False

def test_resource_system():
    """Test resource management system"""
    logger = logging.getLogger(__name__)
    logger.info("Testing resource system...")
    
    try:
        from data.resources import ResourcePool, MGRScarcitySystem, ResourceGenerationSystem
        
        # Test ResourcePool
        resources = ResourcePool()
        assert resources.food == 50, f"Expected 50 food, got {resources.food}"
        assert resources.add("food", 10), "Failed to add food"
        assert resources.food == 60, f"Expected 60 food after adding 10, got {resources.food}"
        assert resources.subtract("food", 5), "Failed to subtract food"
        assert resources.food == 55, f"Expected 55 food after subtracting 5, got {resources.food}"
        
        # Test resource requirements
        requirements = {"food": 10, "scrap": 5}
        assert resources.has_resources(requirements), "Should have sufficient resources"
        
        logger.info("✓ ResourcePool working correctly")
        
        # Test MGR scarcity system
        mgr_system = MGRScarcitySystem()
        price = mgr_system.calculate_mgr_price("Test Station", 5)
        assert price > 0, "MGR price should be positive"
        
        logger.info("✓ MGR scarcity system working correctly")
        
        # Test resource generation
        gen_system = ResourceGenerationSystem()
        generation = gen_system.calculate_generation(100, ["mushroom_farm"], 1.0)
        assert generation["food"] > 0, "Should generate food with mushroom farm"
        
        logger.info("✓ Resource generation system working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Resource system test failed: {e}")
        return False

def test_faction_system():
    """Test faction system"""
    logger = logging.getLogger(__name__)
    logger.info("Testing faction system...")
    
    try:
        from data.faction import Faction, FactionManager, GovernmentType, Ideology
        
        # Test individual faction
        faction = Faction("Test Faction", GovernmentType.REPUBLIC, Ideology.DEMOCRATIC)
        assert faction.name == "Test Faction", "Faction name not set correctly"
        assert faction.government == GovernmentType.REPUBLIC, "Government type not set correctly"
        assert faction.ideology == Ideology.DEMOCRATIC, "Ideology not set correctly"
        
        logger.info("✓ Individual faction creation working")
        
        # Test faction manager
        manager = FactionManager()
        assert len(manager.factions) > 0, "No factions created by manager"
        
        red_line = manager.get_faction("Red Line")
        assert red_line is not None, "Red Line faction not found"
        assert red_line.government == GovernmentType.COMMUNIST, "Red Line should be communist"
        
        logger.info("✓ Faction manager working correctly")
        
        # Test faction mechanics
        game_state = {"controlled_stations": ["Test Station"], "statistics": {}}
        red_line.process_turn(1, game_state)
        
        logger.info("✓ Faction mechanics processing correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Faction system test failed: {e}")
        return False

def test_game_systems_integration():
    """Test integration between game systems"""
    logger = logging.getLogger(__name__)
    logger.info("Testing game systems integration...")
    
    try:
        from utils.map_loader import MapLoader
        from systems.game_state import GameStateManager
        
        # Load map
        map_loader = MapLoader()
        metro_map = map_loader.load_default_map()
        assert len(metro_map.stations) > 0, "No stations loaded"
        
        logger.info("✓ Map loading working")
        
        # Initialize game state
        game_state = GameStateManager(metro_map)
        assert game_state.metro_map is not None, "Metro map not set in game state"
        assert game_state.player is not None, "Player not initialized"
        
        logger.info("✓ Game state initialization working")
        
        # Test turn processing
        initial_turn = game_state.current_turn
        game_state.advance_turn()
        assert game_state.current_turn == initial_turn + 1, "Turn not advanced correctly"
        
        logger.info("✓ Turn processing working")
        
        # Test victory system
        victory_status = game_state.get_victory_status()
        assert "game_ended" in victory_status, "Victory status missing game_ended field"
        assert not victory_status["game_ended"], "Game should not be ended initially"
        
        logger.info("✓ Victory system integration working")
        
        # Test AI system
        ai_info = game_state.get_ai_statistics()
        assert "ai_factions" in ai_info, "AI statistics missing ai_factions field"
        
        logger.info("✓ AI system integration working")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Game systems integration test failed: {e}")
        return False

def test_save_load_system():
    """Test save/load functionality"""
    logger = logging.getLogger(__name__)
    logger.info("Testing save/load system...")
    
    try:
        from utils.map_loader import MapLoader
        from systems.game_state import GameStateManager
        
        # Create game state
        map_loader = MapLoader()
        metro_map = map_loader.load_default_map()
        game_state = GameStateManager(metro_map)
        
        # Advance a few turns to create some state
        for _ in range(3):
            game_state.advance_turn()
        
        original_turn = game_state.current_turn
        original_resources = game_state.player.resources.to_dict()
        
        # Test save
        save_result = game_state.save_game("integration_test", "Integration test save")
        assert save_result["success"], f"Save failed: {save_result['message']}"
        
        logger.info("✓ Save functionality working")
        
        # Modify state
        game_state.advance_turn()
        game_state.player.resources.add("food", 100)
        
        # Test load
        load_result = game_state.load_game("integration_test")
        assert load_result["success"], f"Load failed: {load_result['message']}"
        
        # Verify state restored
        assert game_state.current_turn == original_turn, "Turn not restored correctly"
        
        logger.info("✓ Load functionality working")
        
        # Clean up test save
        delete_result = game_state.delete_save("integration_test")
        assert delete_result["success"], "Failed to clean up test save"
        
        logger.info("✓ Save/load system working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Save/load system test failed: {e}")
        return False

def test_performance_systems():
    """Test performance monitoring and optimization"""
    logger = logging.getLogger(__name__)
    logger.info("Testing performance systems...")
    
    try:
        from utils.performance_profiler import PerformanceProfiler, ProfileCategory
        from utils.render_optimizer import RenderOptimizer
        
        # Test performance profiler
        profiler = PerformanceProfiler()
        profiler.start_frame()
        
        with profiler.time_operation(ProfileCategory.GAME_LOGIC, "test_operation"):
            # Simulate some work
            sum(range(1000))
        
        fps = profiler.get_current_fps()
        assert fps >= 0, "FPS should be non-negative"
        
        logger.info("✓ Performance profiler working")
        
        # Test render optimizer
        optimizer = RenderOptimizer(1024, 768)
        stats = optimizer.get_optimization_stats()
        assert "total_render_commands" in stats, "Render stats missing commands field"
        
        logger.info("✓ Render optimizer working")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Performance systems test failed: {e}")
        return False

def run_all_tests():
    """Run all integration tests"""
    logger = setup_test_logging()
    
    tests = [
        ("Module Imports", test_imports),
        ("Game Initialization", test_game_initialization),
        ("Resource System", test_resource_system),
        ("Faction System", test_faction_system),
        ("Game Systems Integration", test_game_systems_integration),
        ("Save/Load System", test_save_load_system),
        ("Performance Systems", test_performance_systems)
    ]
    
    logger.info("=" * 60)
    logger.info("Metro Universe Strategy Game - Integration Tests")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        logger.info("-" * 40)
        
        try:
            if test_func():
                logger.info(f"✓ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"✗ {test_name} FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} CRASHED: {e}")
            failed += 1
    
    logger.info("\n" + "=" * 60)
    logger.info("Integration Test Results")
    logger.info("=" * 60)
    logger.info(f"Tests Passed: {passed}")
    logger.info(f"Tests Failed: {failed}")
    logger.info(f"Total Tests: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All integration tests passed!")
        return True
    else:
        logger.error(f"❌ {failed} integration tests failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)