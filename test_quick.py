#!/usr/bin/env python3
"""
Quick test to check basic functionality
"""

try:
    print("Testing basic imports...")
    
    # Test core imports
    from core.config import Config
    print("✓ Config imported")
    
    from systems.resource_production_system import ResourceProductionSystem
    print("✓ ResourceProductionSystem imported")
    
    from data.resources import ResourcePool
    print("✓ ResourcePool imported")
    
    # Test basic functionality
    config = Config()
    print("✓ Config created")
    
    resources = ResourcePool()
    print(f"✓ ResourcePool created with {resources.food} food")
    
    print("\n🎉 Basic functionality test passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()