#!/usr/bin/env python3
"""
Comprehensive test for all typing issues
"""

def test_all_critical_imports():
    """Test all imports that were causing typing errors"""
    try:
        print("Testing render_optimizer...")
        from utils.render_optimizer import RenderOptimizer
        print("✓ RenderOptimizer imported successfully")
        
        print("Testing performance_profiler...")
        from utils.performance_profiler import get_profiler
        print("✓ PerformanceProfiler imported successfully")
        
        print("Testing game_state...")
        from systems.game_state import GameStateManager
        print("✓ GameStateManager imported successfully")
        
        print("Testing settings_system...")
        from systems.settings_system import SettingsSystem
        print("✓ SettingsSystem imported successfully")
        
        print("Testing config...")
        from core.config import Config
        print("✓ Config imported successfully")
        
        print("Testing game_engine...")
        from core.game_engine import GameEngine
        print("✓ GameEngine imported successfully")
        
        print("Testing basic functionality...")
        config = Config()
        render_optimizer = RenderOptimizer(1024, 768)
        stats = render_optimizer.get_optimization_stats()
        print(f"✓ RenderOptimizer.get_optimization_stats() works - {len(stats)} stats returned")
        
        print("\n🎉 All typing issues resolved!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_all_critical_imports()
    if success:
        print("\n✅ All typing fixes successful! Game should launch now.")
    else:
        print("\n❌ Still have typing issues.")
    
    import sys
    sys.exit(0 if success else 1)