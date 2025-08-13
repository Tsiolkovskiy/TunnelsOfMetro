"""
Game State Management System
Manages the overall game state and provides data to UI components
"""

import logging
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass

from data.resources import ResourcePool
from data.military_unit import MilitaryManager, UnitType
from data.infrastructure import BuildingType
from systems.metro_map import MetroMap
from systems.scouting_system import ScoutingSystem
from systems.trade_system import TradeSystem
from systems.combat_system import CombatSystem, AttackType
from systems.diplomacy_system import DiplomacySystem, DiplomaticAction
from systems.building_system import BuildingSystem
from systems.resource_production_system import ResourceProductionSystem
from systems.event_system import EventSystem
from systems.victory_system import VictorySystem, VictoryType
from systems.ai_system import AISystem


@dataclass
class PlayerState:
    """Player state information"""
    faction: str = "Rangers"
    resources: ResourcePool = None
    controlled_stations: List[str] = None
    
    def __post_init__(self):
        if self.resources is None:
            self.resources = ResourcePool()
        if self.controlled_stations is None:
            self.controlled_stations = []


class GameStateManager:
    """
    Manages the complete game state
    
    Provides centralized access to:
    - Player state and resources
    - Turn information
    - Map state
    - Game statistics
    """
    
    def __init__(self, metro_map: MetroMap):
        """
        Initialize game state manager
        
        Args:
            metro_map: MetroMap instance
        """
        self.logger = logging.getLogger(__name__)
        
        # Core game state
        self.metro_map = metro_map
        self.current_turn = 1
        self.game_phase = "planning"  # planning, action, resolution
        
        # Game systems
        self.scouting_system = ScoutingSystem(metro_map)
        self.trade_system = TradeSystem(metro_map)
        self.combat_system = CombatSystem(metro_map)
        self.diplomacy_system = DiplomacySystem(metro_map)
        self.military_manager = MilitaryManager("Rangers")
        self.building_system = BuildingSystem(metro_map)
        self.resource_production_system = ResourceProductionSystem(metro_map)
        self.event_system = EventSystem(metro_map)
        self.victory_system = VictorySystem(metro_map)
        self.ai_system = AISystem(metro_map)
        
        # Connect systems
        self.combat_system.diplomacy_system = self.diplomacy_system
        self.combat_system.register_military_manager("Rangers", self.military_manager)
        
        # Player state
        self.player = PlayerState()
        
        # Initialize player resources
        self._initialize_player_resources()
        
        # Game statistics
        self.statistics = {
            "stations_controlled": 0,
            "total_population": 0,
            "battles_won": 0,
            "trades_completed": 0,
            "diplomatic_agreements": 0,
            "units_recruited": 0,
            "total_military_strength": 0
        }
        
        self.logger.info("Game state manager initialized")
    
    def _initialize_player_resources(self):
        """Initialize player starting resources"""
        # Starting resources for Rangers faction
        starting_resources = {
            "food": 100,
            "clean_water": 50,
            "scrap": 75,
            "medicine": 25,
            "mgr_rounds": 50
        }
        
        for resource, amount in starting_resources.items():
            self.player.resources.set(resource, amount)
        
        # Find player-controlled stations
        self.player.controlled_stations = [
            station.name for station in self.metro_map.stations.values()
            if station.controlling_faction == self.player.faction
        ]
        
        # Initialize scouting system with player knowledge
        self.scouting_system.initialize_player_knowledge(self.player.faction)
        
        self.logger.info(f"Player initialized with {len(self.player.controlled_stations)} stations")
    
    def get_game_state(self) -> Dict[str, Any]:
        """
        Get complete game state for UI components
        
        Returns:
            Dictionary containing all game state information
        """
        return {
            "current_turn": self.current_turn,
            "game_phase": self.game_phase,
            "player_faction": self.player.faction,
            "player_resources": self.player.resources,
            "controlled_stations": self.player.controlled_stations.copy(),
            "statistics": self.statistics.copy(),
            "map_stats": self.metro_map.get_map_statistics(),
            "military_maintenance_cost": self.military_manager.calculate_total_maintenance_cost(),
            "military_unit_summary": self.military_manager.get_unit_summary(),
            "building_maintenance_cost": self.get_building_maintenance_cost(),
            "construction_projects": self.get_construction_projects(),
            "production_summary": self.get_production_summary(),
            "production_reports": self.get_production_reports(),
            "resource_forecast": self.get_resource_forecast(),
            "triggered_events": self.get_triggered_events(),
            "active_events": self.get_active_events(),
            "event_statistics": self.get_event_statistics(),
            "victory_status": self.get_victory_status(),
            "victory_progress": self.get_victory_progress_summary(),
            "closest_victory": self.get_closest_victory(),
            "game_ended": self.is_game_ended(),
            "active_events": self.get_active_events(),
            "recent_events": self.get_recent_events(),
            "triggered_events": self.get_triggered_events(),
            "victory_progress": self.get_victory_progress_summary(),
            "victory_status": self.get_victory_status(),
            "closest_victory": self.get_closest_victory(),
            "ai_statistics": self.get_ai_statistics()
        }
    
    def advance_turn(self):
        """Advance to the next turn"""
        self.current_turn += 1
        
        # Process turn-based updates
        self._process_resource_generation()
        self._process_station_updates()
        self._update_statistics()
        
        # Process scouting system
        self.scouting_system.process_turn(self.current_turn, self.player.faction)
        
        # Process trade system
        trade_events = self.trade_system.process_turn(self.current_turn, self.player.resources)
        for event in trade_events:
            self.logger.info(f"Trade event: {event.get('message', 'Unknown event')}")
        
        # Process diplomacy system
        self.diplomacy_system.process_turn(self.current_turn)
        
        # Process military maintenance
        self._process_military_maintenance()
        
        # Process building construction
        self._process_building_construction()
        
        # Process building maintenance
        self._process_building_maintenance()
        
        # Process events
        self._process_turn_events()
        
        # Process AI faction actions
        self._process_ai_turn()
        
        # Check victory conditions
        self._check_victory_conditions()
        
        self.logger.info(f"Advanced to turn {self.current_turn}")
    
    def _process_resource_generation(self):
        """Process comprehensive resource generation and consumption"""
        # Get all player-controlled stations
        player_stations = [
            self.metro_map.get_station(station_name) 
            for station_name in self.player.controlled_stations
        ]
        player_stations = [s for s in player_stations if s is not None]
        
        # Process faction production using the comprehensive system
        production_reports = self.resource_production_system.process_faction_production(
            player_stations, self.player.resources, self.current_turn
        )
        
        # Log production summary
        for report in production_reports:
            if any(amount != 0 for amount in report.net_production.values()):
                net_summary = ", ".join(f"{amount:+d} {resource}" 
                                      for resource, amount in report.net_production.items() 
                                      if amount != 0)
                self.logger.debug(f"{report.station_name} production: {net_summary} (efficiency: {report.efficiency_rating:.1f})")
        
        # Store production reports for UI display
        self._last_production_reports = production_reports
    

    
    def _process_military_maintenance(self):
        """Process military unit maintenance costs"""
        maintenance_cost = self.military_manager.calculate_total_maintenance_cost()
        
        # Apply maintenance costs
        for resource, amount in maintenance_cost.items():
            if not self.player.resources.subtract(resource, amount):
                self.logger.warning(f"Insufficient {resource} for military maintenance!")
                # Apply penalties to military units
                self._apply_military_maintenance_penalty(resource)
        
        # Remove destroyed units
        self.military_manager.remove_destroyed_units()
    
    def _process_building_construction(self):
        """Process building construction projects"""
        completion_messages = self.building_system.process_construction_turn(self.current_turn)
        for message in completion_messages:
            self.logger.info(f"Construction complete: {message}")
    
    def _process_building_maintenance(self):
        """Process building maintenance costs"""
        # Get all player-controlled stations
        player_stations = [
            self.metro_map.get_station(station_name) 
            for station_name in self.player.controlled_stations
        ]
        player_stations = [s for s in player_stations if s is not None]
        
        # Calculate total maintenance cost
        maintenance_cost = self.building_system.get_building_maintenance_summary(player_stations)
        
        # Apply maintenance costs
        for resource, amount in maintenance_cost.items():
            if not self.player.resources.subtract(resource, amount):
                self.logger.warning(f"Insufficient {resource} for building maintenance!")
                # Apply penalties for lack of maintenance
                self._apply_building_maintenance_penalty(resource)
    
    def _apply_building_maintenance_penalty(self, resource: str):
        """Apply penalties for insufficient building maintenance"""
        # Damage buildings that require this resource
        for station_name in self.player.controlled_stations:
            station = self.metro_map.get_station(station_name)
            if station:
                for infrastructure in station.infrastructure.values():
                    maintenance = infrastructure.get_maintenance_cost()
                    if resource in maintenance:
                        # Apply damage to buildings that need this resource
                        infrastructure.apply_damage(10)
                        self.logger.warning(f"Building {infrastructure.building_type.value} at {station_name} damaged due to lack of {resource}")
    
    def _process_turn_events(self):
        """Process events for the current turn"""
        # Get all player-controlled stations
        player_stations = [
            self.metro_map.get_station(station_name) 
            for station_name in self.player.controlled_stations
        ]
        player_stations = [s for s in player_stations if s is not None]
        
        # Process events
        triggered_events = self.event_system.process_turn_events(self.current_turn, player_stations)
        
        # Store triggered events for UI display
        self._last_triggered_events = triggered_events
        
        # Log triggered events
        for event in triggered_events:
            self.logger.info(f"Event triggered: {event['title']} ({event['severity']})")
            
            # Auto-resolve some events if no choices or simple effects
            if not event['choices']:
                self._auto_resolve_event(event, player_stations)
    
    def _process_turn_events(self):
        """Process events for the current turn"""
        # Get player-controlled stations
        player_stations = [
            self.metro_map.get_station(station_name) 
            for station_name in self.player.controlled_stations
        ]
        player_stations = [s for s in player_stations if s is not None]
        
        # Process events
        triggered_events = self.event_system.process_turn_events(self.current_turn, player_stations)
        
        # Store triggered events for UI display
        self._last_triggered_events = triggered_events
        
        # Log significant events
        for event in triggered_events:
            if event["severity"] in ["major", "catastrophic"]:
                self.logger.warning(f"Major event: {event['title']} at {event.get('target', 'global')}")
            else:
                self.logger.info(f"Event: {event['title']}")
    
    def _apply_military_maintenance_penalty(self, resource: str):
        """Apply penalties for insufficient military maintenance"""
        # Reduce morale of all units
        for unit in self.military_manager.units:
            if unit.is_active:
                unit.modify_morale(-15)
                if unit.morale <= 20:
                    # Unit may desert or become inactive
                    if unit.morale <= 10:
                        unit.is_active = False
                        self.logger.warning(f"{unit.unit_type.value} unit deserted due to lack of {resource}")
    
    def _process_station_updates(self):
        """Process turn-based station updates"""
        for station_name in self.player.controlled_stations:
            station = self.metro_map.get_station(station_name)
            if station:
                station.process_turn()
    
    def _update_statistics(self):
        """Update game statistics"""
        self.statistics["stations_controlled"] = len(self.player.controlled_stations)
        
        # Calculate total population in controlled stations
        total_population = 0
        for station_name in self.player.controlled_stations:
            station = self.metro_map.get_station(station_name)
            if station:
                total_population += station.population
        
        self.statistics["total_population"] = total_population
        
        # Update military statistics
        self.statistics["total_military_strength"] = sum(
            unit.calculate_combat_strength() for unit in self.military_manager.units if unit.is_active
        )
    
    def execute_action(self, action: str, origin: str, target: str = None) -> Dict[str, Any]:
        """
        Execute a game action
        
        Args:
            action: Action to execute
            origin: Origin station
            target: Target station (if applicable)
            
        Returns:
            Result dictionary with success status and message
        """
        origin_station = self.metro_map.get_station(origin)
        if not origin_station:
            return {"success": False, "message": f"Station {origin} not found"}
        
        # Route to appropriate action handler
        if action == "scout":
            return self._execute_scout_action(origin, target)
        elif action == "trade":
            return self._execute_trade_action(origin, target)
        elif action == "attack":
            return self._execute_attack_action(origin, target)
        elif action == "diplomacy":
            return self._execute_diplomacy_action(origin, target)
        elif action == "fortify":
            return self._execute_fortify_action(origin)
        elif action == "recruit":
            return self._execute_recruit_action(origin)
        elif action == "recruit_unit":
            # For specific unit recruitment with unit type parameter
            return self._execute_recruit_specific_unit_action(origin, target)
        elif action == "develop":
            return self._execute_develop_action(origin)
        elif action == "construct":
            return self._execute_construct_action(origin, target)
        elif action == "upgrade":
            return self._execute_upgrade_action(origin, target)
        elif action == "repair":
            return self._execute_repair_action(origin, target)
        elif action == "resolve_event":
            return self._execute_resolve_event_action(origin, target)
        else:
            return {"success": False, "message": f"Unknown action: {action}"}
    
    def _execute_scout_action(self, origin: str, target: str) -> Dict[str, Any]:
        """Execute scout action"""
        if not target:
            # If no target specified, show available targets
            targets = self.scouting_system.get_scouting_targets(origin)
            if targets:
                return {"success": False, "message": f"Select target to scout: {', '.join(targets[:5])}"}
            else:
                return {"success": False, "message": "No valid scouting targets available"}
        
        # Execute scouting through scouting system
        result = self.scouting_system.execute_scout_action(
            origin, target, self.current_turn, self.player.resources
        )
        
        return result
    
    def _execute_trade_action(self, origin: str, target: str) -> Dict[str, Any]:
        """Execute trade action"""
        if not target:
            # Show available trade opportunities
            opportunities = self.trade_system.get_trade_opportunities(origin)
            if opportunities:
                targets = [opp["target"] for opp in opportunities[:3]]
                return {"success": False, "message": f"Select trade target: {', '.join(targets)}"}
            else:
                return {"success": False, "message": "No trade opportunities available"}
        
        # Execute trade through trade system
        result = self.trade_system.execute_trade(origin, target, self.player.resources, self.current_turn)
        
        if result["success"]:
            self.statistics["trades_completed"] += 1
        
        return result
    
    def _execute_attack_action(self, origin: str, target: str) -> Dict[str, Any]:
        """Execute attack action"""
        if not target:
            # Show potential attack targets
            hostile_targets = []
            for station_name, station in self.metro_map.stations.items():
                if station.controlling_faction != self.player.faction:
                    can_attack, _ = self.combat_system.can_attack(self.player.faction, station_name)
                    if can_attack:
                        # Check if within attack range
                        path = self.metro_map.find_path(origin, station_name, "military")
                        if path and len(path) <= 5:  # Within 5 stations
                            hostile_targets.append(station_name)
            
            if hostile_targets:
                return {"success": False, "message": f"Select attack target: {', '.join(hostile_targets[:3])}"}
            else:
                return {"success": False, "message": "No valid attack targets available"}
        
        # Execute attack through combat system
        result = self.combat_system.execute_attack(
            origin, target, self.player.faction, self.player.resources, 
            self.current_turn, AttackType.ASSAULT
        )
        
        # Update controlled stations if territory changed
        if result.get("territory_changed"):
            if target not in self.player.controlled_stations:
                self.player.controlled_stations.append(target)
            self.statistics["battles_won"] += 1
        
        return result
    
    def _execute_diplomacy_action(self, origin: str, target: str) -> Dict[str, Any]:
        """Execute diplomacy action"""
        if not target:
            # Show available diplomatic targets
            diplomatic_targets = []
            for station_name, station in self.metro_map.stations.items():
                if station.controlling_faction != self.player.faction:
                    # Check if we have diplomatic options
                    options = self.diplomacy_system.get_diplomatic_options(
                        self.player.faction, station.controlling_faction
                    )
                    if options:
                        diplomatic_targets.append(station.controlling_faction)
            
            # Remove duplicates
            diplomatic_targets = list(set(diplomatic_targets))
            
            if diplomatic_targets:
                return {"success": False, "message": f"Select diplomatic target: {', '.join(diplomatic_targets[:3])}"}
            else:
                return {"success": False, "message": "No diplomatic opportunities available"}
        
        # Get target faction
        target_station = self.metro_map.get_station(target)
        if not target_station:
            return {"success": False, "message": f"Target station {target} not found"}
        
        target_faction = target_station.controlling_faction
        
        # Execute basic diplomacy action (improve relations)
        result = self.diplomacy_system.execute_diplomatic_action(
            self.player.faction, target_faction, DiplomaticAction.IMPROVE_RELATIONS,
            self.current_turn, mgr_cost=10
        )
        
        # Consume MGR if successful
        if result["success"]:
            if self.player.resources.has_sufficient("mgr_rounds", 10):
                self.player.resources.subtract("mgr_rounds", 10)
                self.statistics["diplomatic_agreements"] += 1
            else:
                return {"success": False, "message": "Not enough MGR rounds for diplomacy"}
        
        return result
    
    def _execute_fortify_action(self, origin: str) -> Dict[str, Any]:
        """Execute fortify action"""
        origin_station = self.metro_map.get_station(origin)
        if origin_station.controlling_faction != self.player.faction:
            return {"success": False, "message": "Can only fortify own stations"}
        
        # Check costs
        scrap_cost = 30
        mgr_cost = 5
        
        if not self.player.resources.has_sufficient_multiple({"scrap": scrap_cost, "mgr_rounds": mgr_cost}):
            return {"success": False, "message": "Insufficient resources for fortification"}
        
        # Consume resources
        self.player.resources.consume_multiple({"scrap": scrap_cost, "mgr_rounds": mgr_cost})
        
        # Improve defenses
        origin_station.defensive_value += 10
        
        return {"success": True, "message": f"Fortified {origin}. Defense increased to {origin_station.defensive_value}"}
    
    def _execute_recruit_action(self, origin: str) -> Dict[str, Any]:
        """Execute recruit action"""
        origin_station = self.metro_map.get_station(origin)
        if origin_station.controlling_faction != self.player.faction:
            return {"success": False, "message": "Can only recruit at own stations"}
        
        # Default to recruiting militia (basic unit)
        unit_type = UnitType.MILITIA
        
        # Check if we can recruit this unit type
        can_recruit, reason = self.military_manager.can_recruit_unit(
            unit_type, origin_station, self.get_player_resource_amounts()
        )
        
        if not can_recruit:
            return {"success": False, "message": reason}
        
        # Recruit the unit
        success, message, unit = self.military_manager.recruit_unit(
            unit_type, origin, self.get_player_resource_amounts()
        )
        
        if success:
            # Update player resources (they were modified by reference)
            self.statistics["units_recruited"] += 1
            return {"success": True, "message": f"Recruited {unit_type.value} at {origin}"}
        else:
            return {"success": False, "message": message}
    
    def _execute_develop_action(self, origin: str) -> Dict[str, Any]:
        """Execute develop action"""
        origin_station = self.metro_map.get_station(origin)
        if origin_station.controlling_faction != self.player.faction:
            return {"success": False, "message": "Can only develop own stations"}
        
        # Simple development: add mushroom farm if not present
        from data.infrastructure import BuildingType
        
        if BuildingType.MUSHROOM_FARM not in origin_station.infrastructure:
            scrap_cost = 20
            if not self.player.resources.has_sufficient("scrap", scrap_cost):
                return {"success": False, "message": "Insufficient scrap for development"}
            
            self.player.resources.subtract("scrap", scrap_cost)
            origin_station.add_infrastructure(BuildingType.MUSHROOM_FARM, 1)
            
            return {"success": True, "message": f"Built mushroom farm at {origin}"}
        else:
            return {"success": False, "message": f"{origin} already has a mushroom farm"}
    
    def get_player_resources(self) -> ResourcePool:
        """Get player resource pool"""
        return self.player.resources
    
    def get_controlled_stations(self) -> List[str]:
        """Get list of player-controlled stations"""
        return self.player.controlled_stations.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get game statistics"""
        return self.statistics.copy()
    
    def get_player_resource_amounts(self) -> Dict[str, int]:
        """Get player resource amounts as dictionary"""
        return {
            "food": self.player.resources.food,
            "clean_water": self.player.resources.clean_water,
            "scrap": self.player.resources.scrap,
            "medicine": self.player.resources.medicine,
            "mgr_rounds": self.player.resources.mgr_rounds
        }
    
    def get_station_intelligence(self, station_name: str) -> Optional[Dict[str, Any]]:
        """Get intelligence about a station"""
        intel = self.scouting_system.get_station_intelligence(station_name)
        if intel:
            return {
                "station_name": intel.station_name,
                "level": intel.level.value,
                "last_updated": intel.last_updated,
                "faction": intel.faction,
                "population": intel.population,
                "morale": intel.morale,
                "defensive_value": intel.defensive_value,
                "resources": intel.resources,
                "infrastructure": intel.infrastructure,
                "military_units": intel.military_units,
                "special_traits": intel.special_traits
            }
        return None
    
    def is_station_discovered(self, station_name: str) -> bool:
        """Check if a station has been discovered"""
        return self.scouting_system.is_station_discovered(station_name)
    
    def get_visible_stations(self) -> Set[str]:
        """Get all stations visible to the player"""
        return self.scouting_system.get_visible_stations()
    
    def get_scouting_targets(self, origin_station: str) -> List[str]:
        """Get valid scouting targets from a station"""
        return self.scouting_system.get_scouting_targets(origin_station)
    
    def get_active_caravans(self) -> Dict[str, Any]:
        """Get information about active caravans"""
        caravans = self.trade_system.get_active_caravans()
        return {cid: {
            "id": caravan.caravan_id,
            "origin": caravan.origin,
            "destination": caravan.destination,
            "current_position": caravan.current_position,
            "status": caravan.status.value,
            "estimated_arrival": caravan.estimated_arrival
        } for cid, caravan in caravans.items()}
    
    def get_trade_routes(self) -> Dict[str, Any]:
        """Get information about established trade routes"""
        routes = self.trade_system.get_trade_routes()
        return {rid: {
            "id": route.route_id,
            "stations": [route.station_a, route.station_b],
            "status": route.status.value,
            "total_trades": route.total_trades,
            "security_level": route.security_level
        } for rid, route in routes.items()}
    
    def get_supply_lines(self, station: str) -> List[str]:
        """Get supply lines connected to a station"""
        return self.trade_system.get_supply_lines(station)
    
    def get_trade_opportunities(self, origin: str) -> List[Dict[str, Any]]:
        """Get available trade opportunities from a station"""
        return self.trade_system.get_trade_opportunities(origin)
    
    def get_attack_preview(self, origin: str, target: str) -> Dict[str, Any]:
        """Get preview of potential attack outcome"""
        return self.combat_system.get_attack_preview(origin, target, self.player.faction)
    
    def get_battle_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent battle history"""
        battles = self.combat_system.get_battle_history(limit)
        return [{
            "attacker": battle.attacker,
            "defender": battle.defender,
            "result": battle.result.value,
            "description": battle.battle_description,
            "turn": battle.turn_number,
            "territory_changed": battle.territory_changed
        } for battle in battles]
    
    def get_military_strength(self, faction: str = None) -> Dict[str, Any]:
        """Get military strength assessment"""
        faction = faction or self.player.faction
        return self.combat_system.get_faction_military_strength(faction)
    
    def can_attack_station(self, target: str) -> Tuple[bool, str]:
        """Check if player can attack a station"""
        return self.combat_system.can_attack(self.player.faction, target)
    
    def get_diplomatic_options(self, target_faction: str) -> List[Dict[str, Any]]:
        """Get available diplomatic options with a faction"""
        return self.diplomacy_system.get_diplomatic_options(self.player.faction, target_faction)
    
    def get_faction_relationships(self) -> Dict[str, Dict[str, Any]]:
        """Get all diplomatic relationships for the player faction"""
        return self.diplomacy_system.get_faction_relationships(self.player.faction)
    
    def get_relationship_status(self, target_faction: str) -> str:
        """Get relationship status with a faction"""
        relationship = self.diplomacy_system.get_relationship(self.player.faction, target_faction)
        return relationship.status.value if relationship else "unknown"
    
    def execute_diplomatic_action(self, target_faction: str, action: str, mgr_cost: int = 0) -> Dict[str, Any]:
        """Execute a specific diplomatic action"""
        try:
            diplomatic_action = DiplomaticAction(action)
        except ValueError:
            return {"success": False, "message": f"Unknown diplomatic action: {action}"}
        
        # Check MGR cost
        if mgr_cost > 0 and not self.player.resources.has_sufficient("mgr_rounds", mgr_cost):
            return {"success": False, "message": f"Insufficient MGR for diplomatic action (need {mgr_cost})"}
        
        # Execute action
        result = self.diplomacy_system.execute_diplomatic_action(
            self.player.faction, target_faction, diplomatic_action,
            self.current_turn, mgr_cost
        )
        
        # Consume MGR if successful
        if result["success"] and mgr_cost > 0:
            self.player.resources.subtract("mgr_rounds", mgr_cost)
            self.statistics["diplomatic_agreements"] += 1
        
        return result
    
    def _execute_recruit_specific_unit_action(self, origin: str, unit_type_str: str) -> Dict[str, Any]:
        """Execute recruitment of a specific unit type"""
        origin_station = self.metro_map.get_station(origin)
        if origin_station.controlling_faction != self.player.faction:
            return {"success": False, "message": "Can only recruit at own stations"}
        
        # Parse unit type
        try:
            unit_type = UnitType(unit_type_str.lower())
        except ValueError:
            return {"success": False, "message": f"Unknown unit type: {unit_type_str}"}
        
        # Check if we can recruit this unit type
        can_recruit, reason = self.military_manager.can_recruit_unit(
            unit_type, origin_station, self.get_player_resource_amounts()
        )
        
        if not can_recruit:
            return {"success": False, "message": reason}
        
        # Recruit the unit
        success, message, unit = self.military_manager.recruit_unit(
            unit_type, origin, self.get_player_resource_amounts()
        )
        
        if success:
            self.statistics["units_recruited"] += 1
            return {"success": True, "message": message}
        else:
            return {"success": False, "message": message}
    
    def get_military_units_at_station(self, station_id: str) -> List[Dict]:
        """Get all military units at a specific station"""
        units = self.military_manager.get_units_at_station(station_id)
        return [unit.get_info() for unit in units]
    
    def get_total_military_strength_at_station(self, station_id: str) -> int:
        """Get total combat strength at a station"""
        return self.military_manager.get_total_combat_strength_at_station(station_id)
    
    def get_military_unit_summary(self) -> Dict[str, int]:
        """Get summary of all military units by type"""
        return self.military_manager.get_unit_summary()
    
    def get_all_military_units(self) -> List[Dict]:
        """Get information about all military units"""
        return self.military_manager.get_all_units_info()
    
    def get_military_maintenance_cost(self) -> Dict[str, int]:
        """Get total military maintenance cost per turn"""
        return self.military_manager.calculate_total_maintenance_cost()
    
    def get_available_unit_types(self, station_id: str) -> List[Dict[str, Any]]:
        """Get unit types that can be recruited at a station"""
        station = self.metro_map.get_station(station_id)
        if not station or station.controlling_faction != self.player.faction:
            return []
        
        available_units = []
        resources = self.get_player_resource_amounts()
        
        for unit_type in UnitType:
            can_recruit, reason = self.military_manager.can_recruit_unit(
                unit_type, station, resources
            )
            
            # Get unit stats for display
            from data.military_unit import MilitaryUnit
            temp_unit = MilitaryUnit(unit_type, self.player.faction, station_id, 1, 0)
            stats = temp_unit.base_stats
            
            available_units.append({
                "type": unit_type.value,
                "can_recruit": can_recruit,
                "reason": reason if not can_recruit else "Available",
                "combat_strength": stats.combat_strength,
                "movement_range": stats.movement_range,
                "recruitment_cost": stats.recruitment_cost,
                "population_cost": stats.population_cost,
                "maintenance_cost": stats.maintenance_cost,
                "abilities": stats.special_abilities
            })
        
        return available_units
    
    def _auto_resolve_event(self, event: Dict[str, Any], player_stations: List):
        """Auto-resolve events that don't require player choice"""
        # This would apply automatic effects for events without choices
        # For now, we'll just log that the event occurred
        self.logger.info(f"Auto-resolved event: {event['title']}")
    
    def get_triggered_events(self) -> List[Dict[str, Any]]:
        """Get events that were triggered this turn"""
        if hasattr(self, '_last_triggered_events'):
            return self._last_triggered_events
        return []
    
    def get_active_events(self) -> List[Dict[str, Any]]:
        """Get currently active events"""
        return self.event_system.get_active_events()
    
    def get_event_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent event history"""
        return self.event_system.get_event_history(limit)
    
    def resolve_event_choice(self, event_id: str, choice_id: str) -> Dict[str, Any]:
        """Resolve a player choice for an event"""
        # Get all player-controlled stations
        player_stations = [
            self.metro_map.get_station(station_name) 
            for station_name in self.player.controlled_stations
        ]
        player_stations = [s for s in player_stations if s is not None]
        
        # Resolve the choice through the event system
        result = self.event_system.resolve_event_choice(
            event_id, choice_id, self.player.resources, player_stations
        )
        
        if result['success']:
            self.logger.info(f"Resolved event choice: {event_id} -> {choice_id}")
        else:
            self.logger.warning(f"Failed to resolve event choice: {result['message']}")
        
        return result
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get event system statistics"""
        return self.event_system.get_event_statistics()
    
    def set_event_category_modifier(self, category: str, modifier: float):
        """Set probability modifier for an event category"""
        from systems.event_system import EventCategory
        try:
            event_category = EventCategory(category.lower())
            self.event_system.set_category_modifier(event_category, modifier)
            self.logger.info(f"Set {category} event probability modifier to {modifier}")
        except ValueError:
            self.logger.error(f"Unknown event category: {category}")
    
    def trigger_specific_event(self, event_id: str) -> Dict[str, Any]:
        """Manually trigger a specific event (for testing or scripted events)"""
        player_stations = [
            self.metro_map.get_station(station_name) 
            for station_name in self.player.controlled_stations
        ]
        player_stations = [s for s in player_stations if s is not None]
        
        return self.event_system.trigger_specific_event(event_id, self.current_turn, player_stations)
    
    def _check_victory_conditions(self):
        """Check victory conditions and handle game end"""
        # Get current game state for victory checking
        game_state_data = self.get_game_state()
        
        # Check all victory conditions
        victory_results = self.victory_system.check_victory_conditions(self.current_turn, game_state_data)
        
        # Check if any victory was achieved
        for result in victory_results:
            if result.achieved:
                self.logger.info(f"Victory achieved: {result.victory_type.value} on turn {self.current_turn}")
                # Store victory results for UI display
                self._last_victory_results = victory_results
                break
        
        # Store victory results for UI display
        self._last_victory_results = victory_results
    
    def _process_ai_turn(self):
        """Process AI faction actions for this turn"""
        try:
            self.ai_system.process_ai_turn(
                self.current_turn,
                self.diplomacy_system,
                self.combat_system,
                self.trade_system
            )
            self.logger.debug(f"AI turn processing completed for turn {self.current_turn}")
        except Exception as e:
            self.logger.error(f"Error processing AI turn: {e}")
    
    def _execute_resolve_event_action(self, event_id: str, choice_id: str) -> Dict[str, Any]:
        """Execute event choice resolution"""
        if not event_id or not choice_id:
            return {"success": False, "message": "Event ID and choice ID required"}
        
        result = self.resolve_event_choice(event_id, choice_id)
        
        if result['success']:
            return {"success": True, "message": f"Event choice resolved: {result.get('description', 'Choice resolved')}"}
        else:
            return {"success": False, "message": result['message']}
    
    def _execute_construct_action(self, origin: str, building_type_str: str) -> Dict[str, Any]:
        """Execute construction of a building"""
        origin_station = self.metro_map.get_station(origin)
        if origin_station.controlling_faction != self.player.faction:
            return {"success": False, "message": "Can only construct at own stations"}
        
        # Parse building type
        try:
            building_type = BuildingType(building_type_str.lower())
        except ValueError:
            return {"success": False, "message": f"Unknown building type: {building_type_str}"}
        
        # Start construction
        success, message = self.building_system.start_construction(
            origin, building_type, self.player.resources, self.current_turn
        )
        
        return {"success": success, "message": message}
    
    def _execute_upgrade_action(self, origin: str, building_type_str: str) -> Dict[str, Any]:
        """Execute upgrade of a building"""
        origin_station = self.metro_map.get_station(origin)
        if origin_station.controlling_faction != self.player.faction:
            return {"success": False, "message": "Can only upgrade at own stations"}
        
        # Parse building type
        try:
            building_type = BuildingType(building_type_str.lower())
        except ValueError:
            return {"success": False, "message": f"Unknown building type: {building_type_str}"}
        
        # Upgrade building
        success, message = self.building_system.upgrade_building(
            origin, building_type, self.player.resources
        )
        
        return {"success": success, "message": message}
    
    def _execute_repair_action(self, origin: str, building_type_str: str) -> Dict[str, Any]:
        """Execute repair of a building"""
        origin_station = self.metro_map.get_station(origin)
        if origin_station.controlling_faction != self.player.faction:
            return {"success": False, "message": "Can only repair at own stations"}
        
        # Parse building type
        try:
            building_type = BuildingType(building_type_str.lower())
        except ValueError:
            return {"success": False, "message": f"Unknown building type: {building_type_str}"}
        
        # Repair building
        success, message = self.building_system.repair_building(
            origin, building_type, self.player.resources
        )
        
        return {"success": success, "message": message}
    
    def get_available_buildings(self, station_id: str) -> List[Dict[str, Any]]:
        """Get buildings that can be constructed at a station"""
        return self.building_system.get_available_buildings(station_id, self.player.resources)
    
    def get_construction_projects(self) -> List[Dict[str, Any]]:
        """Get active construction projects"""
        return self.building_system.get_construction_projects()
    
    def get_station_buildings(self, station_id: str) -> List[Dict[str, Any]]:
        """Get all buildings at a station with their status"""
        station = self.metro_map.get_station(station_id)
        if not station:
            return []
        
        buildings = []
        for building_type, infrastructure in station.infrastructure.items():
            building_info = infrastructure.get_info()
            
            # Add upgrade and repair options
            can_upgrade, upgrade_reason = self.building_system.can_upgrade_building(
                station_id, building_type, self.player.resources
            )
            
            building_info.update({
                "can_upgrade": can_upgrade,
                "upgrade_reason": upgrade_reason if not can_upgrade else "Available",
                "needs_repair": infrastructure.damage_level > 0
            })
            
            buildings.append(building_info)
        
        return buildings
    
    def get_building_maintenance_cost(self) -> Dict[str, int]:
        """Get total building maintenance cost per turn"""
        player_stations = [
            self.metro_map.get_station(station_name) 
            for station_name in self.player.controlled_stations
        ]
        player_stations = [s for s in player_stations if s is not None]
        
        return self.building_system.get_building_maintenance_summary(player_stations)
    
    def get_victory_status(self) -> Dict[str, Any]:
        """Get current victory status and progress"""
        return self.victory_system.get_victory_status()
    
    def get_victory_progress_summary(self) -> Dict[str, Any]:
        """Get summary of all victory condition progress"""
        return self.victory_system.get_victory_progress_summary()
    
    def get_closest_victory(self) -> Optional[tuple]:
        """Get the victory condition closest to completion"""
        return self.victory_system.get_closest_victory()
    
    def get_victory_progress_history(self, turns: int = 10) -> List[Dict[str, Any]]:
        """Get victory progress history"""
        return self.victory_system.get_progress_history(turns)
    
    def is_game_ended(self) -> bool:
        """Check if game has ended due to victory"""
        return self.victory_system.is_game_ended()
    
    def get_victory_results(self) -> List[Dict[str, Any]]:
        """Get latest victory condition results"""
        if hasattr(self, '_last_victory_results'):
            return [
                {
                    "victory_type": result.victory_type.value,
                    "achieved": result.achieved,
                    "progress": result.progress * 100,  # Convert to percentage
                    "status": result.status.value,
                    "description": result.description,
                    "turn_achieved": result.turn_achieved
                }
                for result in self._last_victory_results
            ]
        return []
    
    def reset_game(self):
        """Reset game state for new game"""
        self.current_turn = 1
        self.game_phase = "planning"
        
        # Reset player state
        self.player = PlayerState()
        self._initialize_player_resources()
        
        # Reset statistics
        self.statistics = {
            "stations_controlled": 0,
            "total_population": 0,
            "battles_won": 0,
            "trades_completed": 0,
            "diplomatic_agreements": 0,
            "units_recruited": 0,
            "total_military_strength": 0
        }
        
        # Reset victory conditions
        self.victory_system.reset_victory_conditions()
        
        self.logger.info("Game state reset for new game")
    
    def get_production_summary(self) -> Dict[str, Any]:
        """Get comprehensive production summary for the player faction"""
        player_stations = [
            self.metro_map.get_station(station_name) 
            for station_name in self.player.controlled_stations
        ]
        player_stations = [s for s in player_stations if s is not None]
        
        return self.resource_production_system.get_production_summary(player_stations, self.current_turn)
    
    def get_production_reports(self) -> List[Dict[str, Any]]:
        """Get detailed production reports for all player stations"""
        if hasattr(self, '_last_production_reports'):
            return [report.__dict__ for report in self._last_production_reports]
        return []
    
    def get_resource_forecast(self, turns_ahead: int = 3) -> Dict[str, List[int]]:
        """Get resource forecast for the next few turns"""
        player_stations = [
            self.metro_map.get_station(station_name) 
            for station_name in self.player.controlled_stations
        ]
        player_stations = [s for s in player_stations if s is not None]
        
        return self.resource_production_system.get_resource_forecast(
            player_stations, self.player.resources, turns_ahead
        )
    
    def set_production_modifier(self, resource: str, modifier: float, duration: int = -1):
        """Set a global production modifier (for events, policies, etc.)"""
        self.resource_production_system.set_global_modifier(resource, modifier, duration)
    
    def get_station_production_report(self, station_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed production report for a specific station"""
        station = self.metro_map.get_station(station_name)
        if not station:
            return None
        
        report = self.resource_production_system.calculate_station_production(station, self.current_turn)
        return report.__dict__
    
    def get_active_events(self) -> List[Dict[str, Any]]:
        """Get all currently active events"""
        return self.event_system.get_active_events()
    
    def get_recent_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent events"""
        return self.event_system.get_event_history(limit)
    
    def get_triggered_events(self) -> List[Dict[str, Any]]:
        """Get events triggered this turn"""
        if hasattr(self, '_last_triggered_events'):
            return self._last_triggered_events
        return []
    
    def resolve_event_choice(self, event_id: str, choice_id: str) -> Dict[str, Any]:
        """Resolve a player's choice for an event"""
        player_stations = [
            self.metro_map.get_station(station_name) 
            for station_name in self.player.controlled_stations
        ]
        player_stations = [s for s in player_stations if s is not None]
        
        return self.event_system.resolve_event_choice(
            event_id, choice_id, self.player.resources, player_stations
        )
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get event system statistics"""
        return self.event_system.get_event_statistics()
    
    def set_event_category_modifier(self, category: str, modifier: float):
        """Set probability modifier for an event category"""
        from systems.event_system import EventCategory
        try:
            event_category = EventCategory(category)
            self.event_system.set_category_modifier(event_category, modifier)
        except ValueError:
            self.logger.error(f"Invalid event category: {category}")  
  
    def get_ai_faction_info(self, faction_name: str = None) -> Dict[str, Any]:
        """Get AI faction information"""
        if faction_name:
            return self.ai_system.get_ai_faction_info(faction_name)
        else:
            return self.ai_system.get_all_ai_factions_info()
    
    def get_ai_statistics(self) -> Dict[str, Any]:
        """Get AI system statistics"""
        return self.ai_system.get_ai_statistics()
    
    def get_victory_status(self) -> Dict[str, Any]:
        """Get current victory status"""
        return self.victory_system.get_victory_status()
    
    def get_victory_progress_summary(self) -> Dict[str, Any]:
        """Get victory progress summary"""
        return self.victory_system.get_victory_progress_summary()
    
    def get_closest_victory(self) -> Optional[tuple]:
        """Get the victory condition closest to completion"""
        return self.victory_system.get_closest_victory()
    
    def is_game_ended(self) -> bool:
        """Check if game has ended due to victory"""
        return self.victory_system.is_game_ended()   
 
    def save_game(self, slot_name: str, description: str = "") -> Dict[str, Any]:
        """
        Save current game state
        
        Args:
            slot_name: Name for the save slot
            description: Optional description for the save
            
        Returns:
            Result dictionary with success status and message
        """
        from systems.save_system import SaveSystem
        save_system = SaveSystem()
        return save_system.save_game(self, slot_name, description)
    
    def load_game(self, slot_name: str) -> Dict[str, Any]:
        """
        Load game state from save file
        
        Args:
            slot_name: Name of the save slot to load
            
        Returns:
            Result dictionary with success status and message
        """
        from systems.save_system import SaveSystem
        from systems.load_system import LoadSystem
        
        save_system = SaveSystem()
        load_system = LoadSystem()
        
        result = save_system.load_game(slot_name)
        
        if result["success"]:
            try:
                # Reconstruct game state from save data
                save_data = result["save_data"]
                reconstructed_state = load_system.reconstruct_game_state(save_data, self.metro_map)
                
                # Validate loaded state
                validation = load_system.validate_loaded_state(reconstructed_state)
                

                if not validation["valid"]:
                    self.logger.warning(f"Loaded state has issues: {validation['issues']}")
                
                # Copy reconstructed state to current instance
                self._copy_game_state(reconstructed_state)
                
                self.logger.info(f"Game loaded successfully from slot '{slot_name}' - Turn {self.current_turn}")
                return {
                    "success": True,
                    "message": f"Game loaded from slot '{slot_name}'",
                    "turn": self.current_turn,
                    "validation": validation
                }
                
            except Exception as e:
                self.logger.error(f"Failed to reconstruct game state: {e}")
                return {
                    "success": False,
                    "message": f"Failed to load game: {str(e)}",
                    "error": str(e)
                }
        
        return result
    
    def _copy_game_state(self, source_state: 'GameStateManager'):
        """Copy game state from another GameStateManager instance"""
        # Copy core state
        self.current_turn = source_state.current_turn
        self.game_phase = source_state.game_phase
        self.statistics = source_state.statistics.copy()
        
        # Copy player state
        self.player.faction = source_state.player.faction
        self.player.controlled_stations = source_state.player.controlled_stations.copy()
        
        # Copy resources
        self.player.resources.food = source_state.player.resources.food
        self.player.resources.clean_water = source_state.player.resources.clean_water
        self.player.resources.scrap = source_state.player.resources.scrap
        self.player.resources.medicine = source_state.player.resources.medicine
        self.player.resources.mgr_rounds = source_state.player.resources.mgr_rounds
        
        # Copy system states (references to maintain object relationships)
        self.scouting_system = source_state.scouting_system
        self.trade_system = source_state.trade_system
        self.diplomacy_system = source_state.diplomacy_system
        self.military_manager = source_state.military_manager
        self.building_system = source_state.building_system
        self.event_system = source_state.event_system
        self.victory_system = source_state.victory_system
        self.ai_system = source_state.ai_system
        
        # Reconnect systems
        self.combat_system.diplomacy_system = self.diplomacy_system
        self.combat_system.register_military_manager(self.player.faction, self.military_manager)
    
    def get_save_slots(self) -> List[Dict[str, Any]]:
        """Get list of available save slots"""
        from systems.save_system import SaveSystem
        save_system = SaveSystem()
        return save_system.get_save_slots()
    
    def delete_save(self, slot_name: str) -> Dict[str, Any]:
        """Delete a save slot"""
        from systems.save_system import SaveSystem
        save_system = SaveSystem()
        return save_system.delete_save(slot_name)
    
    def create_quick_save(self) -> Dict[str, Any]:
        """Create a quick save with automatic naming"""
        from systems.save_system import SaveSystem
        save_system = SaveSystem()
        return save_system.create_quick_save(self)
    
    def create_auto_save(self) -> Dict[str, Any]:
        """Create an auto-save for the current turn"""
        from systems.save_system import SaveSystem
        save_system = SaveSystem()
        slot_name = save_system.get_auto_save_name(self)
        description = f"Auto-save for turn {self.current_turn}"
        return save_system.save_game(self, slot_name, description)