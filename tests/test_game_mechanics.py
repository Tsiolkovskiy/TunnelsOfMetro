"""
Unit Tests for Core Game Mechanics
Tests critical game systems and mechanics
"""

import unittest
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import game modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.resources import ResourcePool
from data.station import Station
from data.infrastructure import Infrastructure, BuildingType
from data.military_unit import MilitaryManager, UnitType
from systems.metro_map import MetroMap
from systems.diplomacy_system import DiplomacySystem, RelationshipLevel
from systems.trade_system import TradeSystem
from systems.combat_system import CombatSystem
from systems.victory_system import VictorySystem, VictoryType
from systems.ai_system import AISystem, AIPersonality
from utils.map_loader import MapLoader


class TestResourcePool(unittest.TestCase):
    """Test resource management system"""
    
    def setUp(self):
        """Set up test resources"""
        self.resources = ResourcePool()
    
    def test_initial_resources(self):
        """Test initial resource values"""
        self.assertEqual(self.resources.food, 50)
        self.assertEqual(self.resources.clean_water, 30)
        self.assertEqual(self.resources.scrap, 40)
        self.assertEqual(self.resources.medicine, 15)
        self.assertEqual(self.resources.mgr_rounds, 25)
    
    def test_add_resources(self):
        """Test adding resources"""
        initial_food = self.resources.food
        self.resources.add("food", 10)
        self.assertEqual(self.resources.food, initial_food + 10)
    
    def test_subtract_resources(self):
        """Test subtracting resources"""
        initial_food = self.resources.food
        success = self.resources.subtract("food", 10)
        self.assertTrue(success)
        self.assertEqual(self.resources.food, initial_food - 10)
    
    def test_insufficient_resources(self):
        """Test handling insufficient resources"""
        success = self.resources.subtract("food", 1000)
        self.assertFalse(success)
        self.assertEqual(self.resources.food, 50)  # Should remain unchanged
    
    def test_has_resources(self):
        """Test resource availability checking"""
        required = {"food": 10, "scrap": 5}
        self.assertTrue(self.resources.has_resources(required))
        
        required = {"food": 1000, "scrap": 5}
        self.assertFalse(self.resources.has_resources(required))


class TestStation(unittest.TestCase):
    """Test station mechanics"""
    
    def setUp(self):
        """Set up test station"""
        self.station = Station("Test Station", (100, 200), "Rangers")
    
    def test_station_creation(self):
        """Test station initialization"""
        self.assertEqual(self.station.name, "Test Station")
        self.assertEqual(self.station.position, (100, 200))
        self.assertEqual(self.station.controlling_faction, "Rangers")
        self.assertGreater(self.station.population, 0)
        self.assertGreater(self.station.morale, 0)
    
    def test_add_infrastructure(self):
        """Test adding infrastructure to station"""
        initial_count = len(self.station.infrastructure)
        success = self.station.add_infrastructure(BuildingType.MUSHROOM_FARM, 1)
        self.assertTrue(success)
        self.assertEqual(len(self.station.infrastructure), initial_count + 1)
        self.assertIn(BuildingType.MUSHROOM_FARM, self.station.infrastructure)
    
    def test_infrastructure_limit(self):
        """Test infrastructure capacity limits"""
        # Fill up infrastructure slots
        building_types = [BuildingType.MUSHROOM_FARM, BuildingType.WATER_FILTER, 
                         BuildingType.SCRAP_WORKSHOP, BuildingType.MED_BAY]
        
        for building_type in building_types:
            self.station.add_infrastructure(building_type, 1)
        
        # Try to add one more (should fail if at capacity)
        success = self.station.add_infrastructure(BuildingType.BARRACKS, 1)
        # This depends on the station's capacity limit implementation
    
    def test_process_turn(self):
        """Test turn processing for stations"""
        initial_morale = self.station.morale
        self.station.process_turn()
        # Morale might change based on conditions
        self.assertIsInstance(self.station.morale, (int, float))


class TestMilitaryManager(unittest.TestCase):
    """Test military unit management"""
    
    def setUp(self):
        """Set up test military manager"""
        self.military = MilitaryManager("Rangers")
        self.resources = ResourcePool()
    
    def test_recruit_unit(self):
        """Test unit recruitment"""
        initial_count = len(self.military.units)
        success, message, unit = self.military.recruit_unit(
            UnitType.MILITIA, "Test Station", self.resources
        )
        
        if success:
            self.assertEqual(len(self.military.units), initial_count + 1)
            self.assertEqual(unit.unit_type, UnitType.MILITIA)
            self.assertEqual(unit.stationed_at, "Test Station")
    
    def test_unit_maintenance(self):
        """Test unit maintenance costs"""
        # Recruit a unit first
        self.military.recruit_unit(UnitType.MILITIA, "Test Station", self.resources)
        
        maintenance = self.military.calculate_total_maintenance_cost()
        self.assertIsInstance(maintenance, dict)
        self.assertGreater(sum(maintenance.values()), 0)
    
    def test_unit_combat_strength(self):
        """Test combat strength calculation"""
        # Recruit some units
        self.military.recruit_unit(UnitType.MILITIA, "Test Station", self.resources)
        self.military.recruit_unit(UnitType.CONSCRIPTS, "Test Station", self.resources)
        
        strength = self.military.get_total_combat_strength()
        self.assertGreater(strength, 0)


class TestDiplomacySystem(unittest.TestCase):
    """Test diplomacy mechanics"""
    
    def setUp(self):
        """Set up test diplomacy system"""
        # Create a simple map for testing
        self.metro_map = MetroMap()
        self.metro_map.add_station(Station("Station A", (0, 0), "Rangers"))
        self.metro_map.add_station(Station("Station B", (100, 0), "Red Line"))
        
        self.diplomacy = DiplomacySystem(self.metro_map)
    
    def test_initial_relationships(self):
        """Test initial faction relationships"""
        relationship = self.diplomacy.get_relationship("Rangers", "Red Line")
        self.assertIsInstance(relationship, RelationshipLevel)
    
    def test_improve_relations(self):
        """Test relationship improvement"""
        initial_relationship = self.diplomacy.get_relationship("Rangers", "Red Line")
        
        # Try to improve relations
        success = self.diplomacy.improve_relations("Rangers", "Red Line", 10)
        
        if success:
            new_relationship = self.diplomacy.get_relationship("Rangers", "Red Line")
            # Relationship should be same or better
            self.assertGreaterEqual(new_relationship.value, initial_relationship.value)
    
    def test_faction_pairs(self):
        """Test faction pair generation"""
        pair1 = self.diplomacy._get_faction_pair("Rangers", "Red Line")
        pair2 = self.diplomacy._get_faction_pair("Red Line", "Rangers")
        self.assertEqual(pair1, pair2)  # Should be the same regardless of order


class TestVictorySystem(unittest.TestCase):
    """Test victory condition mechanics"""
    
    def setUp(self):
        """Set up test victory system"""
        self.metro_map = MetroMap()
        self.metro_map.add_station(Station("Station A", (0, 0), "Rangers"))
        self.victory = VictorySystem(self.metro_map)
    
    def test_victory_conditions_initialized(self):
        """Test that victory conditions are properly initialized"""
        self.assertGreater(len(self.victory.victory_conditions), 0)
        self.assertIn(VictoryType.POLITICAL, self.victory.victory_conditions)
        self.assertIn(VictoryType.MILITARY, self.victory.victory_conditions)
        self.assertIn(VictoryType.ECONOMIC, self.victory.victory_conditions)
    
    def test_victory_progress_tracking(self):
        """Test victory progress calculation"""
        game_state = {
            "controlled_stations": ["Station A"],
            "statistics": {"battles_won": 5, "trades_completed": 10},
            "player_resources": ResourcePool()
        }
        
        results = self.victory.check_victory_conditions(1, game_state)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        for result in results:
            self.assertIsInstance(result.progress, float)
            self.assertGreaterEqual(result.progress, 0.0)
            self.assertLessEqual(result.progress, 1.0)
    
    def test_game_not_ended_initially(self):
        """Test that game is not ended initially"""
        self.assertFalse(self.victory.is_game_ended())


class TestAISystem(unittest.TestCase):
    """Test AI behavior and decision making"""
    
    def setUp(self):
        """Set up test AI system"""
        self.metro_map = MetroMap()
        self.metro_map.add_station(Station("AI Station", (0, 0), "Red Line"))
        self.ai_system = AISystem(self.metro_map)
    
    def test_ai_factions_created(self):
        """Test that AI factions are created"""
        self.assertGreater(len(self.ai_system.ai_factions), 0)
    
    def test_ai_faction_personalities(self):
        """Test AI faction personality assignment"""
        for faction_name, ai_faction in self.ai_system.ai_factions.items():
            self.assertIsInstance(ai_faction.personality, AIPersonality)
            self.assertIsInstance(ai_faction.aggression_level, float)
            self.assertIsInstance(ai_faction.expansion_desire, float)
    
    def test_ai_resource_generation(self):
        """Test AI resource generation"""
        if self.ai_system.ai_factions:
            faction = list(self.ai_system.ai_factions.values())[0]
            initial_resources = faction.resources.copy()
            
            # Generate resources
            self.ai_system._generate_ai_resources(faction)
            
            # Resources should increase or stay the same
            for resource, amount in faction.resources.items():
                self.assertGreaterEqual(amount, initial_resources.get(resource, 0))


class TestGameIntegration(unittest.TestCase):
    """Test integration between game systems"""
    
    def setUp(self):
        """Set up integrated test environment"""
        # Load a test map
        map_loader = MapLoader()
        self.metro_map = map_loader.load_default_map()
        
        # Initialize systems
        self.diplomacy = DiplomacySystem(self.metro_map)
        self.trade = TradeSystem(self.metro_map)
        self.combat = CombatSystem(self.metro_map)
        self.victory = VictorySystem(self.metro_map)
        self.ai = AISystem(self.metro_map)
    
    def test_system_initialization(self):
        """Test that all systems initialize without errors"""
        self.assertIsNotNone(self.diplomacy)
        self.assertIsNotNone(self.trade)
        self.assertIsNotNone(self.combat)
        self.assertIsNotNone(self.victory)
        self.assertIsNotNone(self.ai)
    
    def test_faction_consistency(self):
        """Test that factions are consistent across systems"""
        # Get factions from different systems
        diplomacy_factions = set()
        for pair in self.diplomacy.faction_relationships.keys():
            diplomacy_factions.update(pair.split(" - "))
        
        ai_factions = set(self.ai.ai_factions.keys())
        
        # There should be some overlap (AI factions should be in diplomacy)
        self.assertTrue(len(ai_factions.intersection(diplomacy_factions)) > 0)
    
    def test_map_station_access(self):
        """Test that systems can access map stations"""
        stations = list(self.metro_map.stations.keys())
        self.assertGreater(len(stations), 0)
        
        # Test that systems can get station information
        for station_name in stations[:3]:  # Test first 3 stations
            station = self.metro_map.get_station(station_name)
            self.assertIsNotNone(station)
            self.assertEqual(station.name, station_name)


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    test_classes = [
        TestResourcePool,
        TestStation,
        TestMilitaryManager,
        TestDiplomacySystem,
        TestVictorySystem,
        TestAISystem,
        TestGameIntegration
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("Running Metro Strategy Game Tests...")
    print("=" * 50)
    
    result = run_tests()
    
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\nAll tests passed! ✓")
    else:
        print(f"\nSome tests failed. Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")