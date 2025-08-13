"""
Building and Upgrade System
Manages station development, construction, and infrastructure upgrades
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from data.infrastructure import Infrastructure, BuildingType
from data.station import Station
from data.resources import ResourcePool
from systems.metro_map import MetroMap


class ConstructionResult(Enum):
    """Results of construction attempts"""
    SUCCESS = "success"
    INSUFFICIENT_RESOURCES = "insufficient_resources"
    INSUFFICIENT_POPULATION = "insufficient_population"
    BUILDING_EXISTS = "building_exists"
    STATION_CAPACITY_FULL = "station_capacity_full"
    INVALID_STATION = "invalid_station"
    INVALID_BUILDING_TYPE = "invalid_building_type"


class BuildingProject:
    """Represents an ongoing construction project"""
    
    def __init__(self, station_name: str, building_type: BuildingType, 
                 construction_time: int, resource_cost: Dict[str, int]):
        self.station_name = station_name
        self.building_type = building_type
        self.construction_time = construction_time
        self.remaining_time = construction_time
        self.resource_cost = resource_cost
        self.start_turn = 0
    
    def advance_construction(self) -> bool:
        """
        Advance construction by one turn
        
        Returns:
            True if construction is complete
        """
        self.remaining_time = max(0, self.remaining_time - 1)
        return self.remaining_time == 0
    
    def get_progress(self) -> float:
        """Get construction progress as percentage (0.0 to 1.0)"""
        if self.construction_time == 0:
            return 1.0
        return 1.0 - (self.remaining_time / self.construction_time)


class BuildingSystem:
    """
    Complete building and upgrade management system
    
    Features:
    - Construction planning and resource checking
    - Multi-turn construction projects
    - Building upgrades with resource costs
    - Station specialization bonuses
    - Infrastructure maintenance
    - Building damage and repair
    """
    
    def __init__(self, metro_map: MetroMap):
        """
        Initialize building system
        
        Args:
            metro_map: MetroMap instance
        """
        self.metro_map = metro_map
        self.logger = logging.getLogger(__name__)
        
        # Active construction projects
        self.construction_projects: List[BuildingProject] = []
        
        # Building construction times (in turns)
        self.construction_times = {
            BuildingType.MUSHROOM_FARM: 2,
            BuildingType.WATER_FILTER: 3,
            BuildingType.SCRAP_WORKSHOP: 2,
            BuildingType.MED_BAY: 4,
            BuildingType.BARRACKS: 5,
            BuildingType.FORTIFICATIONS: 6,
            BuildingType.MARKET: 4,
            BuildingType.LIBRARY: 7
        }
        
        # Base construction costs
        self.construction_costs = {
            BuildingType.MUSHROOM_FARM: {"scrap": 15, "clean_water": 5},
            BuildingType.WATER_FILTER: {"scrap": 25, "mgr_rounds": 2},
            BuildingType.SCRAP_WORKSHOP: {"scrap": 20, "food": 10},
            BuildingType.MED_BAY: {"scrap": 35, "clean_water": 15, "mgr_rounds": 3},
            BuildingType.BARRACKS: {"scrap": 50, "food": 20, "mgr_rounds": 8},
            BuildingType.FORTIFICATIONS: {"scrap": 75, "mgr_rounds": 12},
            BuildingType.MARKET: {"scrap": 40, "food": 25, "mgr_rounds": 15},
            BuildingType.LIBRARY: {"scrap": 60, "clean_water": 30, "mgr_rounds": 20}
        }
        
        # Population requirements for construction
        self.population_requirements = {
            BuildingType.MUSHROOM_FARM: 30,
            BuildingType.WATER_FILTER: 40,
            BuildingType.SCRAP_WORKSHOP: 35,
            BuildingType.MED_BAY: 60,
            BuildingType.BARRACKS: 80,
            BuildingType.FORTIFICATIONS: 70,
            BuildingType.MARKET: 100,
            BuildingType.LIBRARY: 120
        }
        
        self.logger.info("Building system initialized")
    
    def can_construct_building(self, station_name: str, building_type: BuildingType, 
                             resources: ResourcePool) -> Tuple[bool, str]:
        """
        Check if a building can be constructed at a station
        
        Args:
            station_name: Name of the station
            building_type: Type of building to construct
            resources: Available resources
            
        Returns:
            Tuple of (can_construct, reason)
        """
        station = self.metro_map.get_station(station_name)
        if not station:
            return False, f"Station {station_name} not found"
        
        # Check if building already exists
        if building_type in station.infrastructure:
            return False, f"{building_type.value} already exists at {station_name}"
        
        # Check station capacity
        max_buildings = self._get_station_building_capacity(station)
        current_buildings = len(station.infrastructure)
        if current_buildings >= max_buildings:
            return False, f"Station at capacity ({current_buildings}/{max_buildings} buildings)"
        
        # Check population requirement
        required_population = self.population_requirements.get(building_type, 0)
        if station.population < required_population:
            return False, f"Insufficient population (need {required_population}, have {station.population})"
        
        # Check resource requirements
        required_resources = self.construction_costs.get(building_type, {})
        for resource, amount in required_resources.items():
            if not resources.has_sufficient(resource, amount):
                current = getattr(resources, resource, 0)
                return False, f"Insufficient {resource} (need {amount}, have {current})"
        
        # Check for prerequisite buildings
        prerequisites = self._get_building_prerequisites(building_type)
        for prereq in prerequisites:
            if prereq not in station.infrastructure:
                return False, f"Requires {prereq.value} to be built first"
        
        return True, "Construction possible"
    
    def start_construction(self, station_name: str, building_type: BuildingType, 
                          resources: ResourcePool, current_turn: int) -> Tuple[bool, str]:
        """
        Start construction of a building
        
        Args:
            station_name: Name of the station
            building_type: Type of building to construct
            resources: Player's resource pool
            current_turn: Current game turn
            
        Returns:
            Tuple of (success, message)
        """
        # Check if construction is possible
        can_construct, reason = self.can_construct_building(station_name, building_type, resources)
        if not can_construct:
            return False, reason
        
        # Check if already under construction
        for project in self.construction_projects:
            if project.station_name == station_name and project.building_type == building_type:
                return False, f"{building_type.value} already under construction at {station_name}"
        
        # Consume resources
        required_resources = self.construction_costs.get(building_type, {})
        for resource, amount in required_resources.items():
            resources.subtract(resource, amount)
        
        # Create construction project
        construction_time = self.construction_times.get(building_type, 3)
        project = BuildingProject(station_name, building_type, construction_time, required_resources)
        project.start_turn = current_turn
        
        self.construction_projects.append(project)
        
        self.logger.info(f"Started construction of {building_type.value} at {station_name} (ETA: {construction_time} turns)")
        
        return True, f"Construction of {building_type.value} started at {station_name} (ETA: {construction_time} turns)"
    
    def can_upgrade_building(self, station_name: str, building_type: BuildingType, 
                           resources: ResourcePool) -> Tuple[bool, str]:
        """
        Check if a building can be upgraded
        
        Args:
            station_name: Name of the station
            building_type: Type of building to upgrade
            resources: Available resources
            
        Returns:
            Tuple of (can_upgrade, reason)
        """
        station = self.metro_map.get_station(station_name)
        if not station:
            return False, f"Station {station_name} not found"
        
        # Check if building exists
        if building_type not in station.infrastructure:
            return False, f"{building_type.value} does not exist at {station_name}"
        
        building = station.infrastructure[building_type]
        
        # Check if already at max level
        if building.efficiency_level >= 3:
            return False, f"{building_type.value} already at maximum level"
        
        # Check if building is operational
        if not building.is_operational():
            return False, f"{building_type.value} is too damaged to upgrade (repair first)"
        
        # Check resource requirements
        upgrade_cost = building.get_upgrade_cost()
        for resource, amount in upgrade_cost.items():
            if not resources.has_sufficient(resource, amount):
                current = getattr(resources, resource, 0)
                return False, f"Insufficient {resource} (need {amount}, have {current})"
        
        return True, "Upgrade possible"
    
    def upgrade_building(self, station_name: str, building_type: BuildingType, 
                        resources: ResourcePool) -> Tuple[bool, str]:
        """
        Upgrade a building to the next level
        
        Args:
            station_name: Name of the station
            building_type: Type of building to upgrade
            resources: Player's resource pool
            
        Returns:
            Tuple of (success, message)
        """
        # Check if upgrade is possible
        can_upgrade, reason = self.can_upgrade_building(station_name, building_type, resources)
        if not can_upgrade:
            return False, reason
        
        station = self.metro_map.get_station(station_name)
        building = station.infrastructure[building_type]
        
        # Consume resources
        upgrade_cost = building.get_upgrade_cost()
        for resource, amount in upgrade_cost.items():
            resources.subtract(resource, amount)
        
        # Upgrade building
        old_level = building.efficiency_level
        building.upgrade()
        
        self.logger.info(f"Upgraded {building_type.value} at {station_name} from level {old_level} to {building.efficiency_level}")
        
        return True, f"Upgraded {building_type.value} at {station_name} to level {building.efficiency_level}"
    
    def repair_building(self, station_name: str, building_type: BuildingType, 
                       resources: ResourcePool, repair_amount: int = 50) -> Tuple[bool, str]:
        """
        Repair damage to a building
        
        Args:
            station_name: Name of the station
            building_type: Type of building to repair
            resources: Player's resource pool
            repair_amount: Amount of damage to repair (0-100)
            
        Returns:
            Tuple of (success, message)
        """
        station = self.metro_map.get_station(station_name)
        if not station:
            return False, f"Station {station_name} not found"
        
        # Check if building exists
        if building_type not in station.infrastructure:
            return False, f"{building_type.value} does not exist at {station_name}"
        
        building = station.infrastructure[building_type]
        
        # Check if repair is needed
        if building.damage_level == 0:
            return False, f"{building_type.value} is not damaged"
        
        # Calculate repair cost
        repair_cost = self._calculate_repair_cost(building_type, repair_amount)
        
        # Check resource requirements
        for resource, amount in repair_cost.items():
            if not resources.has_sufficient(resource, amount):
                current = getattr(resources, resource, 0)
                return False, f"Insufficient {resource} (need {amount}, have {current})"
        
        # Consume resources
        for resource, amount in repair_cost.items():
            resources.subtract(resource, amount)
        
        # Repair building
        old_damage = building.damage_level
        building.repair(repair_amount)
        
        self.logger.info(f"Repaired {building_type.value} at {station_name}: {old_damage}% -> {building.damage_level}% damage")
        
        return True, f"Repaired {building_type.value} at {station_name} ({old_damage}% -> {building.damage_level}% damage)"
    
    def process_construction_turn(self, current_turn: int) -> List[str]:
        """
        Process construction projects for one turn
        
        Args:
            current_turn: Current game turn
            
        Returns:
            List of completion messages
        """
        completed_projects = []
        completion_messages = []
        
        for project in self.construction_projects:
            if project.advance_construction():
                # Construction complete
                station = self.metro_map.get_station(project.station_name)
                if station:
                    # Add building to station
                    infrastructure = Infrastructure(project.building_type, 1)
                    station.infrastructure[project.building_type] = infrastructure
                    
                    message = f"Construction complete: {project.building_type.value} at {project.station_name}"
                    completion_messages.append(message)
                    self.logger.info(message)
                
                completed_projects.append(project)
        
        # Remove completed projects
        for project in completed_projects:
            self.construction_projects.remove(project)
        
        return completion_messages
    
    def get_construction_projects(self) -> List[Dict[str, Any]]:
        """Get information about active construction projects"""
        projects = []
        for project in self.construction_projects:
            projects.append({
                "station": project.station_name,
                "building_type": project.building_type.value,
                "progress": project.get_progress(),
                "remaining_time": project.remaining_time,
                "total_time": project.construction_time
            })
        return projects
    
    def get_available_buildings(self, station_name: str, resources: ResourcePool) -> List[Dict[str, Any]]:
        """
        Get list of buildings that can be constructed at a station
        
        Args:
            station_name: Name of the station
            resources: Available resources
            
        Returns:
            List of building information dictionaries
        """
        available_buildings = []
        
        for building_type in BuildingType:
            can_construct, reason = self.can_construct_building(station_name, building_type, resources)
            
            # Get building info
            construction_cost = self.construction_costs.get(building_type, {})
            construction_time = self.construction_times.get(building_type, 3)
            population_req = self.population_requirements.get(building_type, 0)
            
            # Create temporary infrastructure to get specs
            temp_infrastructure = Infrastructure(building_type, 1)
            building_info = temp_infrastructure.get_info()
            
            available_buildings.append({
                "type": building_type.value,
                "name": building_info["name"],
                "description": building_info["description"],
                "can_construct": can_construct,
                "reason": reason if not can_construct else "Available",
                "construction_cost": construction_cost,
                "construction_time": construction_time,
                "population_requirement": population_req,
                "resource_output": building_info["resource_output"],
                "special_effects": building_info["special_effects"]
            })
        
        return available_buildings
    
    def get_station_specialization_bonus(self, station: Station) -> Dict[str, float]:
        """
        Calculate specialization bonuses based on station buildings
        
        Args:
            station: Station to analyze
            
        Returns:
            Dictionary of bonus multipliers
        """
        bonuses = {
            "food_production": 1.0,
            "water_production": 1.0,
            "scrap_production": 1.0,
            "medicine_production": 1.0,
            "defensive_bonus": 0,
            "trade_bonus": 0,
            "research_bonus": 0,
            "morale_bonus": 0
        }
        
        # Calculate bonuses from buildings
        for building_type, infrastructure in station.infrastructure.items():
            if not infrastructure.is_operational():
                continue
            
            special_effects = infrastructure.get_special_effects()
            
            # Apply building-specific bonuses
            if building_type == BuildingType.MUSHROOM_FARM:
                bonuses["food_production"] += 0.2 * infrastructure.efficiency_level
            elif building_type == BuildingType.WATER_FILTER:
                bonuses["water_production"] += 0.25 * infrastructure.efficiency_level
            elif building_type == BuildingType.SCRAP_WORKSHOP:
                bonuses["scrap_production"] += 0.3 * infrastructure.efficiency_level
            elif building_type == BuildingType.MED_BAY:
                bonuses["medicine_production"] += 0.4 * infrastructure.efficiency_level
            
            # Apply special effects
            for effect, value in special_effects.items():
                if effect in bonuses:
                    bonuses[effect] += value
        
        return bonuses
    
    def _get_station_building_capacity(self, station: Station) -> int:
        """Calculate maximum number of buildings for a station"""
        base_capacity = 3
        population_bonus = station.population // 50  # 1 extra building per 50 people
        return base_capacity + population_bonus
    
    def _get_building_prerequisites(self, building_type: BuildingType) -> List[BuildingType]:
        """Get prerequisite buildings for construction"""
        prerequisites = {
            BuildingType.MED_BAY: [BuildingType.WATER_FILTER],
            BuildingType.MARKET: [BuildingType.SCRAP_WORKSHOP],
            BuildingType.LIBRARY: [BuildingType.MED_BAY]
        }
        return prerequisites.get(building_type, [])
    
    def _calculate_repair_cost(self, building_type: BuildingType, repair_amount: int) -> Dict[str, int]:
        """Calculate cost to repair a building"""
        base_cost = self.construction_costs.get(building_type, {})
        repair_multiplier = (repair_amount / 100.0) * 0.5  # Repair costs 50% of construction per 100% damage
        
        repair_cost = {}
        for resource, amount in base_cost.items():
            repair_cost[resource] = max(1, int(amount * repair_multiplier))
        
        return repair_cost
    
    def get_building_maintenance_summary(self, faction_stations: List[Station]) -> Dict[str, int]:
        """
        Calculate total maintenance costs for all faction buildings
        
        Args:
            faction_stations: List of stations controlled by faction
            
        Returns:
            Dictionary of total maintenance costs
        """
        total_maintenance = {}
        
        for station in faction_stations:
            for infrastructure in station.infrastructure.values():
                if infrastructure.is_operational():
                    maintenance = infrastructure.get_maintenance_cost()
                    for resource, amount in maintenance.items():
                        total_maintenance[resource] = total_maintenance.get(resource, 0) + amount
        
        return total_maintenance