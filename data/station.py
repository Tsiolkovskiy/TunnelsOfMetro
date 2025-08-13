"""
Station Data Model
Represents a Metro station with all its properties and capabilities
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum

from data.resources import ResourcePool
from data.infrastructure import Infrastructure, BuildingType


class StationStatus(Enum):
    """Station operational status"""
    OPERATIONAL = "operational"
    DAMAGED = "damaged"
    RUINED = "ruined"
    INFESTED = "infested"
    ANOMALOUS = "anomalous"


class Station:
    """
    Represents a Metro station with all its properties and capabilities
    
    This class handles:
    - Basic station properties (name, position, faction control)
    - Resource production and management
    - Infrastructure and building management
    - Population and morale tracking
    - Station events and status effects
    """
    
    def __init__(
        self,
        name: str,
        position: tuple,
        metro_line: str = "",
        faction: str = "Independent",
        population: int = 100,
        morale: int = 50
    ):
        """
        Initialize a Metro station
        
        Args:
            name: Station name (e.g., "VDNKh", "Polis")
            position: (x, y) coordinates on the map
            metro_line: Metro line name (e.g., "Sokolnicheskaya")
            faction: Controlling faction name
            population: Current population count
            morale: Station morale (0-100)
        """
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Basic properties
        self.name = name
        self.position = position
        self.metro_line = metro_line
        self.controlling_faction = faction
        self.population = max(0, population)
        self.morale = max(0, min(100, morale))
        
        # Operational status
        self.status = StationStatus.OPERATIONAL
        self.defensive_value = 10  # Base defense
        
        # Resources and infrastructure
        self.resources = ResourcePool()
        self.infrastructure: Dict[BuildingType, Infrastructure] = {}
        
        # Special traits and effects
        self.special_traits: List[str] = []
        self.active_effects: List[Dict[str, Any]] = []
        
        # Production modifiers
        self.production_modifiers: Dict[str, float] = {
            "food": 1.0,
            "clean_water": 1.0,
            "scrap": 1.0,
            "medicine": 1.0
        }
        
        self.logger.info(f"Station {name} initialized - Faction: {faction}, Population: {population}")
    
    def get_resource_production(self) -> Dict[str, int]:
        """
        Calculate total resource production for this station
        
        Returns:
            Dictionary of resource types and their production amounts per turn
        """
        production = {
            "food": 0,
            "clean_water": 0,
            "scrap": 0,
            "medicine": 0
        }
        
        # Base production from population
        base_food = max(1, self.population // 20)  # 1 food per 20 people
        production["food"] = int(base_food * self.production_modifiers["food"])
        
        # Infrastructure-based production
        for building_type, infrastructure in self.infrastructure.items():
            building_production = infrastructure.get_resource_output()
            for resource, amount in building_production.items():
                if resource in production:
                    modifier = self.production_modifiers.get(resource, 1.0)
                    production[resource] += int(amount * modifier)
        
        # Apply morale modifier (low morale reduces production)
        morale_modifier = 0.5 + (self.morale / 100.0) * 0.5  # 0.5 to 1.0 range
        for resource in production:
            production[resource] = int(production[resource] * morale_modifier)
        
        # Apply status effects
        if self.status == StationStatus.DAMAGED:
            for resource in production:
                production[resource] = int(production[resource] * 0.7)
        elif self.status == StationStatus.RUINED:
            for resource in production:
                production[resource] = int(production[resource] * 0.3)
        
        return production
    
    def change_faction_control(self, new_faction: str, peaceful: bool = False):
        """
        Change the controlling faction of this station
        
        Args:
            new_faction: Name of the new controlling faction
            peaceful: Whether the change was peaceful (affects morale)
        """
        old_faction = self.controlling_faction
        self.controlling_faction = new_faction
        
        # Morale effects
        if not peaceful:
            # Hostile takeover reduces morale
            self.morale = max(0, self.morale - 20)
            self.logger.info(f"Station {self.name} captured by {new_faction} from {old_faction}")
        else:
            # Peaceful transition has minimal impact
            self.morale = max(0, self.morale - 5)
            self.logger.info(f"Station {self.name} peacefully joined {new_faction}")
        
        # Population may flee during hostile takeover
        if not peaceful and self.population > 50:
            population_loss = int(self.population * 0.1)  # 10% flee
            self.population = max(50, self.population - population_loss)
    
    def add_infrastructure(self, building_type: BuildingType, efficiency_level: int = 1) -> bool:
        """
        Add infrastructure to the station
        
        Args:
            building_type: Type of building to construct
            efficiency_level: Building efficiency level (1-3)
            
        Returns:
            True if building was added successfully
        """
        if building_type in self.infrastructure:
            self.logger.warning(f"Building {building_type} already exists at {self.name}")
            return False
        
        # Check if station can support more buildings
        max_buildings = max(3, self.population // 50)  # 1 building per 50 people, minimum 3
        if len(self.infrastructure) >= max_buildings:
            self.logger.warning(f"Station {self.name} cannot support more buildings")
            return False
        
        # Create and add infrastructure
        infrastructure = Infrastructure(building_type, efficiency_level)
        self.infrastructure[building_type] = infrastructure
        
        # Update defensive value for military buildings
        if building_type == BuildingType.BARRACKS:
            self.defensive_value += 15
        elif building_type == BuildingType.FORTIFICATIONS:
            self.defensive_value += 25
        
        self.logger.info(f"Added {building_type} to station {self.name}")
        return True
    
    def has_infrastructure(self, building_type: str) -> bool:
        """
        Check if station has a specific type of infrastructure
        
        Args:
            building_type: Building type to check for (string or BuildingType)
            
        Returns:
            True if the station has this infrastructure
        """
        if isinstance(building_type, str):
            # Convert string to BuildingType
            try:
                building_type = BuildingType(building_type.lower())
            except ValueError:
                return False
        
        return building_type in self.infrastructure
    
    def upgrade_infrastructure(self, building_type: BuildingType) -> bool:
        """
        Upgrade existing infrastructure
        
        Args:
            building_type: Type of building to upgrade
            
        Returns:
            True if upgrade was successful
        """
        if building_type not in self.infrastructure:
            self.logger.warning(f"No {building_type} to upgrade at {self.name}")
            return False
        
        infrastructure = self.infrastructure[building_type]
        if infrastructure.upgrade():
            self.logger.info(f"Upgraded {building_type} at station {self.name}")
            return True
        else:
            self.logger.warning(f"Cannot upgrade {building_type} at {self.name} - already at max level")
            return False
    
    def apply_event(self, event: Dict[str, Any]):
        """
        Apply an event effect to this station
        
        Args:
            event: Event data containing type, effects, and duration
        """
        event_type = event.get("type", "unknown")
        effects = event.get("effects", {})
        duration = event.get("duration", 1)
        
        self.logger.info(f"Applying event '{event_type}' to station {self.name}")
        
        # Apply immediate effects
        if "population_change" in effects:
            old_pop = self.population
            self.population = max(0, self.population + effects["population_change"])
            self.logger.info(f"Population changed from {old_pop} to {self.population}")
        
        if "morale_change" in effects:
            old_morale = self.morale
            self.morale = max(0, min(100, self.morale + effects["morale_change"]))
            self.logger.info(f"Morale changed from {old_morale} to {self.morale}")
        
        if "status_change" in effects:
            try:
                new_status = StationStatus(effects["status_change"])
                self.status = new_status
                self.logger.info(f"Station status changed to {new_status}")
            except ValueError:
                self.logger.error(f"Invalid status: {effects['status_change']}")
        
        # Add ongoing effects
        if duration > 1:
            ongoing_effect = {
                "type": event_type,
                "effects": effects,
                "remaining_turns": duration - 1
            }
            self.active_effects.append(ongoing_effect)
    
    def process_turn(self):
        """
        Process end-of-turn updates for this station
        """
        # Process ongoing effects
        effects_to_remove = []
        for i, effect in enumerate(self.active_effects):
            effect["remaining_turns"] -= 1
            if effect["remaining_turns"] <= 0:
                effects_to_remove.append(i)
        
        # Remove expired effects
        for i in reversed(effects_to_remove):
            removed_effect = self.active_effects.pop(i)
            self.logger.info(f"Effect '{removed_effect['type']}' expired at {self.name}")
        
        # Natural morale recovery (very slow)
        if self.morale < 50 and self.status == StationStatus.OPERATIONAL:
            self.morale = min(100, self.morale + 1)
        
        # Population growth/decline based on conditions
        if self.morale > 70 and self.status == StationStatus.OPERATIONAL:
            # Slow population growth in good conditions
            growth = max(1, int(self.population * 0.02))  # 2% growth
            self.population += growth
        elif self.morale < 30 or self.status in [StationStatus.DAMAGED, StationStatus.RUINED]:
            # Population decline in bad conditions
            decline = max(1, int(self.population * 0.01))  # 1% decline
            self.population = max(10, self.population - decline)  # Minimum 10 people
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get comprehensive station information
        
        Returns:
            Dictionary containing all station data
        """
        return {
            "name": self.name,
            "position": self.position,
            "metro_line": self.metro_line,
            "faction": self.controlling_faction,
            "population": self.population,
            "morale": self.morale,
            "status": self.status.value,
            "defensive_value": self.defensive_value,
            "resources": self.resources.to_dict(),
            "production": self.get_resource_production(),
            "infrastructure": {bt.value: inf.to_dict() for bt, inf in self.infrastructure.items()},
            "special_traits": self.special_traits.copy(),
            "active_effects": len(self.active_effects)
        }
    
    def __str__(self) -> str:
        """String representation of the station"""
        return f"Station({self.name}, {self.controlling_faction}, Pop: {self.population})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"Station(name='{self.name}', faction='{self.controlling_faction}', "
                f"population={self.population}, morale={self.morale}, status={self.status.value})")