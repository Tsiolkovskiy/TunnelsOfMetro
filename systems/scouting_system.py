"""
Scouting System
Handles intelligence gathering, fog of war, and station reconnaissance
"""

import logging
import random
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass

from systems.metro_map import MetroMap
from data.station import Station
from data.tunnel import Tunnel, TunnelState


class IntelligenceLevel(Enum):
    """Levels of intelligence about a station"""
    UNKNOWN = "unknown"
    BASIC = "basic"
    DETAILED = "detailed"
    COMPLETE = "complete"


@dataclass
class StationIntelligence:
    """Intelligence data about a station"""
    station_name: str
    level: IntelligenceLevel
    last_updated: int  # Turn number
    
    # Basic intelligence (visible from adjacent stations)
    faction: Optional[str] = None
    
    # Detailed intelligence (requires scouting)
    population: Optional[int] = None
    morale: Optional[int] = None
    defensive_value: Optional[int] = None
    
    # Complete intelligence (requires multiple scouts or special units)
    resources: Optional[Dict[str, int]] = None
    infrastructure: Optional[List[str]] = None
    military_units: Optional[int] = None
    
    # Special intelligence
    special_traits: Optional[List[str]] = None
    recent_activities: Optional[List[str]] = None


class ScoutingSystem:
    """
    Complete scouting and intelligence system
    
    Features:
    - Fog of war mechanics
    - Progressive intelligence gathering
    - Scout unit management
    - Intelligence decay over time
    - Counter-intelligence detection
    """
    
    def __init__(self, metro_map: MetroMap):
        """
        Initialize scouting system
        
        Args:
            metro_map: MetroMap instance
        """
        self.metro_map = metro_map
        self.logger = logging.getLogger(__name__)
        
        # Intelligence database
        self.station_intelligence: Dict[str, StationIntelligence] = {}
        
        # Fog of war - stations that have been discovered
        self.discovered_stations: Set[str] = set()
        
        # Scouting costs and requirements
        self.scout_costs = {
            "fuel": 10,  # Base fuel cost
            "time": 1,   # Turns required
            "risk": 0.1  # Base risk of detection
        }
        
        # Intelligence decay settings
        self.intelligence_decay_turns = 5  # Turns before intelligence becomes stale
        
        self.logger.info("Scouting system initialized")
    
    def initialize_player_knowledge(self, player_faction: str):
        """
        Initialize player's starting knowledge
        
        Args:
            player_faction: Player's faction name
        """
        # Player knows about their own stations and adjacent ones
        for station_name, station in self.metro_map.stations.items():
            if station.controlling_faction == player_faction:
                # Complete knowledge of own stations
                self._set_station_intelligence(station_name, IntelligenceLevel.COMPLETE, 0)
                self.discovered_stations.add(station_name)
                
                # Basic knowledge of adjacent stations
                adjacent_stations = self.metro_map.get_adjacent_stations(station_name)
                for adj_station in adjacent_stations:
                    if adj_station not in self.station_intelligence:
                        self._set_station_intelligence(adj_station, IntelligenceLevel.BASIC, 0)
                        self.discovered_stations.add(adj_station)
        
        self.logger.info(f"Initialized knowledge for {player_faction}: {len(self.discovered_stations)} stations known")
    
    def execute_scout_action(self, origin_station: str, target_station: str, 
                           current_turn: int, player_resources) -> Dict[str, Any]:
        """
        Execute a scouting action
        
        Args:
            origin_station: Station sending the scout
            target_station: Station to scout
            current_turn: Current game turn
            player_resources: Player's resource pool
            
        Returns:
            Result dictionary with success status and intelligence gained
        """
        # Validate stations
        origin = self.metro_map.get_station(origin_station)
        target = self.metro_map.get_station(target_station)
        
        if not origin or not target:
            return {"success": False, "message": "Invalid station for scouting"}
        
        # Check if stations are adjacent or connected
        if not self._can_scout_target(origin_station, target_station):
            return {"success": False, "message": f"Cannot scout {target_station} from {origin_station} - too far"}
        
        # Check resource costs
        fuel_cost = self._calculate_scout_cost(origin_station, target_station)
        if not player_resources.has_sufficient("clean_water", fuel_cost):  # Using clean_water as fuel
            return {"success": False, "message": f"Insufficient fuel for scouting (need {fuel_cost})"}
        
        # Consume resources
        player_resources.subtract("clean_water", fuel_cost)
        
        # Execute scouting
        result = self._perform_scouting(origin_station, target_station, current_turn)
        
        # Add to discovered stations
        self.discovered_stations.add(target_station)
        
        return result
    
    def _can_scout_target(self, origin: str, target: str) -> bool:
        """Check if target can be scouted from origin"""
        # Can scout adjacent stations
        adjacent = self.metro_map.get_adjacent_stations(origin)
        if target in adjacent:
            return True
        
        # Can scout stations within 2 hops if path is clear
        reachable = self.metro_map.find_all_paths_within_range(origin, 3, "scout")
        return target in reachable
    
    def _calculate_scout_cost(self, origin: str, target: str) -> int:
        """Calculate fuel cost for scouting"""
        base_cost = self.scout_costs["fuel"]
        
        # Check if target is adjacent
        adjacent = self.metro_map.get_adjacent_stations(origin)
        if target in adjacent:
            return base_cost
        
        # Calculate path cost for distant targets
        path = self.metro_map.find_path(origin, target, "scout")
        if path:
            path_length = len(path) - 1  # Number of hops
            return base_cost + (path_length * 5)  # Extra cost per hop
        
        return base_cost * 2  # Default higher cost
    
    def _perform_scouting(self, origin: str, target: str, current_turn: int) -> Dict[str, Any]:
        """Perform the actual scouting operation"""
        target_station = self.metro_map.get_station(target)
        if not target_station:
            return {"success": False, "message": "Target station not found"}
        
        # Determine success chance
        success_chance = self._calculate_success_chance(origin, target)
        
        if random.random() > success_chance:
            return {"success": False, "message": f"Scouting mission to {target} failed - scout did not return"}
        
        # Determine intelligence level gained
        current_intel = self.station_intelligence.get(target)
        new_level = self._determine_intelligence_gain(current_intel, success_chance)
        
        # Update intelligence
        intelligence = self._gather_intelligence(target_station, new_level, current_turn)
        self.station_intelligence[target] = intelligence
        
        # Create result message
        message = self._create_scout_report(intelligence)
        
        return {
            "success": True,
            "message": message,
            "intelligence": intelligence,
            "target": target
        }
    
    def _calculate_success_chance(self, origin: str, target: str) -> float:
        """Calculate chance of successful scouting"""
        base_chance = 0.8  # 80% base success rate
        
        # Check tunnel conditions
        path = self.metro_map.find_path(origin, target, "scout")
        if path:
            for i in range(len(path) - 1):
                tunnel = self.metro_map.get_tunnel(path[i], path[i + 1])
                if tunnel:
                    if tunnel.state == TunnelState.HAZARDOUS:
                        base_chance -= 0.1
                    elif tunnel.state == TunnelState.INFESTED:
                        base_chance -= 0.2
                    elif tunnel.state == TunnelState.ANOMALOUS:
                        base_chance -= 0.3
                    elif tunnel.state == TunnelState.COLLAPSED:
                        base_chance = 0.0  # Cannot scout through collapsed tunnels
        
        # Target station factors
        target_station = self.metro_map.get_station(target)
        if target_station:
            # Hostile factions are harder to scout
            if target_station.controlling_faction in ["Fourth Reich", "Red Line"]:
                base_chance -= 0.1
            
            # High defensive value makes scouting harder
            if target_station.defensive_value > 20:
                base_chance -= 0.1
        
        return max(0.1, min(0.95, base_chance))  # Clamp between 10% and 95%
    
    def _determine_intelligence_gain(self, current_intel: Optional[StationIntelligence], 
                                   success_chance: float) -> IntelligenceLevel:
        """Determine what level of intelligence is gained"""
        if not current_intel or current_intel.level == IntelligenceLevel.UNKNOWN:
            return IntelligenceLevel.BASIC
        
        # Higher success chance allows for better intelligence
        if success_chance > 0.8 and current_intel.level == IntelligenceLevel.BASIC:
            return IntelligenceLevel.DETAILED
        elif success_chance > 0.9 and current_intel.level == IntelligenceLevel.DETAILED:
            return IntelligenceLevel.COMPLETE
        
        # Otherwise, refresh existing intelligence
        return current_intel.level
    
    def _gather_intelligence(self, station: Station, level: IntelligenceLevel, 
                           current_turn: int) -> StationIntelligence:
        """Gather intelligence about a station"""
        intel = StationIntelligence(
            station_name=station.name,
            level=level,
            last_updated=current_turn
        )
        
        # Basic intelligence - always available
        intel.faction = station.controlling_faction
        
        if level in [IntelligenceLevel.DETAILED, IntelligenceLevel.COMPLETE]:
            # Detailed intelligence
            intel.population = station.population
            intel.morale = station.morale
            intel.defensive_value = station.defensive_value
            
            # Add some uncertainty to make it realistic
            if level == IntelligenceLevel.DETAILED:
                intel.population = int(intel.population * (0.9 + random.random() * 0.2))
                intel.morale = max(0, min(100, intel.morale + random.randint(-10, 10)))
        
        if level == IntelligenceLevel.COMPLETE:
            # Complete intelligence
            intel.resources = {
                "food": station.resources.food,
                "clean_water": station.resources.clean_water,
                "scrap": station.resources.scrap,
                "medicine": station.resources.medicine,
                "mgr_rounds": station.resources.mgr_rounds
            }
            
            intel.infrastructure = [building.value for building in station.infrastructure.keys()]
            intel.special_traits = station.special_traits.copy()
            
            # Estimate military presence (simplified)
            intel.military_units = len(station.infrastructure) * 2  # Rough estimate
        
        return intel
    
    def _create_scout_report(self, intelligence: StationIntelligence) -> str:
        """Create a readable scout report"""
        station_name = intelligence.station_name
        faction = intelligence.faction or "Unknown"
        
        if intelligence.level == IntelligenceLevel.BASIC:
            return f"Scouted {station_name}: Controlled by {faction}"
        
        elif intelligence.level == IntelligenceLevel.DETAILED:
            pop = intelligence.population or 0
            morale = intelligence.morale or 0
            defense = intelligence.defensive_value or 0
            return (f"Scouted {station_name}: {faction} faction, "
                   f"~{pop} population, {morale}% morale, defense: {defense}")
        
        elif intelligence.level == IntelligenceLevel.COMPLETE:
            pop = intelligence.population or 0
            resources = intelligence.resources or {}
            buildings = len(intelligence.infrastructure or [])
            return (f"Complete intel on {station_name}: {faction}, {pop} people, "
                   f"{buildings} buildings, {resources.get('mgr_rounds', 0)} MGR")
        
        return f"Scouted {station_name}: No useful intelligence gathered"
    
    def _set_station_intelligence(self, station_name: str, level: IntelligenceLevel, turn: int):
        """Set intelligence level for a station"""
        station = self.metro_map.get_station(station_name)
        if station:
            self.station_intelligence[station_name] = self._gather_intelligence(station, level, turn)
    
    def get_station_intelligence(self, station_name: str) -> Optional[StationIntelligence]:
        """Get intelligence about a station"""
        return self.station_intelligence.get(station_name)
    
    def is_station_discovered(self, station_name: str) -> bool:
        """Check if a station has been discovered"""
        return station_name in self.discovered_stations
    
    def get_visible_stations(self) -> Set[str]:
        """Get all stations visible to the player"""
        return self.discovered_stations.copy()
    
    def update_intelligence_decay(self, current_turn: int):
        """Update intelligence decay over time"""
        for station_name, intel in self.station_intelligence.items():
            turns_old = current_turn - intel.last_updated
            
            if turns_old > self.intelligence_decay_turns:
                # Degrade intelligence level
                if intel.level == IntelligenceLevel.COMPLETE:
                    intel.level = IntelligenceLevel.DETAILED
                elif intel.level == IntelligenceLevel.DETAILED:
                    intel.level = IntelligenceLevel.BASIC
                
                intel.last_updated = current_turn
                self.logger.debug(f"Intelligence on {station_name} degraded to {intel.level.value}")
    
    def reveal_adjacent_stations(self, station_name: str, current_turn: int):
        """Reveal stations adjacent to a controlled station"""
        adjacent = self.metro_map.get_adjacent_stations(station_name)
        
        for adj_station in adjacent:
            if adj_station not in self.discovered_stations:
                self.discovered_stations.add(adj_station)
                
                # Add basic intelligence
                if adj_station not in self.station_intelligence:
                    self._set_station_intelligence(adj_station, IntelligenceLevel.BASIC, current_turn)
    
    def get_scouting_targets(self, origin_station: str) -> List[str]:
        """Get list of valid scouting targets from a station"""
        targets = []
        
        # Get all stations within scouting range
        reachable = self.metro_map.find_all_paths_within_range(origin_station, 3, "scout")
        
        for station_name in reachable:
            if station_name != origin_station:
                # Check if we can gain new intelligence
                current_intel = self.station_intelligence.get(station_name)
                if not current_intel or current_intel.level != IntelligenceLevel.COMPLETE:
                    targets.append(station_name)
        
        return targets
    
    def get_intelligence_summary(self) -> Dict[str, Any]:
        """Get summary of current intelligence"""
        summary = {
            "discovered_stations": len(self.discovered_stations),
            "intelligence_levels": {
                "unknown": 0,
                "basic": 0,
                "detailed": 0,
                "complete": 0
            },
            "recent_scouts": []
        }
        
        for intel in self.station_intelligence.values():
            summary["intelligence_levels"][intel.level.value] += 1
        
        return summary
    
    def create_fog_of_war_filter(self) -> Set[str]:
        """Create filter for fog of war rendering"""
        return self.discovered_stations
    
    def process_turn(self, current_turn: int, player_faction: str):
        """Process end-of-turn scouting updates"""
        # Update intelligence decay
        self.update_intelligence_decay(current_turn)
        
        # Reveal adjacent stations for controlled stations
        for station_name, station in self.metro_map.stations.items():
            if station.controlling_faction == player_faction:
                self.reveal_adjacent_stations(station_name, current_turn)