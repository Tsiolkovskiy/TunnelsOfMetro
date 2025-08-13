"""
Infrastructure System
Manages station buildings and their effects on resource production
"""

import logging
from typing import Dict, Any
from enum import Enum


class BuildingType(Enum):
    """Types of buildings that can be constructed in stations"""
    MUSHROOM_FARM = "mushroom_farm"
    WATER_FILTER = "water_filter"
    SCRAP_WORKSHOP = "scrap_workshop"
    MED_BAY = "med_bay"
    BARRACKS = "barracks"
    FORTIFICATIONS = "fortifications"
    MARKET = "market"
    LIBRARY = "library"


class Infrastructure:
    """
    Represents a building or infrastructure in a Metro station
    
    Each building provides specific benefits:
    - Resource production
    - Defensive bonuses
    - Special capabilities
    """
    
    def __init__(self, building_type: BuildingType, efficiency_level: int = 1):
        """
        Initialize infrastructure
        
        Args:
            building_type: Type of building
            efficiency_level: Building efficiency (1-3, where 3 is maximum)
        """
        self.logger = logging.getLogger(__name__)
        
        self.building_type = building_type
        self.efficiency_level = max(1, min(3, efficiency_level))
        self.damage_level = 0  # 0 = undamaged, 100 = destroyed
        
        # Building specifications
        self._building_specs = {
            BuildingType.MUSHROOM_FARM: {
                "name": "Mushroom Farm",
                "description": "Cultivates mushrooms for food production",
                "base_production": {"food": 15},
                "upgrade_cost": {"scrap": 20, "clean_water": 10},
                "maintenance_cost": {"clean_water": 2}
            },
            BuildingType.WATER_FILTER: {
                "name": "Water Filter",
                "description": "Purifies contaminated water",
                "base_production": {"clean_water": 10},
                "upgrade_cost": {"scrap": 25, "medicine": 5},
                "maintenance_cost": {"scrap": 1}
            },
            BuildingType.SCRAP_WORKSHOP: {
                "name": "Scrap Workshop",
                "description": "Processes salvaged materials",
                "base_production": {"scrap": 12},
                "upgrade_cost": {"scrap": 15, "mgr_rounds": 2},
                "maintenance_cost": {}
            },
            BuildingType.MED_BAY: {
                "name": "Medical Bay",
                "description": "Produces medicine and treats injuries",
                "base_production": {"medicine": 8},
                "upgrade_cost": {"scrap": 30, "clean_water": 15},
                "maintenance_cost": {"clean_water": 3}
            },
            BuildingType.BARRACKS: {
                "name": "Barracks",
                "description": "Houses and trains military units",
                "base_production": {},
                "upgrade_cost": {"scrap": 40, "mgr_rounds": 5},
                "maintenance_cost": {"food": 5},
                "special_effects": {"defensive_bonus": 15, "unit_capacity": 20}
            },
            BuildingType.FORTIFICATIONS: {
                "name": "Fortifications",
                "description": "Defensive structures and barriers",
                "base_production": {},
                "upgrade_cost": {"scrap": 50, "mgr_rounds": 3},
                "maintenance_cost": {},
                "special_effects": {"defensive_bonus": 25, "siege_resistance": 30}
            },
            BuildingType.MARKET: {
                "name": "Market",
                "description": "Trading post for resource exchange",
                "base_production": {},
                "upgrade_cost": {"scrap": 35, "mgr_rounds": 8},
                "maintenance_cost": {"food": 3},
                "special_effects": {"trade_bonus": 20, "mgr_generation": 2}
            },
            BuildingType.LIBRARY: {
                "name": "Library",
                "description": "Preserves knowledge and enables research",
                "base_production": {},
                "upgrade_cost": {"scrap": 45, "mgr_rounds": 10},
                "maintenance_cost": {"clean_water": 5},
                "special_effects": {"research_bonus": 25, "morale_bonus": 10}
            }
        }
        
        self.logger.info(f"Created {building_type.value} (Level {efficiency_level})")
    
    def get_resource_output(self) -> Dict[str, int]:
        """
        Calculate resource output for this building
        
        Returns:
            Dictionary of resource production per turn
        """
        specs = self._building_specs[self.building_type]
        base_production = specs.get("base_production", {})
        
        # Calculate efficiency modifier
        efficiency_modifier = self.efficiency_level * 0.5 + 0.5  # 1.0, 1.5, 2.0 for levels 1, 2, 3
        
        # Calculate damage modifier
        damage_modifier = max(0.1, 1.0 - (self.damage_level / 100.0))
        
        # Apply modifiers to base production
        output = {}
        for resource, base_amount in base_production.items():
            final_amount = int(base_amount * efficiency_modifier * damage_modifier)
            output[resource] = final_amount
        
        return output
    
    def get_upgrade_cost(self) -> Dict[str, int]:
        """
        Get cost to upgrade this building to the next level
        
        Returns:
            Dictionary of resource costs, or empty dict if max level
        """
        if self.efficiency_level >= 3:
            return {}  # Already at maximum level
        
        specs = self._building_specs[self.building_type]
        base_cost = specs.get("upgrade_cost", {})
        
        # Cost increases with each level
        cost_multiplier = self.efficiency_level  # Level 1->2 costs 1x, Level 2->3 costs 2x
        
        upgrade_cost = {}
        for resource, base_amount in base_cost.items():
            upgrade_cost[resource] = base_amount * cost_multiplier
        
        return upgrade_cost
    
    def get_maintenance_cost(self) -> Dict[str, int]:
        """
        Get per-turn maintenance cost for this building
        
        Returns:
            Dictionary of resource costs per turn
        """
        specs = self._building_specs[self.building_type]
        base_maintenance = specs.get("maintenance_cost", {})
        
        # Maintenance scales with efficiency level
        maintenance_multiplier = self.efficiency_level * 0.5 + 0.5
        
        maintenance_cost = {}
        for resource, base_amount in base_maintenance.items():
            maintenance_cost[resource] = int(base_amount * maintenance_multiplier)
        
        return maintenance_cost
    
    def get_special_effects(self) -> Dict[str, int]:
        """
        Get special effects provided by this building
        
        Returns:
            Dictionary of special effects and their values
        """
        specs = self._building_specs[self.building_type]
        base_effects = specs.get("special_effects", {})
        
        # Effects scale with efficiency level
        effects_multiplier = self.efficiency_level * 0.5 + 0.5
        
        # Apply damage reduction to effects
        damage_modifier = max(0.1, 1.0 - (self.damage_level / 100.0))
        
        special_effects = {}
        for effect, base_value in base_effects.items():
            final_value = int(base_value * effects_multiplier * damage_modifier)
            special_effects[effect] = final_value
        
        return special_effects
    
    def upgrade(self) -> bool:
        """
        Upgrade building to next efficiency level
        
        Returns:
            True if upgrade was successful
        """
        if self.efficiency_level >= 3:
            self.logger.warning(f"{self.building_type.value} already at maximum level")
            return False
        
        old_level = self.efficiency_level
        self.efficiency_level += 1
        
        self.logger.info(f"Upgraded {self.building_type.value} from level {old_level} to {self.efficiency_level}")
        return True
    
    def apply_damage(self, damage_amount: int):
        """
        Apply damage to the building
        
        Args:
            damage_amount: Amount of damage to apply (0-100)
        """
        old_damage = self.damage_level
        self.damage_level = min(100, self.damage_level + damage_amount)
        
        if self.damage_level != old_damage:
            self.logger.info(f"{self.building_type.value} damage: {old_damage}% -> {self.damage_level}%")
    
    def repair(self, repair_amount: int):
        """
        Repair damage to the building
        
        Args:
            repair_amount: Amount of damage to repair (0-100)
        """
        old_damage = self.damage_level
        self.damage_level = max(0, self.damage_level - repair_amount)
        
        if self.damage_level != old_damage:
            self.logger.info(f"{self.building_type.value} repaired: {old_damage}% -> {self.damage_level}% damage")
    
    def is_operational(self) -> bool:
        """Check if building is operational (not destroyed)"""
        return self.damage_level < 100
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get comprehensive building information
        
        Returns:
            Dictionary containing all building data
        """
        specs = self._building_specs[self.building_type]
        
        return {
            "type": self.building_type.value,
            "name": specs["name"],
            "description": specs["description"],
            "efficiency_level": self.efficiency_level,
            "damage_level": self.damage_level,
            "operational": self.is_operational(),
            "resource_output": self.get_resource_output(),
            "maintenance_cost": self.get_maintenance_cost(),
            "upgrade_cost": self.get_upgrade_cost(),
            "special_effects": self.get_special_effects()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "building_type": self.building_type.value,
            "efficiency_level": self.efficiency_level,
            "damage_level": self.damage_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Infrastructure':
        """Create Infrastructure from dictionary"""
        building_type = BuildingType(data["building_type"])
        infrastructure = cls(building_type, data["efficiency_level"])
        infrastructure.damage_level = data.get("damage_level", 0)
        return infrastructure
    
    def __str__(self) -> str:
        """String representation"""
        specs = self._building_specs[self.building_type]
        status = "Operational" if self.is_operational() else "Destroyed"
        return f"{specs['name']} (Level {self.efficiency_level}, {status})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"Infrastructure(type={self.building_type.value}, "
                f"level={self.efficiency_level}, damage={self.damage_level}%)")