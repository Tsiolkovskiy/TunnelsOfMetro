"""
Military unit data model and management system.
Handles different unit types, recruitment, and unit positioning.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


class UnitType(Enum):
    """Different types of military units available in the game."""
    # Basic Units - cheap, numerous
    MILITIA = "militia"
    CONSCRIPTS = "conscripts"
    
    # Elite Units - expensive, powerful
    STORMTROOPERS = "stormtroopers"
    RANGERS = "rangers"
    
    # Specialist Units
    SCOUTS = "scouts"
    SPIES = "spies"
    STALKERS = "stalkers"
    
    # Support Units
    CARAVANS = "caravans"
    ENGINEERS = "engineers"


@dataclass
class UnitStats:
    """Base statistics for a unit type."""
    combat_strength: int
    movement_range: int
    recruitment_cost: Dict[str, int]  # Resource costs
    population_cost: int
    maintenance_cost: Dict[str, int]  # Per-turn costs
    special_abilities: List[str]


class MilitaryUnit:
    """Represents a military unit with position, stats, and capabilities."""
    
    def __init__(self, unit_type: UnitType, faction: str, station_id: str, 
                 equipment_level: int = 1, experience: int = 0):
        self.unit_type = unit_type
        self.faction = faction
        self.station_id = station_id
        self.equipment_level = equipment_level
        self.experience = experience
        self.health = 100
        self.morale = 100
        self.is_active = True
        
        # Get base stats for this unit type
        self.base_stats = self._get_unit_stats(unit_type)
    
    def _get_unit_stats(self, unit_type: UnitType) -> UnitStats:
        """Get base statistics for a unit type."""
        unit_stats = {
            UnitType.MILITIA: UnitStats(
                combat_strength=10,
                movement_range=2,
                recruitment_cost={"food": 5, "scrap": 3},
                population_cost=2,
                maintenance_cost={"food": 1},
                special_abilities=["local_knowledge"]
            ),
            UnitType.CONSCRIPTS: UnitStats(
                combat_strength=15,
                movement_range=2,
                recruitment_cost={"food": 8, "scrap": 5, "medicine": 2},
                population_cost=3,
                maintenance_cost={"food": 2},
                special_abilities=["disciplined"]
            ),
            UnitType.STORMTROOPERS: UnitStats(
                combat_strength=35,
                movement_range=3,
                recruitment_cost={"food": 20, "scrap": 15, "medicine": 8, "mgr": 5},
                population_cost=5,
                maintenance_cost={"food": 3, "scrap": 2},
                special_abilities=["assault", "heavy_weapons"]
            ),
            UnitType.RANGERS: UnitStats(
                combat_strength=40,
                movement_range=4,
                recruitment_cost={"food": 25, "scrap": 20, "medicine": 10, "mgr": 8},
                population_cost=4,
                maintenance_cost={"food": 3, "medicine": 1},
                special_abilities=["elite_training", "tunnel_warfare", "leadership"]
            ),
            UnitType.SCOUTS: UnitStats(
                combat_strength=8,
                movement_range=5,
                recruitment_cost={"food": 10, "scrap": 8},
                population_cost=1,
                maintenance_cost={"food": 1},
                special_abilities=["stealth", "reconnaissance", "fast_movement"]
            ),
            UnitType.SPIES: UnitStats(
                combat_strength=5,
                movement_range=3,
                recruitment_cost={"food": 15, "medicine": 5, "mgr": 3},
                population_cost=1,
                maintenance_cost={"food": 2},
                special_abilities=["infiltration", "sabotage", "intelligence"]
            ),
            UnitType.STALKERS: UnitStats(
                combat_strength=25,
                movement_range=4,
                recruitment_cost={"food": 18, "scrap": 12, "medicine": 6},
                population_cost=2,
                maintenance_cost={"food": 2, "scrap": 1},
                special_abilities=["anomaly_resistance", "scavenging", "survival"]
            ),
            UnitType.CARAVANS: UnitStats(
                combat_strength=3,
                movement_range=3,
                recruitment_cost={"scrap": 20, "food": 5},
                population_cost=3,
                maintenance_cost={"scrap": 1},
                special_abilities=["cargo_transport", "trade_bonus"]
            ),
            UnitType.ENGINEERS: UnitStats(
                combat_strength=8,
                movement_range=2,
                recruitment_cost={"scrap": 25, "medicine": 8, "mgr": 2},
                population_cost=4,
                maintenance_cost={"scrap": 2},
                special_abilities=["construction", "repair", "fortification"]
            )
        }
        return unit_stats[unit_type]
    
    def calculate_combat_strength(self) -> int:
        """Calculate effective combat strength including modifiers."""
        base_strength = self.base_stats.combat_strength
        
        # Equipment level modifier (1-5 scale)
        equipment_modifier = 1.0 + (self.equipment_level - 1) * 0.2
        
        # Experience modifier (0-100 scale)
        experience_modifier = 1.0 + (self.experience / 100) * 0.5
        
        # Health modifier
        health_modifier = self.health / 100
        
        # Morale modifier
        morale_modifier = 0.5 + (self.morale / 100) * 0.5
        
        effective_strength = base_strength * equipment_modifier * experience_modifier * health_modifier * morale_modifier
        return int(effective_strength)
    
    def can_move_to(self, target_station_id: str, metro_map) -> bool:
        """Check if unit can move to target station."""
        if not self.is_active:
            return False
        
        # Check if target is within movement range
        path = metro_map.find_path(self.station_id, target_station_id)
        if not path or len(path) - 1 > self.base_stats.movement_range:
            return False
        
        return True
    
    def move_to_station(self, target_station_id: str) -> bool:
        """Move unit to target station."""
        if not self.is_active:
            return False
        
        self.station_id = target_station_id
        return True
    
    def take_damage(self, damage: int) -> bool:
        """Apply damage to unit. Returns True if unit is destroyed."""
        self.health = max(0, self.health - damage)
        if self.health <= 0:
            self.is_active = False
            return True
        return False
    
    def gain_experience(self, amount: int):
        """Increase unit experience."""
        self.experience = min(100, self.experience + amount)
    
    def modify_morale(self, change: int):
        """Modify unit morale."""
        self.morale = max(0, min(100, self.morale + change))
    
    def get_maintenance_cost(self) -> Dict[str, int]:
        """Get per-turn maintenance cost for this unit."""
        return self.base_stats.maintenance_cost.copy()
    
    def has_ability(self, ability: str) -> bool:
        """Check if unit has a specific special ability."""
        return ability in self.base_stats.special_abilities
    
    def get_info(self) -> Dict:
        """Get comprehensive unit information."""
        return {
            "type": self.unit_type.value,
            "faction": self.faction,
            "station": self.station_id,
            "combat_strength": self.calculate_combat_strength(),
            "health": self.health,
            "morale": self.morale,
            "experience": self.experience,
            "equipment_level": self.equipment_level,
            "abilities": self.base_stats.special_abilities,
            "active": self.is_active
        }


class MilitaryManager:
    """Manages military units for a faction."""
    
    def __init__(self, faction_name: str):
        self.faction_name = faction_name
        self.units: List[MilitaryUnit] = []
        self.unit_id_counter = 0
    
    def can_recruit_unit(self, unit_type: UnitType, station, resources: Dict[str, int]) -> Tuple[bool, str]:
        """Check if unit can be recruited at station with available resources."""
        # Get unit stats
        stats = MilitaryUnit(unit_type, self.faction_name, "temp", 1, 0).base_stats
        
        # Check population requirement
        if station.population < stats.population_cost:
            return False, f"Not enough population (need {stats.population_cost}, have {station.population})"
        
        # Check resource requirements
        for resource, cost in stats.recruitment_cost.items():
            if resources.get(resource, 0) < cost:
                return False, f"Not enough {resource} (need {cost}, have {resources.get(resource, 0)})"
        
        # Check if station has required infrastructure for elite units
        if unit_type in [UnitType.STORMTROOPERS, UnitType.RANGERS]:
            if not station.has_infrastructure("barracks"):
                return False, "Elite units require barracks infrastructure"
        
        return True, "Can recruit"
    
    def recruit_unit(self, unit_type: UnitType, station_id: str, resources: Dict[str, int]) -> Tuple[bool, str, Optional[MilitaryUnit]]:
        """Recruit a new military unit."""
        # Create temporary unit to get stats
        temp_unit = MilitaryUnit(unit_type, self.faction_name, station_id, 1, 0)
        stats = temp_unit.base_stats
        
        # Deduct resources
        for resource, cost in stats.recruitment_cost.items():
            resources[resource] -= cost
        
        # Create actual unit
        unit = MilitaryUnit(unit_type, self.faction_name, station_id, 1, 0)
        self.units.append(unit)
        self.unit_id_counter += 1
        
        return True, f"Recruited {unit_type.value} at {station_id}", unit
    
    def get_units_at_station(self, station_id: str) -> List[MilitaryUnit]:
        """Get all active units at a specific station."""
        return [unit for unit in self.units if unit.station_id == station_id and unit.is_active]
    
    def get_total_combat_strength_at_station(self, station_id: str) -> int:
        """Get total combat strength of all units at station."""
        units = self.get_units_at_station(station_id)
        return sum(unit.calculate_combat_strength() for unit in units)
    
    def calculate_total_maintenance_cost(self) -> Dict[str, int]:
        """Calculate total maintenance cost for all active units."""
        total_cost = {}
        for unit in self.units:
            if unit.is_active:
                for resource, cost in unit.get_maintenance_cost().items():
                    total_cost[resource] = total_cost.get(resource, 0) + cost
        return total_cost
    
    def remove_destroyed_units(self):
        """Remove all destroyed units from the unit list."""
        self.units = [unit for unit in self.units if unit.is_active]
    
    def get_unit_summary(self) -> Dict[str, int]:
        """Get summary of unit counts by type."""
        summary = {}
        for unit in self.units:
            if unit.is_active:
                unit_type = unit.unit_type.value
                summary[unit_type] = summary.get(unit_type, 0) + 1
        return summary
    
    def get_all_units_info(self) -> List[Dict]:
        """Get information for all active units."""
        return [unit.get_info() for unit in self.units if unit.is_active]