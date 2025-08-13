"""
Load System for Game State Reconstruction
Handles deserialization and reconstruction of game state from save data
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

from systems.metro_map import MetroMap
from systems.game_state import GameStateManager
from systems.scouting_system import ScoutingSystem, StationIntelligence, IntelligenceLevel
from systems.trade_system import TradeSystem, Caravan, TradeRoute, CaravanStatus, RouteStatus
from systems.diplomacy_system import DiplomacySystem, RelationshipLevel
from systems.building_system import BuildingSystem, ConstructionProject
from systems.event_system import EventSystem, EventCategory
from systems.victory_system import VictorySystem, VictoryType, VictoryStatus
from systems.ai_system import AISystem, AIFaction, AIPersonality, AIAction
from data.resources import ResourcePool
from data.station import Station
from data.infrastructure import Infrastructure, BuildingType
from data.military_unit import MilitaryManager, MilitaryUnit, UnitType
from data.tunnel import Tunnel, TunnelCondition


class LoadSystem:
    """
    System for reconstructing game state from save data
    
    Features:
    - Complete game state reconstruction from serialized data
    - Error handling and validation during load process
    - System state restoration with proper object relationships
    - Backward compatibility support
    """
    
    def __init__(self):
        """Initialize load system"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Load system initialized")
    
    def reconstruct_game_state(self, save_data: Dict[str, Any], metro_map: MetroMap) -> GameStateManager:
        """
        Reconstruct complete game state from save data
        
        Args:
            save_data: Serialized game state data
            metro_map: MetroMap instance to use as base
            
        Returns:
            Reconstructed GameStateManager instance
        """
        try:
            # Create new game state manager
            game_state = GameStateManager(metro_map)
            
            # Restore core game state
            game_state.current_turn = save_data["current_turn"]
            game_state.game_phase = save_data["game_phase"]
            game_state.statistics = save_data["statistics"].copy()
            
            # Restore player state
            self._restore_player_state(game_state, save_data["player"])
            
            # Restore metro map state
            self._restore_metro_map_state(game_state.metro_map, save_data["metro_map"])
            
            # Restore system states
            self._restore_scouting_system(game_state.scouting_system, save_data["scouting_system"])
            self._restore_trade_system(game_state.trade_system, save_data["trade_system"])
            self._restore_diplomacy_system(game_state.diplomacy_system, save_data["diplomacy_system"])
            self._restore_military_manager(game_state.military_manager, save_data["military_manager"])
            self._restore_building_system(game_state.building_system, save_data["building_system"])
            self._restore_event_system(game_state.event_system, save_data["event_system"])
            self._restore_victory_system(game_state.victory_system, save_data["victory_system"])
            self._restore_ai_system(game_state.ai_system, save_data["ai_system"])
            
            self.logger.info(f"Game state reconstructed successfully for turn {game_state.current_turn}")
            return game_state
            
        except Exception as e:
            self.logger.error(f"Failed to reconstruct game state: {e}")
            raise
    
    def _restore_player_state(self, game_state: GameStateManager, player_data: Dict[str, Any]):
        """Restore player state"""
        game_state.player.faction = player_data["faction"]
        game_state.player.controlled_stations = player_data["controlled_stations"].copy()
        
        # Restore resources
        resources_data = player_data["resources"]
        game_state.player.resources.food = resources_data["food"]
        game_state.player.resources.clean_water = resources_data["clean_water"]
        game_state.player.resources.scrap = resources_data["scrap"]
        game_state.player.resources.medicine = resources_data["medicine"]
        game_state.player.resources.mgr_rounds = resources_data["mgr_rounds"]
    
    def _restore_metro_map_state(self, metro_map: MetroMap, map_data: Dict[str, Any]):
        """Restore metro map state"""
        # Restore stations
        stations_data = map_data["stations"]
        for station_name, station_data in stations_data.items():
            if station_name in metro_map.stations:
                station = metro_map.stations[station_name]
                self._restore_station_state(station, station_data)
        
        # Restore tunnels
        tunnels_data = map_data["tunnels"]
        for tunnel_id, tunnel_data in tunnels_data.items():
            if tunnel_id in metro_map.tunnels:
                tunnel = metro_map.tunnels[tunnel_id]
                tunnel.condition = TunnelCondition(tunnel_data["condition"])
                tunnel.safety_level = tunnel_data["safety_level"]
                tunnel.travel_cost = tunnel_data["travel_cost"]
    
    def _restore_station_state(self, station: Station, station_data: Dict[str, Any]):
        """Restore individual station state"""
        station.controlling_faction = station_data["controlling_faction"]
        station.population = station_data["population"]
        station.morale = station_data["morale"]
        station.defensive_value = station_data["defensive_value"]
        station.special_traits = station_data["special_traits"].copy()
        
        # Restore resources
        resources_data = station_data["resources"]
        station.resources.food = resources_data["food"]
        station.resources.clean_water = resources_data["clean_water"]
        station.resources.scrap = resources_data["scrap"]
        station.resources.medicine = resources_data["medicine"]
        station.resources.mgr_rounds = resources_data["mgr_rounds"]
        
        # Restore infrastructure
        infrastructure_data = station_data["infrastructure"]
        station.infrastructure.clear()
        
        for building_type_str, infra_data in infrastructure_data.items():
            building_type = BuildingType(building_type_str)
            infrastructure = Infrastructure(building_type, infra_data["level"])
            infrastructure.condition = infra_data["condition"]
            infrastructure.construction_turn = infra_data["construction_turn"]
            station.infrastructure[building_type] = infrastructure
    
    def _restore_scouting_system(self, scouting_system: ScoutingSystem, scouting_data: Dict[str, Any]):
        """Restore scouting system state"""
        # Restore station intelligence
        intelligence_data = scouting_data["station_intelligence"]
        scouting_system.station_intelligence.clear()
        
        for station_name, intel_data in intelligence_data.items():
            intel = StationIntelligence(
                station_name=intel_data["station_name"],
                level=IntelligenceLevel(intel_data["level"]),
                last_updated=intel_data["last_updated"]
            )
            intel.faction = intel_data["faction"]
            intel.population = intel_data["population"]
            intel.morale = intel_data["morale"]
            intel.defensive_value = intel_data["defensive_value"]
            intel.resources = intel_data["resources"].copy()
            intel.infrastructure = intel_data["infrastructure"].copy()
            intel.military_units = intel_data["military_units"].copy()
            intel.special_traits = intel_data["special_traits"].copy()
            
            scouting_system.station_intelligence[station_name] = intel
        
        # Restore discovered stations
        scouting_system.discovered_stations = set(scouting_data["discovered_stations"])
        scouting_system.scouting_reports = scouting_data["scouting_reports"].copy()
    
    def _restore_trade_system(self, trade_system: TradeSystem, trade_data: Dict[str, Any]):
        """Restore trade system state"""
        # Restore active caravans
        caravans_data = trade_data["active_caravans"]
        trade_system.active_caravans.clear()
        
        for caravan_id, caravan_data in caravans_data.items():
            caravan = Caravan(
                caravan_id=caravan_data["caravan_id"],
                origin=caravan_data["origin"],
                destination=caravan_data["destination"]
            )
            caravan.current_position = caravan_data["current_position"]
            caravan.status = CaravanStatus(caravan_data["status"])
            caravan.estimated_arrival = caravan_data["estimated_arrival"]
            caravan.cargo = caravan_data["cargo"].copy()
            caravan.security_level = caravan_data["security_level"]
            
            trade_system.active_caravans[caravan_id] = caravan
        
        # Restore trade routes
        routes_data = trade_data["trade_routes"]
        trade_system.trade_routes.clear()
        
        for route_id, route_data in routes_data.items():
            route = TradeRoute(
                route_id=route_data["route_id"],
                station_a=route_data["station_a"],
                station_b=route_data["station_b"]
            )
            route.status = RouteStatus(route_data["status"])
            route.total_trades = route_data["total_trades"]
            route.security_level = route_data["security_level"]
            route.established_turn = route_data["established_turn"]
            
            trade_system.trade_routes[route_id] = route
        
        # Restore trade agreements
        trade_system.trade_agreements = trade_data["trade_agreements"].copy()
    
    def _restore_diplomacy_system(self, diplomacy_system: DiplomacySystem, diplomacy_data: Dict[str, Any]):
        """Restore diplomacy system state"""
        # Restore faction relationships
        relationships_data = diplomacy_data["faction_relationships"]
        diplomacy_system.faction_relationships.clear()
        
        for faction_pair, relationship_str in relationships_data.items():
            diplomacy_system.faction_relationships[faction_pair] = RelationshipLevel(relationship_str)
        
        # Restore relationship history and agreements
        diplomacy_system.relationship_history = diplomacy_data["relationship_history"].copy()
        diplomacy_system.diplomatic_agreements = diplomacy_data["diplomatic_agreements"].copy()
    
    def _restore_military_manager(self, military_manager: MilitaryManager, military_data: Dict[str, Any]):
        """Restore military manager state"""
        military_manager.faction = military_data["faction"]
        
        # Restore units
        units_data = military_data["units"]
        military_manager.units.clear()
        
        for unit_data in units_data:
            unit = MilitaryUnit(
                unit_type=UnitType(unit_data["unit_type"]),
                stationed_at=unit_data["stationed_at"],
                unit_id=unit_data["unit_id"]
            )
            unit.experience = unit_data["experience"]
            unit.morale = unit_data["morale"]
            unit.equipment_level = unit_data["equipment_level"]
            unit.is_active = unit_data["is_active"]
            unit.recruitment_turn = unit_data["recruitment_turn"]
            
            military_manager.units.append(unit)
    
    def _restore_building_system(self, building_system: BuildingSystem, building_data: Dict[str, Any]):
        """Restore building system state"""
        # Restore construction projects
        projects_data = building_data["construction_projects"]
        building_system.construction_projects.clear()
        
        for project_data in projects_data:
            project = ConstructionProject(
                station_name=project_data["station_name"],
                building_type=BuildingType(project_data["building_type"]),
                start_turn=project_data["start_turn"],
                completion_turn=project_data["completion_turn"]
            )
            project.progress = project_data["progress"]
            project.total_cost = project_data["total_cost"].copy()
            
            building_system.construction_projects.append(project)
    
    def _restore_event_system(self, event_system: EventSystem, event_data: Dict[str, Any]):
        """Restore event system state"""
        # Restore active events and history
        event_system.active_events = event_data["active_events"].copy()
        event_system.event_history = event_data["event_history"].copy()
        
        # Restore category modifiers
        modifiers_data = event_data["category_modifiers"]
        event_system.category_modifiers.clear()
        
        for category_str, modifier in modifiers_data.items():
            event_system.category_modifiers[EventCategory(category_str)] = modifier
    
    def _restore_victory_system(self, victory_system: VictorySystem, victory_data: Dict[str, Any]):
        """Restore victory system state"""
        victory_system.game_ended = victory_data["game_ended"]
        victory_system.victory_turn = victory_data["victory_turn"]
        victory_system.victory_score = victory_data["victory_score"]
        victory_system.progress_history = victory_data["progress_history"].copy()
        
        # Restore victory achieved
        if victory_data["victory_achieved"]:
            victory_system.victory_achieved = VictoryType(victory_data["victory_achieved"])
        else:
            victory_system.victory_achieved = None
        
        # Restore victory conditions progress
        conditions_data = victory_data["victory_conditions"]
        for victory_type_str, condition_data in conditions_data.items():
            victory_type = VictoryType(victory_type_str)
            if victory_type in victory_system.victory_conditions:
                condition = victory_system.victory_conditions[victory_type]
                condition.current_progress = condition_data["current_progress"]
                condition.status = VictoryStatus(condition_data["status"])
                condition.turn_achieved = condition_data["turn_achieved"]
    
    def _restore_ai_system(self, ai_system: AISystem, ai_data: Dict[str, Any]):
        """Restore AI system state"""
        ai_system.action_probability = ai_data["action_probability"]
        ai_system.resource_generation_rate = ai_data["resource_generation_rate"]
        
        # Restore AI factions
        factions_data = ai_data["ai_factions"]
        ai_system.ai_factions.clear()
        
        for faction_name, faction_data in factions_data.items():
            ai_faction = AIFaction(
                faction_name=faction_data["faction_name"],
                personality=AIPersonality(faction_data["personality"]),
                controlled_stations=faction_data["controlled_stations"].copy()
            )
            
            # Restore faction state
            ai_faction.resources = faction_data["resources"].copy()
            ai_faction.action_history = faction_data["action_history"].copy()
            ai_faction.aggression_level = faction_data["aggression_level"]
            ai_faction.expansion_desire = faction_data["expansion_desire"]
            ai_faction.diplomatic_tendency = faction_data["diplomatic_tendency"]
            
            # Restore priorities
            priorities_data = faction_data["priorities"]
            ai_faction.priorities.clear()
            for action_str, priority in priorities_data.items():
                ai_faction.priorities[AIAction(action_str)] = priority
            
            ai_system.ai_factions[faction_name] = ai_faction
    
    def validate_loaded_state(self, game_state: GameStateManager) -> Dict[str, Any]:
        """
        Validate the loaded game state for consistency
        
        Args:
            game_state: Loaded GameStateManager instance
            
        Returns:
            Validation result with success status and any issues found
        """
        issues = []
        
        try:
            # Check basic state consistency
            if game_state.current_turn < 1:
                issues.append("Invalid turn number")
            
            if not game_state.player.controlled_stations:
                issues.append("Player has no controlled stations")
            
            # Check station consistency
            for station_name in game_state.player.controlled_stations:
                station = game_state.metro_map.get_station(station_name)
                if not station:
                    issues.append(f"Player controls non-existent station: {station_name}")
                elif station.controlling_faction != game_state.player.faction:
                    issues.append(f"Station {station_name} faction mismatch")
            
            # Check resource consistency
            if any(amount < 0 for amount in [
                game_state.player.resources.food,
                game_state.player.resources.clean_water,
                game_state.player.resources.scrap,
                game_state.player.resources.medicine,
                game_state.player.resources.mgr_rounds
            ]):
                issues.append("Player has negative resources")
            
            # Check military units consistency
            for unit in game_state.military_manager.units:
                if unit.stationed_at not in game_state.player.controlled_stations:
                    issues.append(f"Military unit stationed at uncontrolled station: {unit.stationed_at}")
            
            # Check victory system consistency
            if game_state.victory_system.game_ended and not game_state.victory_system.victory_achieved:
                issues.append("Game ended without victory type")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "issue_count": len(issues)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "issue_count": 1
            }