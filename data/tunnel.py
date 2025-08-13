"""
Tunnel System
Represents connections between Metro stations with dynamic states
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum


class TunnelState(Enum):
    """States that tunnels can be in"""
    CLEAR = "clear"
    HAZARDOUS = "hazardous"
    INFESTED = "infested"
    ANOMALOUS = "anomalous"
    COLLAPSED = "collapsed"


class Tunnel:
    """
    Represents a tunnel connection between two Metro stations
    
    Tunnels have dynamic states that affect movement, trade, and combat:
    - Clear: Normal passage
    - Hazardous: Radiation/contamination (requires filters)
    - Infested: Mutant nests (dangerous for caravans)
    - Anomalous: Supernatural phenomena (impassable to most)
    - Collapsed: Completely blocked
    """
    
    def __init__(
        self,
        station_a: str,
        station_b: str,
        state: TunnelState = TunnelState.CLEAR,
        hazard_level: int = 0,
        metro_line: str = ""
    ):
        """
        Initialize tunnel connection
        
        Args:
            station_a: Name of first connected station
            station_b: Name of second connected station
            state: Current tunnel state
            hazard_level: Danger level (0-100)
            metro_line: Metro line this tunnel belongs to
        """
        self.logger = logging.getLogger(__name__)
        
        # Connection endpoints (order doesn't matter for bidirectional tunnels)
        self.station_a = station_a
        self.station_b = station_b
        self.metro_line = metro_line
        
        # Tunnel state and properties
        self.state = state
        self.hazard_level = max(0, min(100, hazard_level))
        
        # Dynamic properties
        self.blocked_turns_remaining = 0  # For temporary blockages
        self.last_cleared_turn = 0  # When tunnel was last cleared of threats
        
        # Travel costs for different unit types
        self._base_travel_costs = {
            "scout": 1,
            "military": 2,
            "caravan": 3,
            "civilian": 2
        }
        
        self.logger.info(f"Created tunnel {station_a} <-> {station_b} ({state.value})")
    
    def connects_stations(self, station1: str, station2: str) -> bool:
        """
        Check if this tunnel connects the specified stations
        
        Args:
            station1: First station name
            station2: Second station name
            
        Returns:
            True if tunnel connects these stations (in either direction)
        """
        return ((self.station_a == station1 and self.station_b == station2) or
                (self.station_a == station2 and self.station_b == station1))
    
    def get_other_station(self, station: str) -> Optional[str]:
        """
        Get the station on the other end of this tunnel
        
        Args:
            station: Known station name
            
        Returns:
            Name of the other connected station, or None if station not connected
        """
        if self.station_a == station:
            return self.station_b
        elif self.station_b == station:
            return self.station_a
        else:
            return None
    
    def is_passable(self, unit_type: str = "military") -> bool:
        """
        Check if tunnel is passable for the given unit type
        
        Args:
            unit_type: Type of unit attempting passage
            
        Returns:
            True if tunnel can be traversed
        """
        # Collapsed tunnels are impassable to all
        if self.state == TunnelState.COLLAPSED:
            return False
        
        # Anomalous tunnels are only passable by special units
        if self.state == TunnelState.ANOMALOUS:
            return unit_type in ["scout", "stalker", "ranger"]
        
        # Infested tunnels are dangerous but passable
        if self.state == TunnelState.INFESTED:
            # Civilian units avoid infested tunnels
            return unit_type != "civilian"
        
        # All other states are passable
        return True
    
    def calculate_travel_cost(self, unit_type: str) -> int:
        """
        Calculate movement cost for traversing this tunnel
        
        Args:
            unit_type: Type of unit traveling
            
        Returns:
            Movement cost (higher = more expensive/dangerous)
        """
        if not self.is_passable(unit_type):
            return float('inf')  # Impassable
        
        base_cost = self._base_travel_costs.get(unit_type, 2)
        
        # State-based cost modifiers
        state_modifiers = {
            TunnelState.CLEAR: 1.0,
            TunnelState.HAZARDOUS: 1.5,
            TunnelState.INFESTED: 2.0,
            TunnelState.ANOMALOUS: 3.0,
            TunnelState.COLLAPSED: float('inf')
        }
        
        modifier = state_modifiers.get(self.state, 1.0)
        
        # Hazard level adds additional cost
        hazard_modifier = 1.0 + (self.hazard_level / 100.0)
        
        final_cost = int(base_cost * modifier * hazard_modifier)
        return max(1, final_cost)
    
    def get_resource_requirements(self, unit_type: str) -> Dict[str, int]:
        """
        Get resource requirements for traversing this tunnel
        
        Args:
            unit_type: Type of unit traveling
            
        Returns:
            Dictionary of required resources
        """
        requirements = {}
        
        # Hazardous tunnels require filters
        if self.state == TunnelState.HAZARDOUS:
            filter_cost = max(1, self.hazard_level // 20)
            requirements["filters"] = filter_cost
        
        # Infested tunnels may require ammunition for defense
        if self.state == TunnelState.INFESTED and unit_type == "caravan":
            requirements["ammo"] = 5  # For escort protection
        
        # Anomalous tunnels require special equipment
        if self.state == TunnelState.ANOMALOUS:
            requirements["special_equipment"] = 1
        
        return requirements
    
    def update_state(self, new_state: TunnelState, reason: str = ""):
        """
        Update tunnel state
        
        Args:
            new_state: New tunnel state
            reason: Reason for state change (for logging)
        """
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            
            log_msg = f"Tunnel {self.station_a} <-> {self.station_b} state: {old_state.value} -> {new_state.value}"
            if reason:
                log_msg += f" ({reason})"
            
            self.logger.info(log_msg)
            
            # Reset blocked turns if tunnel becomes clear
            if new_state == TunnelState.CLEAR:
                self.blocked_turns_remaining = 0
    
    def apply_temporary_blockage(self, turns: int, reason: str = ""):
        """
        Apply temporary blockage to tunnel
        
        Args:
            turns: Number of turns tunnel will be blocked
            reason: Reason for blockage
        """
        self.blocked_turns_remaining = turns
        
        if turns > 0:
            # Temporarily set to collapsed state
            old_state = self.state
            self.state = TunnelState.COLLAPSED
            
            log_msg = f"Tunnel {self.station_a} <-> {self.station_b} temporarily blocked for {turns} turns"
            if reason:
                log_msg += f" ({reason})"
            
            self.logger.info(log_msg)
    
    def process_turn(self, current_turn: int):
        """
        Process end-of-turn updates for this tunnel
        
        Args:
            current_turn: Current game turn number
        """
        # Handle temporary blockages
        if self.blocked_turns_remaining > 0:
            self.blocked_turns_remaining -= 1
            
            if self.blocked_turns_remaining == 0:
                # Restore to clear state when blockage ends
                self.update_state(TunnelState.CLEAR, "blockage cleared")
        
        # Natural state changes (rare)
        # Infested tunnels may clear over time if not reinforced
        if self.state == TunnelState.INFESTED:
            turns_since_cleared = current_turn - self.last_cleared_turn
            if turns_since_cleared > 10:  # 10 turns without activity
                # Small chance to naturally clear
                import random
                if random.random() < 0.1:  # 10% chance
                    self.update_state(TunnelState.CLEAR, "mutants moved on")
                    self.last_cleared_turn = current_turn
    
    def clear_threats(self, current_turn: int) -> bool:
        """
        Attempt to clear threats from tunnel (military action)
        
        Args:
            current_turn: Current game turn number
            
        Returns:
            True if clearing was successful
        """
        if self.state in [TunnelState.INFESTED, TunnelState.HAZARDOUS]:
            self.update_state(TunnelState.CLEAR, "threats cleared by military")
            self.last_cleared_turn = current_turn
            return True
        
        return False
    
    def get_danger_level(self) -> int:
        """
        Get overall danger level of tunnel (0-100)
        
        Returns:
            Danger level for risk assessment
        """
        base_danger = {
            TunnelState.CLEAR: 0,
            TunnelState.HAZARDOUS: 30,
            TunnelState.INFESTED: 60,
            TunnelState.ANOMALOUS: 80,
            TunnelState.COLLAPSED: 100
        }
        
        state_danger = base_danger.get(self.state, 0)
        return min(100, state_danger + self.hazard_level)
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get comprehensive tunnel information
        
        Returns:
            Dictionary containing all tunnel data
        """
        return {
            "stations": [self.station_a, self.station_b],
            "metro_line": self.metro_line,
            "state": self.state.value,
            "hazard_level": self.hazard_level,
            "danger_level": self.get_danger_level(),
            "blocked_turns": self.blocked_turns_remaining,
            "passable": {
                "military": self.is_passable("military"),
                "caravan": self.is_passable("caravan"),
                "civilian": self.is_passable("civilian")
            },
            "travel_costs": {
                unit_type: self.calculate_travel_cost(unit_type)
                for unit_type in ["scout", "military", "caravan", "civilian"]
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "station_a": self.station_a,
            "station_b": self.station_b,
            "metro_line": self.metro_line,
            "state": self.state.value,
            "hazard_level": self.hazard_level,
            "blocked_turns_remaining": self.blocked_turns_remaining,
            "last_cleared_turn": self.last_cleared_turn
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tunnel':
        """Create Tunnel from dictionary"""
        tunnel = cls(
            data["station_a"],
            data["station_b"],
            TunnelState(data["state"]),
            data["hazard_level"],
            data.get("metro_line", "")
        )
        tunnel.blocked_turns_remaining = data.get("blocked_turns_remaining", 0)
        tunnel.last_cleared_turn = data.get("last_cleared_turn", 0)
        return tunnel
    
    def __str__(self) -> str:
        """String representation"""
        return f"Tunnel({self.station_a} <-> {self.station_b}, {self.state.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"Tunnel(stations=['{self.station_a}', '{self.station_b}'], "
                f"state={self.state.value}, hazard={self.hazard_level})")