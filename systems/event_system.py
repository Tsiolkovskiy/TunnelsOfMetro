"""
Dynamic Event System
Manages random and scripted events that affect the Metro world
"""

import logging
import random
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field

from data.station import Station
from data.tunnel import TunnelState
from data.infrastructure import BuildingType
from systems.metro_map import MetroMap


class EventCategory(Enum):
    """Categories of events that can occur"""
    ENVIRONMENTAL = "environmental"
    POLITICAL = "political"
    ECONOMIC = "economic"
    MILITARY = "military"
    SOCIAL = "social"
    ANOMALOUS = "anomalous"


class EventSeverity(Enum):
    """Severity levels for events"""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CATASTROPHIC = "catastrophic"


class EventScope(Enum):
    """Scope of event effects"""
    STATION = "station"
    TUNNEL = "tunnel"
    LINE = "line"
    REGION = "region"
    GLOBAL = "global"


@dataclass
class EventChoice:
    """Represents a choice the player can make in response to an event"""
    choice_id: str
    description: str
    requirements: Dict[str, Any] = field(default_factory=dict)
    costs: Dict[str, int] = field(default_factory=dict)
    effects: Dict[str, Any] = field(default_factory=dict)
    probability_modifier: float = 1.0


@dataclass
class GameEvent:
    """Represents a game event with all its properties"""
    event_id: str
    title: str
    description: str
    category: EventCategory
    severity: EventSeverity
    scope: EventScope
    
    # Event mechanics
    probability: float
    duration: int = 1  # Duration in turns
    cooldown: int = 0  # Turns before event can occur again
    
    # Requirements and conditions
    requirements: Dict[str, Any] = field(default_factory=dict)
    
    # Effects
    immediate_effects: Dict[str, Any] = field(default_factory=dict)
    ongoing_effects: Dict[str, Any] = field(default_factory=dict)
    
    # Player choices
    choices: List[EventChoice] = field(default_factory=list)
    
    # Metadata
    flavor_text: List[str] = field(default_factory=list)
    historical: bool = False  # Can only happen once


class EventSystem:
    """
    Dynamic event system for the Metro universe
    
    Features:
    - Random event generation with probability-based triggering
    - Multiple event categories (environmental, political, economic, military)
    - Event effects on stations, tunnels, and faction relationships
    - Player choice events with consequences
    - Event chains and dependencies
    - Historical events that can only occur once
    """
    
    def __init__(self, metro_map: MetroMap):
        """
        Initialize event system
        
        Args:
            metro_map: MetroMap instance
        """
        self.metro_map = metro_map
        self.logger = logging.getLogger(__name__)
        
        # Event tracking
        self.active_events: List[Dict[str, Any]] = []
        self.event_history: List[Dict[str, Any]] = []
        self.event_cooldowns: Dict[str, int] = {}
        self.triggered_historical_events: set = set()
        
        # Event probability modifiers
        self.category_modifiers: Dict[EventCategory, float] = {
            EventCategory.ENVIRONMENTAL: 1.0,
            EventCategory.POLITICAL: 1.0,
            EventCategory.ECONOMIC: 1.0,
            EventCategory.MILITARY: 1.0,
            EventCategory.SOCIAL: 1.0,
            EventCategory.ANOMALOUS: 0.5  # Rare by default
        }
        
        # Initialize event database
        self.events: Dict[str, GameEvent] = {}
        self._initialize_events()
        
        self.logger.info("Event system initialized with {} events".format(len(self.events)))
    
    def _initialize_events(self):
        """Initialize the database of possible events"""
        
        # Environmental Events
        self.events["tunnel_collapse"] = GameEvent(
            event_id="tunnel_collapse",
            title="Tunnel Collapse",
            description="A section of tunnel has collapsed, blocking passage and trapping travelers.",
            category=EventCategory.ENVIRONMENTAL,
            severity=EventSeverity.MODERATE,
            scope=EventScope.TUNNEL,
            probability=0.05,
            duration=3,
            cooldown=10,
            immediate_effects={
                "block_tunnel": True,
                "casualties": {"min": 5, "max": 20}
            },
            choices=[
                EventChoice(
                    choice_id="clear_debris",
                    description="Send work crews to clear the debris",
                    costs={"scrap": 30, "mgr_rounds": 5},
                    effects={"clear_tunnel": True, "duration_reduction": 2}
                ),
                EventChoice(
                    choice_id="find_alternate",
                    description="Find alternate routes and wait",
                    effects={"trade_disruption": 0.5}
                )
            ],
            flavor_text=[
                "The rumble echoes through the tunnels as tons of concrete and steel crash down.",
                "Dust clouds billow through the Metro, carrying the acrid smell of destruction.",
                "Emergency crews rush to the scene, but the damage is extensive."
            ]
        )
        
        self.events["radiation_storm"] = GameEvent(
            event_id="radiation_storm",
            title="Radiation Storm",
            description="A massive radiation storm sweeps across the surface, affecting all Metro stations.",
            category=EventCategory.ENVIRONMENTAL,
            severity=EventSeverity.MAJOR,
            scope=EventScope.GLOBAL,
            probability=0.02,
            duration=2,
            cooldown=20,
            immediate_effects={
                "radiation_exposure": True,
                "surface_access_blocked": True
            },
            ongoing_effects={
                "medicine_consumption": 2.0,  # Double medicine consumption
                "morale_penalty": -10
            },
            choices=[
                EventChoice(
                    choice_id="seal_stations",
                    description="Seal all station entrances and distribute medicine",
                    costs={"medicine": 50, "scrap": 20},
                    effects={"radiation_protection": True, "morale_bonus": 5}
                ),
                EventChoice(
                    choice_id="weather_storm",
                    description="Endure the storm with minimal intervention",
                    effects={"population_loss": {"min": 10, "max": 30}}
                )
            ]
        )
        
        self.events["mutant_infestation"] = GameEvent(
            event_id="mutant_infestation",
            title="Mutant Infestation",
            description="A pack of mutants has taken up residence in a tunnel section, making travel dangerous.",
            category=EventCategory.ENVIRONMENTAL,
            severity=EventSeverity.MODERATE,
            scope=EventScope.TUNNEL,
            probability=0.08,
            duration=5,
            cooldown=8,
            requirements={
                "tunnel_state": [TunnelState.CLEAR, TunnelState.HAZARDOUS]
            },
            immediate_effects={
                "tunnel_state": TunnelState.INFESTED,
                "travel_danger": True
            },
            choices=[
                EventChoice(
                    choice_id="military_sweep",
                    description="Send military units to clear the mutants",
                    requirements={"military_units": 2},
                    costs={"mgr_rounds": 15},
                    effects={"clear_infestation": True, "casualties": {"min": 1, "max": 3}}
                ),
                EventChoice(
                    choice_id="hire_stalkers",
                    description="Hire Stalkers to deal with the problem",
                    costs={"mgr_rounds": 25, "food": 20},
                    effects={"clear_infestation": True}
                ),
                EventChoice(
                    choice_id="avoid_area",
                    description="Mark the area as dangerous and find alternate routes",
                    effects={"trade_disruption": 0.3, "tunnel_permanent_hazard": True}
                )
            ]
        )
        
        # Political Events
        self.events["faction_uprising"] = GameEvent(
            event_id="faction_uprising",
            title="Faction Uprising",
            description="Dissidents within a station have risen up against the current leadership.",
            category=EventCategory.POLITICAL,
            severity=EventSeverity.MAJOR,
            scope=EventScope.STATION,
            probability=0.03,
            duration=1,
            cooldown=15,
            requirements={
                "station_morale": {"max": 40}
            },
            immediate_effects={
                "civil_unrest": True,
                "production_halt": True
            },
            choices=[
                EventChoice(
                    choice_id="military_intervention",
                    description="Send military forces to restore order",
                    requirements={"military_units": 3},
                    costs={"mgr_rounds": 20},
                    effects={"restore_order": True, "morale_penalty": -15, "population_loss": {"min": 20, "max": 50}}
                ),
                EventChoice(
                    choice_id="negotiate",
                    description="Attempt to negotiate with the rebels",
                    costs={"food": 30, "mgr_rounds": 10},
                    effects={"restore_order": True, "morale_bonus": 10},
                    probability_modifier=0.7
                ),
                EventChoice(
                    choice_id="grant_autonomy",
                    description="Grant the station semi-autonomous status",
                    effects={"lose_station_control": True, "diplomatic_bonus": 20}
                )
            ]
        )
        
        self.events["diplomatic_crisis"] = GameEvent(
            event_id="diplomatic_crisis",
            title="Diplomatic Crisis",
            description="A diplomatic incident has strained relationships with a neighboring faction.",
            category=EventCategory.POLITICAL,
            severity=EventSeverity.MODERATE,
            scope=EventScope.GLOBAL,
            probability=0.06,
            duration=1,
            cooldown=12,
            immediate_effects={
                "relationship_penalty": -30,
                "trade_sanctions": True
            },
            choices=[
                EventChoice(
                    choice_id="formal_apology",
                    description="Issue a formal apology and offer reparations",
                    costs={"mgr_rounds": 30, "food": 50},
                    effects={"relationship_bonus": 20, "reputation_penalty": -5}
                ),
                EventChoice(
                    choice_id="stand_firm",
                    description="Refuse to back down and prepare for consequences",
                    effects={"relationship_penalty": -20, "military_readiness": True}
                ),
                EventChoice(
                    choice_id="seek_mediation",
                    description="Seek mediation from a neutral faction",
                    costs={"mgr_rounds": 15},
                    effects={"relationship_bonus": 10},
                    probability_modifier=0.8
                )
            ]
        )
        
        # Economic Events
        self.events["resource_discovery"] = GameEvent(
            event_id="resource_discovery",
            title="Resource Discovery",
            description="Scavengers have discovered a cache of pre-war supplies in an abandoned section.",
            category=EventCategory.ECONOMIC,
            severity=EventSeverity.MINOR,
            scope=EventScope.STATION,
            probability=0.12,
            duration=1,
            cooldown=5,
            immediate_effects={
                "resource_bonus": {
                    "food": {"min": 20, "max": 50},
                    "scrap": {"min": 30, "max": 80},
                    "medicine": {"min": 10, "max": 25},
                    "mgr_rounds": {"min": 5, "max": 15}
                }
            },
            choices=[
                EventChoice(
                    choice_id="claim_all",
                    description="Claim all resources for your faction",
                    effects={"full_resource_bonus": True, "reputation_penalty": -10}
                ),
                EventChoice(
                    choice_id="share_discovery",
                    description="Share the discovery with neighboring stations",
                    effects={"partial_resource_bonus": True, "reputation_bonus": 15, "relationship_bonus": 10}
                ),
                EventChoice(
                    choice_id="trade_discovery",
                    description="Trade the information for immediate benefits",
                    effects={"mgr_bonus": 50, "reputation_bonus": 5}
                )
            ]
        )
        
        self.events["trade_caravan"] = GameEvent(
            event_id="trade_caravan",
            title="Merchant Caravan",
            description="A well-equipped merchant caravan has arrived, offering rare goods for trade.",
            category=EventCategory.ECONOMIC,
            severity=EventSeverity.MINOR,
            scope=EventScope.STATION,
            probability=0.15,
            duration=1,
            cooldown=3,
            choices=[
                EventChoice(
                    choice_id="buy_supplies",
                    description="Purchase medical supplies and equipment",
                    costs={"mgr_rounds": 40},
                    effects={"medicine_bonus": 30, "equipment_bonus": True}
                ),
                EventChoice(
                    choice_id="buy_weapons",
                    description="Purchase weapons and ammunition",
                    costs={"mgr_rounds": 60},
                    effects={"military_equipment": True, "mgr_rounds": 20}
                ),
                EventChoice(
                    choice_id="sell_goods",
                    description="Sell excess resources to the caravan",
                    costs={"food": 50, "scrap": 30},
                    effects={"mgr_rounds": 80}
                ),
                EventChoice(
                    choice_id="decline_trade",
                    description="Politely decline to trade",
                    effects={}
                )
            ]
        )
        
        # Military Events
        self.events["bandit_raid"] = GameEvent(
            event_id="bandit_raid",
            title="Bandit Raid",
            description="A group of well-armed bandits is threatening a station, demanding tribute.",
            category=EventCategory.MILITARY,
            severity=EventSeverity.MODERATE,
            scope=EventScope.STATION,
            probability=0.07,
            duration=1,
            cooldown=8,
            immediate_effects={
                "under_threat": True
            },
            choices=[
                EventChoice(
                    choice_id="fight_bandits",
                    description="Fight off the bandits with your military forces",
                    requirements={"military_units": 2},
                    effects={"bandit_defeat": True, "casualties": {"min": 1, "max": 5}, "reputation_bonus": 10}
                ),
                EventChoice(
                    choice_id="pay_tribute",
                    description="Pay the bandits to leave peacefully",
                    costs={"mgr_rounds": 30, "food": 40},
                    effects={"bandit_appeasement": True, "reputation_penalty": -5}
                ),
                EventChoice(
                    choice_id="negotiate",
                    description="Try to negotiate with the bandit leader",
                    costs={"mgr_rounds": 15},
                    effects={"bandit_deal": True},
                    probability_modifier=0.6
                ),
                EventChoice(
                    choice_id="call_for_help",
                    description="Call for military assistance from allies",
                    requirements={"allied_factions": 1},
                    costs={"mgr_rounds": 20},
                    effects={"allied_intervention": True, "relationship_bonus": 5}
                )
            ]
        )
        
        # Social Events
        self.events["population_boom"] = GameEvent(
            event_id="population_boom",
            title="Population Boom",
            description="A group of refugees has arrived, seeking shelter and a new home.",
            category=EventCategory.SOCIAL,
            severity=EventSeverity.MINOR,
            scope=EventScope.STATION,
            probability=0.10,
            duration=1,
            cooldown=6,
            requirements={
                "station_morale": {"min": 60}
            },
            immediate_effects={
                "refugee_arrival": True
            },
            choices=[
                EventChoice(
                    choice_id="welcome_refugees",
                    description="Welcome the refugees and integrate them into the community",
                    costs={"food": 30, "clean_water": 20},
                    effects={"population_bonus": {"min": 20, "max": 40}, "morale_bonus": 10}
                ),
                EventChoice(
                    choice_id="selective_acceptance",
                    description="Accept only skilled workers and specialists",
                    costs={"food": 15, "mgr_rounds": 10},
                    effects={"population_bonus": {"min": 10, "max": 20}, "skill_bonus": True}
                ),
                EventChoice(
                    choice_id="turn_away",
                    description="Turn the refugees away due to resource constraints",
                    effects={"morale_penalty": -15, "reputation_penalty": -10}
                )
            ]
        )
        
        # Anomalous Events
        self.events["anomalous_activity"] = GameEvent(
            event_id="anomalous_activity",
            title="Anomalous Activity",
            description="Strange phenomena have been reported in a tunnel section - reality seems unstable.",
            category=EventCategory.ANOMALOUS,
            severity=EventSeverity.MAJOR,
            scope=EventScope.TUNNEL,
            probability=0.01,
            duration=10,
            cooldown=30,
            immediate_effects={
                "tunnel_state": TunnelState.ANOMALOUS,
                "reality_distortion": True
            },
            ongoing_effects={
                "strange_effects": True,
                "stalker_interest": True
            },
            choices=[
                EventChoice(
                    choice_id="scientific_study",
                    description="Send scientists to study the anomaly",
                    requirements={"library": True},
                    costs={"medicine": 20, "mgr_rounds": 30},
                    effects={"anomaly_research": True, "technology_bonus": True}
                ),
                EventChoice(
                    choice_id="seal_area",
                    description="Seal off the affected area completely",
                    costs={"scrap": 50},
                    effects={"tunnel_sealed": True, "anomaly_contained": True}
                ),
                EventChoice(
                    choice_id="exploit_anomaly",
                    description="Try to exploit the anomaly for resources",
                    effects={"anomaly_exploitation": True, "random_effects": True},
                    probability_modifier=0.4
                )
            ]
        )
        
        # Historical Events (can only happen once)
        self.events["great_library_discovery"] = GameEvent(
            event_id="great_library_discovery",
            title="The Great Library Discovery",
            description="Explorers have discovered the ruins of the State Library with intact pre-war archives.",
            category=EventCategory.ECONOMIC,
            severity=EventSeverity.MAJOR,
            scope=EventScope.GLOBAL,
            probability=0.005,
            duration=1,
            cooldown=0,
            historical=True,
            requirements={
                "turn": {"min": 20}  # Only after turn 20
            },
            immediate_effects={
                "knowledge_cache": True,
                "technology_advancement": True
            },
            choices=[
                EventChoice(
                    choice_id="claim_library",
                    description="Claim the library for your faction exclusively",
                    costs={"military_units": 5, "mgr_rounds": 100},
                    effects={"library_control": True, "technology_monopoly": True, "reputation_penalty": -30}
                ),
                EventChoice(
                    choice_id="share_knowledge",
                    description="Share the discovery with all Metro factions",
                    effects={"global_technology_bonus": True, "reputation_bonus": 50, "relationship_bonus": 30}
                ),
                EventChoice(
                    choice_id="form_consortium",
                    description="Form a research consortium with allied factions",
                    requirements={"allied_factions": 2},
                    effects={"research_consortium": True, "technology_bonus": True, "relationship_bonus": 20}
                )
            ]
        ) 
   
    def process_turn_events(self, current_turn: int, faction_stations: List[Station]) -> List[Dict[str, Any]]:
        """
        Process events for the current turn
        
        Args:
            current_turn: Current game turn
            faction_stations: List of player-controlled stations
            
        Returns:
            List of triggered events
        """
        triggered_events = []
        
        # Update cooldowns
        self._update_cooldowns()
        
        # Process ongoing events
        self._process_ongoing_events()
        
        # Check for new random events
        new_events = self._check_random_events(current_turn, faction_stations)
        triggered_events.extend(new_events)
        
        # Check for scripted events
        scripted_events = self._check_scripted_events(current_turn, faction_stations)
        triggered_events.extend(scripted_events)
        
        # Log triggered events
        for event_data in triggered_events:
            self.logger.info(f"Event triggered: {event_data['title']}")
        
        return triggered_events
    
    def _update_cooldowns(self):
        """Update event cooldowns"""
        for event_id in list(self.event_cooldowns.keys()):
            self.event_cooldowns[event_id] -= 1
            if self.event_cooldowns[event_id] <= 0:
                del self.event_cooldowns[event_id]
    
    def _process_ongoing_events(self):
        """Process ongoing events and remove expired ones"""
        active_events = []
        
        for event_data in self.active_events:
            event_data["remaining_duration"] -= 1
            
            if event_data["remaining_duration"] > 0:
                active_events.append(event_data)
            else:
                # Event has expired
                self._resolve_event_expiration(event_data)
        
        self.active_events = active_events
    
    def _check_random_events(self, current_turn: int, faction_stations: List[Station]) -> List[Dict[str, Any]]:
        """Check for random events that might trigger"""
        triggered_events = []
        
        for event_id, event in self.events.items():
            # Skip if on cooldown
            if event_id in self.event_cooldowns:
                continue
            
            # Skip historical events that have already occurred
            if event.historical and event_id in self.triggered_historical_events:
                continue
            
            # Check requirements
            if not self._check_event_requirements(event, current_turn, faction_stations):
                continue
            
            # Calculate probability with modifiers
            base_probability = event.probability
            category_modifier = self.category_modifiers.get(event.category, 1.0)
            final_probability = base_probability * category_modifier
            
            # Roll for event
            if random.random() < final_probability:
                event_data = self._trigger_event(event, current_turn, faction_stations)
                triggered_events.append(event_data)
                
                # Set cooldown
                if event.cooldown > 0:
                    self.event_cooldowns[event_id] = event.cooldown
                
                # Mark historical events
                if event.historical:
                    self.triggered_historical_events.add(event_id)
        
        return triggered_events
    
    def _check_scripted_events(self, current_turn: int, faction_stations: List[Station]) -> List[Dict[str, Any]]:
        """Check for scripted events that should trigger on specific conditions"""
        # This would contain events that trigger on specific game states
        # For now, we'll keep it simple and return empty list
        return []
    
    def _check_event_requirements(self, event: GameEvent, current_turn: int, faction_stations: List[Station]) -> bool:
        """Check if event requirements are met"""
        requirements = event.requirements
        
        # Check turn requirements
        if "turn" in requirements:
            turn_req = requirements["turn"]
            if "min" in turn_req and current_turn < turn_req["min"]:
                return False
            if "max" in turn_req and current_turn > turn_req["max"]:
                return False
        
        # Check station-specific requirements
        if event.scope == EventScope.STATION and faction_stations:
            # Find stations that meet requirements
            valid_stations = []
            for station in faction_stations:
                if self._station_meets_requirements(station, requirements):
                    valid_stations.append(station)
            
            if not valid_stations:
                return False
        
        # Check faction requirements
        if "allied_factions" in requirements:
            # This would need to be implemented with diplomacy system
            pass
        
        if "military_units" in requirements:
            # This would need to be implemented with military system
            pass
        
        return True
    
    def _station_meets_requirements(self, station: Station, requirements: Dict[str, Any]) -> bool:
        """Check if a station meets specific requirements"""
        # Check morale requirements
        if "station_morale" in requirements:
            morale_req = requirements["station_morale"]
            if "min" in morale_req and station.morale < morale_req["min"]:
                return False
            if "max" in morale_req and station.morale > morale_req["max"]:
                return False
        
        # Check population requirements
        if "population" in requirements:
            pop_req = requirements["population"]
            if "min" in pop_req and station.population < pop_req["min"]:
                return False
            if "max" in pop_req and station.population > pop_req["max"]:
                return False
        
        # Check infrastructure requirements
        if "library" in requirements and requirements["library"]:
            if BuildingType.LIBRARY not in station.infrastructure:
                return False
        
        return True
    
    def _trigger_event(self, event: GameEvent, current_turn: int, faction_stations: List[Station]) -> Dict[str, Any]:
        """Trigger an event and create event data"""
        # Select target based on event scope
        target = self._select_event_target(event, faction_stations)
        
        # Create event data
        event_data = {
            "event_id": event.event_id,
            "title": event.title,
            "description": event.description,
            "category": event.category.value,
            "severity": event.severity.value,
            "scope": event.scope.value,
            "turn_triggered": current_turn,
            "duration": event.duration,
            "remaining_duration": event.duration,
            "target": target,
            "choices": [self._choice_to_dict(choice) for choice in event.choices],
            "flavor_text": random.choice(event.flavor_text) if event.flavor_text else "",
            "resolved": False
        }
        
        # Apply immediate effects
        self._apply_event_effects(event.immediate_effects, event_data, faction_stations)
        
        # Add to active events if it has duration > 1
        if event.duration > 1:
            self.active_events.append(event_data)
        
        # Add to history
        self.event_history.append(event_data.copy())
        
        return event_data
    
    def _select_event_target(self, event: GameEvent, faction_stations: List[Station]) -> Optional[str]:
        """Select a target for the event based on its scope"""
        if event.scope == EventScope.STATION and faction_stations:
            # Select a random station that meets requirements
            valid_stations = [
                station for station in faction_stations
                if self._station_meets_requirements(station, event.requirements)
            ]
            if valid_stations:
                return random.choice(valid_stations).name
        
        elif event.scope == EventScope.TUNNEL:
            # Select a random tunnel
            if self.metro_map.tunnels:
                tunnel = random.choice(self.metro_map.tunnels)
                return f"{tunnel.station_a}-{tunnel.station_b}"
        
        return None
    
    def _choice_to_dict(self, choice: EventChoice) -> Dict[str, Any]:
        """Convert EventChoice to dictionary"""
        return {
            "choice_id": choice.choice_id,
            "description": choice.description,
            "requirements": choice.requirements,
            "costs": choice.costs,
            "effects": choice.effects,
            "probability_modifier": choice.probability_modifier
        }
    
    def _apply_event_effects(self, effects: Dict[str, Any], event_data: Dict[str, Any], faction_stations: List[Station]):
        """Apply event effects to the game world"""
        target_name = event_data.get("target")
        
        # Find target station if applicable
        target_station = None
        if target_name and event_data["scope"] == "station":
            target_station = next((s for s in faction_stations if s.name == target_name), None)
        
        # Apply effects based on type
        for effect_type, effect_value in effects.items():
            if effect_type == "block_tunnel" and target_name:
                self._block_tunnel(target_name)
            
            elif effect_type == "casualties" and target_station:
                casualties = random.randint(effect_value["min"], effect_value["max"])
                target_station.population = max(10, target_station.population - casualties)
                event_data["casualties"] = casualties
            
            elif effect_type == "morale_penalty" and target_station:
                target_station.morale = max(0, target_station.morale + effect_value)
            
            elif effect_type == "morale_bonus" and target_station:
                target_station.morale = min(100, target_station.morale + effect_value)
            
            elif effect_type == "tunnel_state" and target_name:
                self._set_tunnel_state(target_name, effect_value)
            
            elif effect_type == "resource_bonus":
                event_data["resource_rewards"] = self._calculate_resource_bonus(effect_value)
    
    def _block_tunnel(self, tunnel_name: str):
        """Block a tunnel due to event effects"""
        parts = tunnel_name.split("-")
        if len(parts) == 2:
            station_a, station_b = parts
            for tunnel in self.metro_map.tunnels:
                if (tunnel.station_a == station_a and tunnel.station_b == station_b) or \
                   (tunnel.station_a == station_b and tunnel.station_b == station_a):
                    tunnel.state = TunnelState.COLLAPSED
                    break
    
    def _set_tunnel_state(self, tunnel_name: str, new_state: TunnelState):
        """Set tunnel state due to event effects"""
        parts = tunnel_name.split("-")
        if len(parts) == 2:
            station_a, station_b = parts
            for tunnel in self.metro_map.tunnels:
                if (tunnel.station_a == station_a and tunnel.station_b == station_b) or \
                   (tunnel.station_a == station_b and tunnel.station_b == station_a):
                    tunnel.state = new_state
                    break
    
    def _calculate_resource_bonus(self, bonus_data: Dict[str, Dict[str, int]]) -> Dict[str, int]:
        """Calculate random resource bonuses"""
        rewards = {}
        for resource, range_data in bonus_data.items():
            amount = random.randint(range_data["min"], range_data["max"])
            rewards[resource] = amount
        return rewards
    
    def _resolve_event_expiration(self, event_data: Dict[str, Any]):
        """Handle event expiration"""
        self.logger.info(f"Event expired: {event_data['title']}")
        
        # Apply any expiration effects
        event = self.events.get(event_data["event_id"])
        if event and event.ongoing_effects:
            # Remove ongoing effects
            pass
    
    def resolve_event_choice(self, event_id: str, choice_id: str, faction_resources, faction_stations: List[Station]) -> Dict[str, Any]:
        """
        Resolve a player's choice for an event
        
        Args:
            event_id: ID of the event
            choice_id: ID of the chosen option
            faction_resources: Player's resource pool
            faction_stations: Player's stations
            
        Returns:
            Result of the choice resolution
        """
        # Find the active event
        event_data = None
        for event in self.active_events + self.event_history:
            if event["event_id"] == event_id and not event.get("resolved", False):
                event_data = event
                break
        
        if not event_data:
            return {"success": False, "message": "Event not found or already resolved"}
        
        # Find the choice
        choice_data = None
        for choice in event_data["choices"]:
            if choice["choice_id"] == choice_id:
                choice_data = choice
                break
        
        if not choice_data:
            return {"success": False, "message": "Invalid choice"}
        
        # Check requirements
        if not self._check_choice_requirements(choice_data, faction_resources, faction_stations):
            return {"success": False, "message": "Choice requirements not met"}
        
        # Apply costs
        for resource, amount in choice_data["costs"].items():
            if hasattr(faction_resources, resource):
                if not faction_resources.subtract(resource, amount):
                    return {"success": False, "message": f"Insufficient {resource}"}
        
        # Apply choice effects
        result = self._apply_choice_effects(choice_data["effects"], event_data, faction_resources, faction_stations)
        
        # Mark event as resolved
        event_data["resolved"] = True
        event_data["chosen_option"] = choice_id
        
        return {"success": True, "message": "Choice resolved successfully", "effects": result}
    
    def _check_choice_requirements(self, choice_data: Dict[str, Any], faction_resources, faction_stations: List[Station]) -> bool:
        """Check if choice requirements are met"""
        requirements = choice_data.get("requirements", {})
        
        # Check resource requirements
        for resource, amount in requirements.items():
            if resource == "military_units":
                # This would need integration with military system
                continue
            elif resource == "allied_factions":
                # This would need integration with diplomacy system
                continue
            elif hasattr(faction_resources, resource):
                if getattr(faction_resources, resource) < amount:
                    return False
        
        return True
    
    def _apply_choice_effects(self, effects: Dict[str, Any], event_data: Dict[str, Any], faction_resources, faction_stations: List[Station]) -> Dict[str, Any]:
        """Apply the effects of a player's choice"""
        result = {}
        
        for effect_type, effect_value in effects.items():
            if effect_type == "clear_tunnel":
                tunnel_name = event_data.get("target")
                if tunnel_name:
                    self._clear_tunnel(tunnel_name)
                    result["tunnel_cleared"] = tunnel_name
            
            elif effect_type == "duration_reduction":
                event_data["remaining_duration"] = max(0, event_data["remaining_duration"] - effect_value)
                result["duration_reduced"] = effect_value
            
            elif effect_type == "full_resource_bonus" and "resource_rewards" in event_data:
                for resource, amount in event_data["resource_rewards"].items():
                    if hasattr(faction_resources, resource):
                        faction_resources.add(resource, amount)
                result["resources_gained"] = event_data["resource_rewards"]
            
            elif effect_type == "mgr_bonus":
                faction_resources.add("mgr_rounds", effect_value)
                result["mgr_gained"] = effect_value
        
        return result
    
    def _clear_tunnel(self, tunnel_name: str):
        """Clear a blocked tunnel"""
        parts = tunnel_name.split("-")
        if len(parts) == 2:
            station_a, station_b = parts
            for tunnel in self.metro_map.tunnels:
                if (tunnel.station_a == station_a and tunnel.station_b == station_b) or \
                   (tunnel.station_a == station_b and tunnel.station_b == station_a):
                    tunnel.state = TunnelState.CLEAR
                    break
    
    def get_active_events(self) -> List[Dict[str, Any]]:
        """Get all currently active events"""
        return [event.copy() for event in self.active_events]
    
    def get_event_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent event history"""
        return self.event_history[-limit:] if self.event_history else []
    
    def set_category_modifier(self, category: EventCategory, modifier: float):
        """Set probability modifier for an event category"""
        self.category_modifiers[category] = modifier
        self.logger.info(f"Set {category.value} event probability modifier to {modifier}")
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get statistics about events"""
        total_events = len(self.event_history)
        category_counts = {}
        severity_counts = {}
        
        for event in self.event_history:
            category = event["category"]
            severity = event["severity"]
            
            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_events": total_events,
            "active_events": len(self.active_events),
            "category_distribution": category_counts,
            "severity_distribution": severity_counts,
            "historical_events_triggered": len(self.triggered_historical_events)
        }