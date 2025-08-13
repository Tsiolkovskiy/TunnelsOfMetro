"""
AI System for Non-Player Factions
Manages AI behavior, decision making, and faction actions
"""

import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from data.station import Station
from data.infrastructure import BuildingType
from data.military_unit import UnitType, MilitaryManager
from systems.metro_map import MetroMap
from systems.diplomacy_system import DiplomaticAction


class AIPersonality(Enum):
    """AI personality types that affect decision making"""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    DIPLOMATIC = "diplomatic"
    ECONOMIC = "economic"
    EXPANSIONIST = "expansionist"
    ISOLATIONIST = "isolationist"


class AIAction(Enum):
    """Types of actions AI can take"""
    BUILD_INFRASTRUCTURE = "build_infrastructure"
    RECRUIT_UNITS = "recruit_units"
    ATTACK_ENEMY = "attack_enemy"
    IMPROVE_RELATIONS = "improve_relations"
    ESTABLISH_TRADE = "establish_trade"
    FORTIFY_STATION = "fortify_station"
    RESEARCH_TECHNOLOGY = "research_technology"
    EXPAND_TERRITORY = "expand_territory"


class AIFaction:
    """Represents an AI-controlled faction with behavior patterns"""
    
    def __init__(self, faction_name: str, personality: AIPersonality, controlled_stations: List[str]):
        """
        Initialize AI faction
        
        Args:
            faction_name: Name of the faction
            personality: AI personality type
            controlled_stations: List of stations controlled by this faction
        """
        self.faction_name = faction_name
        self.personality = personality
        self.controlled_stations = controlled_stations.copy()
        
        # AI state
        self.resources = {"food": 100, "clean_water": 50, "scrap": 75, "medicine": 25, "mgr_rounds": 100}
        self.military_manager = MilitaryManager(faction_name)
        self.priorities = self._initialize_priorities()
        self.action_history: List[Dict[str, Any]] = []
        
        # AI decision parameters
        self.aggression_level = self._get_aggression_level()
        self.expansion_desire = self._get_expansion_desire()
        self.diplomatic_tendency = self._get_diplomatic_tendency()
        
        self.logger = logging.getLogger(f"{__name__}.{faction_name}")
        self.logger.info(f"AI faction {faction_name} initialized with {personality.value} personality")
    
    def _initialize_priorities(self) -> Dict[AIAction, float]:
        """Initialize action priorities based on personality"""
        base_priorities = {
            AIAction.BUILD_INFRASTRUCTURE: 0.3,
            AIAction.RECRUIT_UNITS: 0.2,
            AIAction.ATTACK_ENEMY: 0.1,
            AIAction.IMPROVE_RELATIONS: 0.15,
            AIAction.ESTABLISH_TRADE: 0.1,
            AIAction.FORTIFY_STATION: 0.1,
            AIAction.RESEARCH_TECHNOLOGY: 0.05,
            AIAction.EXPAND_TERRITORY: 0.1
        }
        
        # Modify priorities based on personality
        if self.personality == AIPersonality.AGGRESSIVE:
            base_priorities[AIAction.ATTACK_ENEMY] = 0.3
            base_priorities[AIAction.RECRUIT_UNITS] = 0.25
            base_priorities[AIAction.IMPROVE_RELATIONS] = 0.05
        
        elif self.personality == AIPersonality.DEFENSIVE:
            base_priorities[AIAction.FORTIFY_STATION] = 0.3
            base_priorities[AIAction.RECRUIT_UNITS] = 0.25
            base_priorities[AIAction.ATTACK_ENEMY] = 0.05
        
        elif self.personality == AIPersonality.DIPLOMATIC:
            base_priorities[AIAction.IMPROVE_RELATIONS] = 0.35
            base_priorities[AIAction.ESTABLISH_TRADE] = 0.25
            base_priorities[AIAction.ATTACK_ENEMY] = 0.02
        
        elif self.personality == AIPersonality.ECONOMIC:
            base_priorities[AIAction.ESTABLISH_TRADE] = 0.3
            base_priorities[AIAction.BUILD_INFRASTRUCTURE] = 0.35
            base_priorities[AIAction.ATTACK_ENEMY] = 0.05
        
        elif self.personality == AIPersonality.EXPANSIONIST:
            base_priorities[AIAction.EXPAND_TERRITORY] = 0.25
            base_priorities[AIAction.ATTACK_ENEMY] = 0.2
            base_priorities[AIAction.RECRUIT_UNITS] = 0.2
        
        elif self.personality == AIPersonality.ISOLATIONIST:
            base_priorities[AIAction.BUILD_INFRASTRUCTURE] = 0.4
            base_priorities[AIAction.FORTIFY_STATION] = 0.25
            base_priorities[AIAction.IMPROVE_RELATIONS] = 0.05
            base_priorities[AIAction.ESTABLISH_TRADE] = 0.05
        
        return base_priorities
    
    def _get_aggression_level(self) -> float:
        """Get aggression level based on personality"""
        aggression_levels = {
            AIPersonality.AGGRESSIVE: 0.8,
            AIPersonality.DEFENSIVE: 0.2,
            AIPersonality.DIPLOMATIC: 0.3,
            AIPersonality.ECONOMIC: 0.4,
            AIPersonality.EXPANSIONIST: 0.7,
            AIPersonality.ISOLATIONIST: 0.1
        }
        return aggression_levels.get(self.personality, 0.5)
    
    def _get_expansion_desire(self) -> float:
        """Get expansion desire based on personality"""
        expansion_levels = {
            AIPersonality.AGGRESSIVE: 0.7,
            AIPersonality.DEFENSIVE: 0.3,
            AIPersonality.DIPLOMATIC: 0.5,
            AIPersonality.ECONOMIC: 0.6,
            AIPersonality.EXPANSIONIST: 0.9,
            AIPersonality.ISOLATIONIST: 0.1
        }
        return expansion_levels.get(self.personality, 0.5)
    
    def _get_diplomatic_tendency(self) -> float:
        """Get diplomatic tendency based on personality"""
        diplomatic_levels = {
            AIPersonality.AGGRESSIVE: 0.2,
            AIPersonality.DEFENSIVE: 0.4,
            AIPersonality.DIPLOMATIC: 0.9,
            AIPersonality.ECONOMIC: 0.7,
            AIPersonality.EXPANSIONIST: 0.3,
            AIPersonality.ISOLATIONIST: 0.2
        }
        return diplomatic_levels.get(self.personality, 0.5)


class AISystem:
    """
    AI system for managing non-player factions
    
    Features:
    - Turn advancement system with resource updates
    - Basic AI behavior for non-player factions
    - Faction action processing and conflict resolution
    - Personality-based decision making
    - Resource management and military actions
    """
    
    def __init__(self, metro_map: MetroMap):
        """
        Initialize AI system
        
        Args:
            metro_map: MetroMap instance
        """
        self.metro_map = metro_map
        self.logger = logging.getLogger(__name__)
        
        # AI factions
        self.ai_factions: Dict[str, AIFaction] = {}
        
        # AI decision parameters
        self.action_probability = 0.7  # Probability AI takes action each turn
        self.resource_generation_rate = 0.8  # AI resource generation multiplier
        
        # Initialize AI factions
        self._initialize_ai_factions()
        
        self.logger.info(f"AI system initialized with {len(self.ai_factions)} AI factions")
    
    def _initialize_ai_factions(self):
        """Initialize AI factions based on map stations"""
        # Define AI factions with their personalities
        faction_personalities = {
            "Red Line": AIPersonality.AGGRESSIVE,
            "Fourth Reich": AIPersonality.EXPANSIONIST,
            "Polis": AIPersonality.DIPLOMATIC,
            "Hanza": AIPersonality.ECONOMIC,
            "Independent": AIPersonality.DEFENSIVE
        }
        
        # Group stations by faction
        faction_stations = {}
        for station_name, station in self.metro_map.stations.items():
            faction = station.controlling_faction
            if faction != "Rangers":  # Don't create AI for player faction
                if faction not in faction_stations:
                    faction_stations[faction] = []
                faction_stations[faction].append(station_name)
        
        # Create AI factions
        for faction_name, stations in faction_stations.items():
            personality = faction_personalities.get(faction_name, AIPersonality.DEFENSIVE)
            ai_faction = AIFaction(faction_name, personality, stations)
            self.ai_factions[faction_name] = ai_faction
            
            self.logger.info(f"Created AI faction: {faction_name} ({personality.value}) with {len(stations)} stations")
    
    def process_ai_turn(self, current_turn: int, diplomacy_system, combat_system, trade_system):
        """
        Process AI actions for all factions
        
        Args:
            current_turn: Current game turn
            diplomacy_system: Diplomacy system reference
            combat_system: Combat system reference
            trade_system: Trade system reference
        """
        self.logger.info(f"Processing AI turn {current_turn}")
        
        for faction_name, ai_faction in self.ai_factions.items():
            self._process_faction_turn(ai_faction, current_turn, diplomacy_system, combat_system, trade_system)
    
    def _process_faction_turn(self, ai_faction: AIFaction, current_turn: int, 
                            diplomacy_system, combat_system, trade_system):
        """Process a single AI faction's turn"""
        # Generate resources for AI faction
        self._generate_ai_resources(ai_faction)
        
        # Decide on actions to take
        actions = self._decide_faction_actions(ai_faction, current_turn)
        
        # Execute actions
        for action in actions:
            self._execute_ai_action(ai_faction, action, diplomacy_system, combat_system, trade_system)
        
        # Update faction state
        self._update_faction_state(ai_faction, current_turn)
    
    def _generate_ai_resources(self, ai_faction: AIFaction):
        """Generate resources for AI faction"""
        # Simple resource generation based on controlled stations
        base_generation = {
            "food": len(ai_faction.controlled_stations) * 8,
            "clean_water": len(ai_faction.controlled_stations) * 5,
            "scrap": len(ai_faction.controlled_stations) * 6,
            "medicine": len(ai_faction.controlled_stations) * 3,
            "mgr_rounds": len(ai_faction.controlled_stations) * 2
        }
        
        # Apply generation rate modifier
        for resource, amount in base_generation.items():
            generated = int(amount * self.resource_generation_rate)
            ai_faction.resources[resource] = ai_faction.resources.get(resource, 0) + generated
        
        # Cap resources to prevent infinite accumulation
        resource_caps = {"food": 500, "clean_water": 300, "scrap": 400, "medicine": 200, "mgr_rounds": 300}
        for resource, cap in resource_caps.items():
            ai_faction.resources[resource] = min(ai_faction.resources[resource], cap)
    
    def _decide_faction_actions(self, ai_faction: AIFaction, current_turn: int) -> List[Dict[str, Any]]:
        """Decide what actions the AI faction should take"""
        actions = []
        
        # Check if AI should take action this turn
        if random.random() > self.action_probability:
            return actions
        
        # Evaluate possible actions based on priorities and current state
        possible_actions = self._evaluate_possible_actions(ai_faction, current_turn)
        
        # Select actions based on priorities and resources
        selected_actions = self._select_actions(ai_faction, possible_actions)
        
        return selected_actions
    
    def _evaluate_possible_actions(self, ai_faction: AIFaction, current_turn: int) -> List[Dict[str, Any]]:
        """Evaluate all possible actions for the AI faction"""
        possible_actions = []
        
        # Infrastructure building actions
        for station_name in ai_faction.controlled_stations:
            station = self.metro_map.get_station(station_name)
            if station and len(station.infrastructure) < 3:  # Station has capacity
                # Prioritize based on personality
                if ai_faction.personality == AIPersonality.ECONOMIC:
                    building_types = [BuildingType.MARKET, BuildingType.SCRAP_WORKSHOP, BuildingType.MUSHROOM_FARM]
                elif ai_faction.personality == AIPersonality.DEFENSIVE:
                    building_types = [BuildingType.FORTIFICATIONS, BuildingType.BARRACKS, BuildingType.MED_BAY]
                elif ai_faction.personality == AIPersonality.AGGRESSIVE:
                    building_types = [BuildingType.BARRACKS, BuildingType.FORTIFICATIONS, BuildingType.SCRAP_WORKSHOP]
                else:
                    building_types = [BuildingType.MUSHROOM_FARM, BuildingType.WATER_FILTER, BuildingType.MED_BAY]
                
                for building_type in building_types:
                    if building_type not in station.infrastructure:
                        possible_actions.append({
                            "type": AIAction.BUILD_INFRASTRUCTURE,
                            "station": station_name,
                            "building_type": building_type,
                            "priority": ai_faction.priorities[AIAction.BUILD_INFRASTRUCTURE],
                            "cost": self._estimate_building_cost(building_type)
                        })
                        break  # Only consider one building per station per turn
        
        # Military recruitment actions
        if ai_faction.resources.get("mgr_rounds", 0) > 50:  # Only if AI has sufficient MGR
            for station_name in ai_faction.controlled_stations:
                station = self.metro_map.get_station(station_name)
                if station and station.population > 80:
                    # Choose unit type based on personality
                    if ai_faction.personality == AIPersonality.AGGRESSIVE:
                        unit_types = [UnitType.STORMTROOPERS, UnitType.CONSCRIPTS, UnitType.MILITIA]
                    elif ai_faction.personality == AIPersonality.DEFENSIVE:
                        unit_types = [UnitType.MILITIA, UnitType.CONSCRIPTS, UnitType.SCOUTS]
                    else:
                        unit_types = [UnitType.MILITIA, UnitType.SCOUTS, UnitType.CONSCRIPTS]
                    
                    for unit_type in unit_types:
                        if self._can_ai_recruit_unit(ai_faction, unit_type, station):
                            possible_actions.append({
                                "type": AIAction.RECRUIT_UNITS,
                                "station": station_name,
                                "unit_type": unit_type,
                                "priority": ai_faction.priorities[AIAction.RECRUIT_UNITS],
                                "cost": self._estimate_recruitment_cost(unit_type)
                            })
                            break  # Only consider one unit type per station
        
        # Diplomatic actions
        if ai_faction.diplomatic_tendency > 0.4:
            possible_actions.append({
                "type": AIAction.IMPROVE_RELATIONS,
                "target_faction": "Rangers",  # Focus on player for now
                "priority": ai_faction.priorities[AIAction.IMPROVE_RELATIONS],
                "cost": {"mgr_rounds": 15}
            })
        
        # Military actions (if aggressive enough)
        if ai_faction.aggression_level > 0.5 and ai_faction.resources.get("mgr_rounds", 0) > 100:
            # Look for weak enemy stations to attack
            enemy_stations = self._find_attack_targets(ai_faction)
            if enemy_stations:
                target = random.choice(enemy_stations)
                possible_actions.append({
                    "type": AIAction.ATTACK_ENEMY,
                    "origin": random.choice(ai_faction.controlled_stations),
                    "target": target,
                    "priority": ai_faction.priorities[AIAction.ATTACK_ENEMY],
                    "cost": {"mgr_rounds": 75}
                })
        
        return possible_actions
    
    def _select_actions(self, ai_faction: AIFaction, possible_actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Select actions to execute based on priorities and resources"""
        if not possible_actions:
            return []
        
        # Sort actions by priority
        possible_actions.sort(key=lambda x: x["priority"], reverse=True)
        
        selected_actions = []
        remaining_resources = ai_faction.resources.copy()
        
        # Select actions while resources allow
        for action in possible_actions:
            cost = action.get("cost", {})
            
            # Check if AI can afford this action
            can_afford = True
            for resource, amount in cost.items():
                if remaining_resources.get(resource, 0) < amount:
                    can_afford = False
                    break
            
            if can_afford:
                # Deduct cost from remaining resources
                for resource, amount in cost.items():
                    remaining_resources[resource] -= amount
                
                selected_actions.append(action)
                
                # Limit actions per turn
                if len(selected_actions) >= 2:
                    break
        
        return selected_actions
    
    def _execute_ai_action(self, ai_faction: AIFaction, action: Dict[str, Any], 
                          diplomacy_system, combat_system, trade_system):
        """Execute a specific AI action"""
        action_type = action["type"]
        
        try:
            if action_type == AIAction.BUILD_INFRASTRUCTURE:
                self._execute_build_action(ai_faction, action)
            
            elif action_type == AIAction.RECRUIT_UNITS:
                self._execute_recruit_action(ai_faction, action)
            
            elif action_type == AIAction.IMPROVE_RELATIONS:
                self._execute_diplomacy_action(ai_faction, action, diplomacy_system)
            
            elif action_type == AIAction.ATTACK_ENEMY:
                self._execute_attack_action(ai_faction, action, combat_system)
            
            elif action_type == AIAction.FORTIFY_STATION:
                self._execute_fortify_action(ai_faction, action)
            
            # Record action in history
            action_record = {
                "turn": len(ai_faction.action_history) + 1,
                "action": action_type.value,
                "details": action,
                "success": True
            }
            ai_faction.action_history.append(action_record)
            
            self.logger.info(f"{ai_faction.faction_name} executed {action_type.value}")
        
        except Exception as e:
            self.logger.error(f"Failed to execute AI action {action_type.value} for {ai_faction.faction_name}: {e}")
    
    def _execute_build_action(self, ai_faction: AIFaction, action: Dict[str, Any]):
        """Execute building construction action"""
        station_name = action["station"]
        building_type = action["building_type"]
        cost = action["cost"]
        
        # Deduct resources
        for resource, amount in cost.items():
            ai_faction.resources[resource] -= amount
        
        # Add building to station
        station = self.metro_map.get_station(station_name)
        if station:
            station.add_infrastructure(building_type, 1)
            self.logger.info(f"{ai_faction.faction_name} built {building_type.value} at {station_name}")
    
    def _execute_recruit_action(self, ai_faction: AIFaction, action: Dict[str, Any]):
        """Execute unit recruitment action"""
        station_name = action["station"]
        unit_type = action["unit_type"]
        cost = action["cost"]
        
        # Deduct resources
        for resource, amount in cost.items():
            ai_faction.resources[resource] -= amount
        
        # Recruit unit
        success, message, unit = ai_faction.military_manager.recruit_unit(unit_type, station_name, ai_faction.resources)
        if success:
            self.logger.info(f"{ai_faction.faction_name} recruited {unit_type.value} at {station_name}")
    
    def _execute_diplomacy_action(self, ai_faction: AIFaction, action: Dict[str, Any], diplomacy_system):
        """Execute diplomatic action"""
        target_faction = action["target_faction"]
        cost = action.get("cost", {})
        
        # Deduct resources
        for resource, amount in cost.items():
            ai_faction.resources[resource] -= amount
        
        # Execute diplomatic action
        if diplomacy_system:
            result = diplomacy_system.execute_diplomatic_action(
                ai_faction.faction_name, target_faction, DiplomaticAction.IMPROVE_RELATIONS,
                len(ai_faction.action_history) + 1, 15
            )
            
            if result["success"]:
                self.logger.info(f"{ai_faction.faction_name} improved relations with {target_faction}")
    
    def _execute_attack_action(self, ai_faction: AIFaction, action: Dict[str, Any], combat_system):
        """Execute attack action"""
        origin = action["origin"]
        target = action["target"]
        cost = action.get("cost", {})
        
        # Deduct resources
        for resource, amount in cost.items():
            ai_faction.resources[resource] -= amount
        
        # Execute attack (simplified - would need full integration)
        self.logger.info(f"{ai_faction.faction_name} attempted attack from {origin} to {target}")
    
    def _execute_fortify_action(self, ai_faction: AIFaction, action: Dict[str, Any]):
        """Execute fortification action"""
        station_name = action["station"]
        
        # Simple fortification
        station = self.metro_map.get_station(station_name)
        if station:
            station.defensive_value += 5
            ai_faction.resources["scrap"] -= 20
            self.logger.info(f"{ai_faction.faction_name} fortified {station_name}")
    
    def _update_faction_state(self, ai_faction: AIFaction, current_turn: int):
        """Update AI faction state"""
        # Update controlled stations list
        current_stations = []
        for station_name, station in self.metro_map.stations.items():
            if station.controlling_faction == ai_faction.faction_name:
                current_stations.append(station_name)
        
        ai_faction.controlled_stations = current_stations
        
        # Adjust priorities based on current situation
        self._adjust_faction_priorities(ai_faction, current_turn)
    
    def _adjust_faction_priorities(self, ai_faction: AIFaction, current_turn: int):
        """Dynamically adjust faction priorities based on situation"""
        # Increase military focus if under threat
        enemy_nearby = self._count_nearby_enemies(ai_faction)
        if enemy_nearby > 2:
            ai_faction.priorities[AIAction.RECRUIT_UNITS] *= 1.5
            ai_faction.priorities[AIAction.FORTIFY_STATION] *= 1.3
        
        # Increase diplomatic focus if isolated
        if len(ai_faction.controlled_stations) < 3:
            ai_faction.priorities[AIAction.IMPROVE_RELATIONS] *= 1.4
        
        # Increase expansion focus if strong
        if len(ai_faction.controlled_stations) > 5:
            ai_faction.priorities[AIAction.EXPAND_TERRITORY] *= 1.2
    
    def _count_nearby_enemies(self, ai_faction: AIFaction) -> int:
        """Count enemy stations near AI faction territory"""
        enemy_count = 0
        
        for station_name in ai_faction.controlled_stations:
            # Get adjacent stations
            adjacent = self.metro_map.get_adjacent_stations(station_name)
            for adj_station_name in adjacent:
                adj_station = self.metro_map.get_station(adj_station_name)
                if adj_station and adj_station.controlling_faction != ai_faction.faction_name:
                    # Check if hostile
                    if adj_station.controlling_faction == "Rangers":  # Player is potential threat
                        enemy_count += 1
        
        return enemy_count
    
    def _find_attack_targets(self, ai_faction: AIFaction) -> List[str]:
        """Find potential attack targets for AI faction"""
        targets = []
        
        for station_name in ai_faction.controlled_stations:
            adjacent = self.metro_map.get_adjacent_stations(station_name)
            for adj_station_name in adjacent:
                adj_station = self.metro_map.get_station(adj_station_name)
                if adj_station and adj_station.controlling_faction != ai_faction.faction_name:
                    # Consider weak stations as targets
                    if adj_station.population < 100 or adj_station.morale < 50:
                        targets.append(adj_station_name)
        
        return targets
    
    def _can_ai_recruit_unit(self, ai_faction: AIFaction, unit_type: UnitType, station: Station) -> bool:
        """Check if AI can recruit a specific unit type"""
        # Simplified recruitment check
        recruitment_costs = {
            UnitType.MILITIA: {"food": 5, "scrap": 3},
            UnitType.CONSCRIPTS: {"food": 8, "scrap": 5, "medicine": 2},
            UnitType.SCOUTS: {"food": 10, "scrap": 8},
            UnitType.STORMTROOPERS: {"food": 20, "scrap": 15, "medicine": 8, "mgr_rounds": 5}
        }
        
        cost = recruitment_costs.get(unit_type, {})
        
        # Check resources
        for resource, amount in cost.items():
            if ai_faction.resources.get(resource, 0) < amount:
                return False
        
        # Check population
        if station.population < 50:
            return False
        
        return True
    
    def _estimate_building_cost(self, building_type: BuildingType) -> Dict[str, int]:
        """Estimate cost for building construction"""
        building_costs = {
            BuildingType.MUSHROOM_FARM: {"scrap": 15, "clean_water": 5},
            BuildingType.WATER_FILTER: {"scrap": 25, "mgr_rounds": 2},
            BuildingType.SCRAP_WORKSHOP: {"scrap": 20, "food": 10},
            BuildingType.MED_BAY: {"scrap": 35, "clean_water": 15, "mgr_rounds": 3},
            BuildingType.BARRACKS: {"scrap": 50, "food": 20, "mgr_rounds": 8},
            BuildingType.FORTIFICATIONS: {"scrap": 75, "mgr_rounds": 12},
            BuildingType.MARKET: {"scrap": 40, "food": 25, "mgr_rounds": 15}
        }
        return building_costs.get(building_type, {"scrap": 20})
    
    def _estimate_recruitment_cost(self, unit_type: UnitType) -> Dict[str, int]:
        """Estimate cost for unit recruitment"""
        recruitment_costs = {
            UnitType.MILITIA: {"food": 5, "scrap": 3},
            UnitType.CONSCRIPTS: {"food": 8, "scrap": 5, "medicine": 2},
            UnitType.SCOUTS: {"food": 10, "scrap": 8},
            UnitType.STORMTROOPERS: {"food": 20, "scrap": 15, "medicine": 8, "mgr_rounds": 5}
        }
        return recruitment_costs.get(unit_type, {"food": 5, "scrap": 3})
    
    def get_ai_faction_info(self, faction_name: str) -> Optional[Dict[str, Any]]:
        """Get information about an AI faction"""
        ai_faction = self.ai_factions.get(faction_name)
        if not ai_faction:
            return None
        
        return {
            "faction_name": ai_faction.faction_name,
            "personality": ai_faction.personality.value,
            "controlled_stations": ai_faction.controlled_stations.copy(),
            "resources": ai_faction.resources.copy(),
            "aggression_level": ai_faction.aggression_level,
            "expansion_desire": ai_faction.expansion_desire,
            "diplomatic_tendency": ai_faction.diplomatic_tendency,
            "action_count": len(ai_faction.action_history),
            "military_units": len(ai_faction.military_manager.units)
        }
    
    def get_all_ai_factions_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all AI factions"""
        return {
            faction_name: self.get_ai_faction_info(faction_name)
            for faction_name in self.ai_factions.keys()
        }
    
    def get_ai_statistics(self) -> Dict[str, Any]:
        """Get AI system statistics"""
        total_actions = sum(len(faction.action_history) for faction in self.ai_factions.values())
        total_stations = sum(len(faction.controlled_stations) for faction in self.ai_factions.values())
        total_units = sum(len(faction.military_manager.units) for faction in self.ai_factions.values())
        
        return {
            "ai_factions": len(self.ai_factions),
            "total_actions_taken": total_actions,
            "total_ai_stations": total_stations,
            "total_ai_units": total_units,
            "action_probability": self.action_probability,
            "resource_generation_rate": self.resource_generation_rate
        }