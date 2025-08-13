"""
Resource Production and Consumption System
Manages complex resource flows, production chains, and consumption mechanics
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass

from data.station import Station
from data.resources import ResourcePool
from data.infrastructure import BuildingType
from systems.metro_map import MetroMap


class ProductionModifier(Enum):
    """Types of production modifiers"""
    EFFICIENCY = "efficiency"
    MORALE = "morale"
    POPULATION = "population"
    INFRASTRUCTURE = "infrastructure"
    SPECIALIZATION = "specialization"
    SEASONAL = "seasonal"
    EVENT = "event"


@dataclass
class ProductionReport:
    """Report of resource production for a station"""
    station_name: str
    base_production: Dict[str, int]
    modified_production: Dict[str, int]
    modifiers_applied: Dict[str, float]
    consumption: Dict[str, int]
    net_production: Dict[str, int]
    efficiency_rating: float


@dataclass
class ConsumptionRequirement:
    """Defines resource consumption requirements"""
    resource_type: str
    base_amount: int
    per_population: float = 0.0
    per_building: float = 0.0
    priority: int = 1  # 1=critical, 2=important, 3=optional


class ResourceProductionSystem:
    """
    Comprehensive resource production and consumption system
    
    Features:
    - Turn-based resource generation from station infrastructure
    - Population-based resource consumption
    - Efficiency modifiers based on station morale and upgrades
    """
    
    def __init__(self, metro_map: MetroMap):
        """Initialize resource production system"""
        self.metro_map = metro_map
        self.logger = logging.getLogger(__name__)
        
        # Base consumption requirements per population
        self.base_consumption = {
            "food": ConsumptionRequirement("food", 0, 0.5, 0, 1),
            "clean_water": ConsumptionRequirement("clean_water", 0, 0.3, 0, 1),
            "medicine": ConsumptionRequirement("medicine", 0, 0.1, 0, 2),
        }
        
        # Production efficiency modifiers
        self.morale_efficiency = {
            (0, 20): 0.3, (21, 40): 0.6, (41, 60): 0.8, (61, 80): 1.0, (81, 100): 1.2
        }
        
        # Seasonal modifiers
        self.seasonal_modifiers = {
            "spring": {"food": 1.1, "clean_water": 1.0, "scrap": 1.0, "medicine": 1.0},
            "summer": {"food": 1.2, "clean_water": 0.9, "scrap": 1.1, "medicine": 1.0},
            "autumn": {"food": 1.0, "clean_water": 1.0, "scrap": 1.2, "medicine": 1.1},
            "winter": {"food": 0.8, "clean_water": 1.1, "scrap": 0.9, "medicine": 0.9}
        }
        
        # Global production modifiers
        self.global_modifiers: Dict[str, float] = {}
        
        # Production history
        self.production_history: List[Dict[str, Any]] = []
        
        self.logger.info("Resource production system initialized")
    
    def calculate_station_production(self, station: Station, current_turn: int) -> ProductionReport:
        """Calculate comprehensive resource production for a station"""
        # Base production from infrastructure
        base_production = self._calculate_base_production(station)
        
        # Calculate all modifiers
        modifiers = self._calculate_production_modifiers(station, current_turn)
        
        # Apply modifiers to base production
        modified_production = {}
        for resource, base_amount in base_production.items():
            modifier = modifiers.get(resource, 1.0)
            modified_production[resource] = max(0, int(base_amount * modifier))
        
        # Calculate consumption
        consumption = self._calculate_station_consumption(station)
        
        # Calculate net production
        net_production = {}
        all_resources = set(modified_production.keys()) | set(consumption.keys())
        
        for resource in all_resources:
            production = modified_production.get(resource, 0)
            consumed = consumption.get(resource, 0)
            net_production[resource] = production - consumed
        
        # Calculate efficiency rating
        efficiency_rating = self._calculate_efficiency_rating(station, modifiers)
        
        return ProductionReport(
            station_name=station.name,
            base_production=base_production,
            modified_production=modified_production,
            modifiers_applied=modifiers,
            consumption=consumption,
            net_production=net_production,
            efficiency_rating=efficiency_rating
        )
    
    def process_faction_production(self, faction_stations: List[Station], 
                                 faction_resources: ResourcePool, current_turn: int) -> List[ProductionReport]:
        """Process resource production for all faction stations"""
        reports = []
        total_net_production = {}
        
        # Calculate production for each station
        for station in faction_stations:
            report = self.calculate_station_production(station, current_turn)
            reports.append(report)
            
            # Accumulate total production
            for resource, amount in report.net_production.items():
                total_net_production[resource] = total_net_production.get(resource, 0) + amount
        
        # Apply net production to faction resources
        for resource, amount in total_net_production.items():
            if amount > 0:
                faction_resources.add(resource, amount)
            elif amount < 0:
                # Consumption exceeds production
                shortage = abs(amount)
                available = getattr(faction_resources, resource, 0)
                consumed = min(shortage, available)
                
                if consumed > 0:
                    faction_resources.subtract(resource, consumed)
                
                # Apply shortage penalties if consumption wasn't fully met
                if consumed < shortage:
                    shortage_amount = shortage - consumed
                    self._apply_resource_shortage(faction_stations, resource, shortage_amount)
        
        return reports
    
    def _calculate_base_production(self, station: Station) -> Dict[str, int]:
        """Calculate base resource production from station infrastructure"""
        base_production = {}
        
        # Production from buildings
        for building_type, infrastructure in station.infrastructure.items():
            if infrastructure.is_operational():
                building_output = infrastructure.get_resource_output()
                for resource, amount in building_output.items():
                    base_production[resource] = base_production.get(resource, 0) + amount
        
        # Base production from population (scavenging, basic crafting)
        population_production = {
            "scrap": max(1, station.population // 50),
            "food": max(1, station.population // 100)
        }
        
        for resource, amount in population_production.items():
            base_production[resource] = base_production.get(resource, 0) + amount
        
        return base_production
    
    def _calculate_production_modifiers(self, station: Station, current_turn: int) -> Dict[str, float]:
        """Calculate all production modifiers for a station"""
        modifiers = {}
        base_resources = ["food", "clean_water", "scrap", "medicine"]
        
        # Base modifier
        for resource in base_resources:
            modifiers[resource] = 1.0
        
        # Morale modifier
        morale_modifier = self._get_morale_modifier(station.morale)
        for resource in base_resources:
            modifiers[resource] *= morale_modifier
        
        # Seasonal modifiers
        season = self._get_current_season(current_turn)
        seasonal_mods = self.seasonal_modifiers.get(season, {})
        for resource, seasonal_mod in seasonal_mods.items():
            modifiers[resource] = modifiers.get(resource, 1.0) * seasonal_mod
        
        # Global modifiers
        for resource, global_mod in self.global_modifiers.items():
            modifiers[resource] = modifiers.get(resource, 1.0) * global_mod
        
        # Population efficiency
        population_efficiency = min(1.5, 1.0 + (station.population / 500))
        for resource in base_resources:
            modifiers[resource] *= population_efficiency
        
        return modifiers
    
    def _calculate_station_consumption(self, station: Station) -> Dict[str, int]:
        """Calculate total resource consumption for a station"""
        consumption = {}
        
        # Population consumption
        for resource, requirement in self.base_consumption.items():
            base_amount = requirement.base_amount
            per_pop_amount = requirement.per_population * station.population
            total_consumption = int(base_amount + per_pop_amount)
            
            if total_consumption > 0:
                consumption[resource] = total_consumption
        
        # Building maintenance consumption
        for building_type, infrastructure in station.infrastructure.items():
            if infrastructure.is_operational():
                maintenance_cost = infrastructure.get_maintenance_cost()
                for resource, amount in maintenance_cost.items():
                    consumption[resource] = consumption.get(resource, 0) + amount
        
        return consumption
    
    def _get_morale_modifier(self, morale: int) -> float:
        """Get production modifier based on station morale"""
        for (min_morale, max_morale), modifier in self.morale_efficiency.items():
            if min_morale <= morale <= max_morale:
                return modifier
        return 1.0
    
    def _get_current_season(self, turn: int) -> str:
        """Determine current season based on turn number"""
        season_cycle = turn % 12
        if season_cycle < 3:
            return "winter"
        elif season_cycle < 6:
            return "spring"
        elif season_cycle < 9:
            return "summer"
        else:
            return "autumn"
    
    def _calculate_efficiency_rating(self, station: Station, modifiers: Dict[str, float]) -> float:
        """Calculate overall efficiency rating for the station"""
        if not modifiers:
            return 1.0
        
        total_modifier = sum(modifiers.values())
        avg_modifier = total_modifier / len(modifiers)
        
        infrastructure_bonus = len(station.infrastructure) * 0.05
        population_factor = min(1.2, station.population / 200)
        
        efficiency = avg_modifier * (1.0 + infrastructure_bonus) * population_factor
        return round(efficiency, 2)
    
    def _apply_resource_shortage(self, stations: List[Station], resource: str, shortage_amount: int):
        """Apply penalties for resource shortages"""
        self.logger.warning(f"Resource shortage: {shortage_amount} {resource}")
        
        penalty_per_station = shortage_amount / len(stations)
        
        for station in stations:
            morale_penalty = min(20, int(penalty_per_station * 2))
            station.morale = max(0, station.morale - morale_penalty)
            
            if resource == "food":
                population_loss = min(station.population // 10, int(penalty_per_station))
                station.population = max(10, station.population - population_loss)
    
    def set_global_modifier(self, resource: str, modifier: float, duration: int = -1):
        """Set a global production modifier"""
        self.global_modifiers[resource] = modifier
        self.logger.info(f"Set global {resource} production modifier to {modifier}")
    
    def get_production_summary(self, faction_stations: List[Station], current_turn: int) -> Dict[str, Any]:
        """Get comprehensive production summary for a faction"""
        total_production = {}
        total_consumption = {}
        total_net = {}
        station_count = len(faction_stations)
        avg_efficiency = 0
        
        for station in faction_stations:
            report = self.calculate_station_production(station, current_turn)
            
            for resource, amount in report.modified_production.items():
                total_production[resource] = total_production.get(resource, 0) + amount
            
            for resource, amount in report.consumption.items():
                total_consumption[resource] = total_consumption.get(resource, 0) + amount
            
            for resource, amount in report.net_production.items():
                total_net[resource] = total_net.get(resource, 0) + amount
            
            avg_efficiency += report.efficiency_rating
        
        if station_count > 0:
            avg_efficiency /= station_count
        
        return {
            "total_production": total_production,
            "total_consumption": total_consumption,
            "net_production": total_net,
            "station_count": station_count,
            "average_efficiency": round(avg_efficiency, 2),
            "current_season": self._get_current_season(current_turn),
            "global_modifiers": self.global_modifiers.copy()
        }
    
    def get_resource_forecast(self, faction_stations: List[Station], 
                            current_resources: ResourcePool, turns_ahead: int = 3) -> Dict[str, List[int]]:
        """Forecast resource levels for the next few turns"""
        forecast = {}
        current_turn = len(self.production_history) + 1
        
        # Initialize forecast with current resources
        for resource in ["food", "clean_water", "scrap", "medicine", "mgr_rounds"]:
            current_amount = getattr(current_resources, resource, 0)
            forecast[resource] = [current_amount]
        
        # Calculate forecast for each turn
        for turn_offset in range(1, turns_ahead + 1):
            future_turn = current_turn + turn_offset
            
            total_net = {}
            for station in faction_stations:
                report = self.calculate_station_production(station, future_turn)
                for resource, amount in report.net_production.items():
                    total_net[resource] = total_net.get(resource, 0) + amount
            
            # Apply net production to forecast
            for resource in forecast:
                previous_amount = forecast[resource][-1]
                net_change = total_net.get(resource, 0)
                new_amount = max(0, previous_amount + net_change)
                forecast[resource].append(new_amount)
        
        return forecast