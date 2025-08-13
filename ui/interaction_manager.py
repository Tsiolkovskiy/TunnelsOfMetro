"""
Interaction Manager
Handles user interactions with the map and game elements
"""

import pygame
import logging
from typing import Optional, Dict, List, Any, Callable
from enum import Enum

from systems.metro_map import MetroMap
from data.station import Station


class InteractionMode(Enum):
    """Different interaction modes for the map"""
    NORMAL = "normal"
    PATHFINDING = "pathfinding"
    RANGE_DISPLAY = "range_display"
    ACTION_TARGET = "action_target"


class InteractionManager:
    """
    Manages all user interactions with the game interface
    
    Features:
    - Station selection and information display
    - Action targeting and confirmation
    - Pathfinding visualization
    - Context-sensitive interactions
    """
    
    def __init__(self, metro_map: MetroMap):
        """
        Initialize interaction manager
        
        Args:
            metro_map: MetroMap instance to interact with
        """
        self.metro_map = metro_map
        self.logger = logging.getLogger(__name__)
        
        # Interaction state
        self.mode = InteractionMode.NORMAL
        self.selected_station: Optional[str] = None
        self.target_station: Optional[str] = None
        self.hovered_station: Optional[str] = None
        
        # Action state
        self.pending_action: Optional[str] = None
        self.action_origin: Optional[str] = None
        
        # Visual feedback
        self.highlighted_stations: List[str] = []
        self.highlighted_paths: List[List[str]] = []
        self.reachable_stations: Dict[str, int] = {}
        
        # Callbacks for game events
        self.on_station_selected: Optional[Callable[[str], None]] = None
        self.on_action_confirmed: Optional[Callable[[str, str, str], None]] = None
        self.on_info_requested: Optional[Callable[[str], Dict[str, Any]]] = None
        
        self.logger.info("Interaction manager initialized")
    
    def handle_mouse_click(self, pos: tuple, button: int, map_view) -> bool:
        """
        Handle mouse click events
        
        Args:
            pos: Mouse position (x, y)
            button: Mouse button pressed
            map_view: MapView instance for position queries
            
        Returns:
            True if click was handled
        """
        clicked_station = map_view.renderer.get_station_at_position(self.metro_map, pos)
        
        if button == 1:  # Left click
            return self._handle_left_click(clicked_station, map_view)
        elif button == 3:  # Right click
            return self._handle_right_click(clicked_station, pos)
        
        return False
    
    def _handle_left_click(self, station_name: Optional[str], map_view) -> bool:
        """Handle left mouse click"""
        if self.mode == InteractionMode.NORMAL:
            if station_name:
                self.select_station(station_name, map_view)
                return True
            else:
                self.deselect_station(map_view)
                return True
                
        elif self.mode == InteractionMode.ACTION_TARGET:
            if station_name and self.pending_action and self.action_origin:
                self.confirm_action(station_name)
                return True
            else:
                self.cancel_action(map_view)
                return True
                
        elif self.mode == InteractionMode.PATHFINDING:
            if station_name and self.selected_station:
                self.show_path_to_station(station_name, map_view)
                return True
        
        return False
    
    def _handle_right_click(self, station_name: Optional[str], pos: tuple) -> bool:
        """Handle right mouse click"""
        if station_name:
            # Right click on station - show context menu or quick info
            self.show_station_context_menu(station_name, pos)
            return True
        else:
            # Right click on empty space - cancel current action
            if self.mode != InteractionMode.NORMAL:
                self.set_mode(InteractionMode.NORMAL)
                return True
        
        return False
    
    def handle_mouse_motion(self, pos: tuple, map_view):
        """
        Handle mouse movement
        
        Args:
            pos: Mouse position (x, y)
            map_view: MapView instance for position queries
        """
        old_hovered = self.hovered_station
        self.hovered_station = map_view.renderer.get_station_at_position(self.metro_map, pos)
        
        # Update hover effects
        if old_hovered != self.hovered_station:
            self._update_hover_effects(map_view)
    
    def _update_hover_effects(self, map_view):
        """Update visual effects based on hover state"""
        if self.mode == InteractionMode.ACTION_TARGET and self.hovered_station:
            # Show preview of action target
            if self.pending_action == "attack":
                # Highlight path to target for attack
                if self.action_origin and self.hovered_station != self.action_origin:
                    path = self.metro_map.find_path(self.action_origin, self.hovered_station, "military")
                    if path:
                        map_view.show_path(path)
            
            elif self.pending_action == "trade":
                # Show trade route
                if self.action_origin and self.hovered_station != self.action_origin:
                    path = self.metro_map.find_path(self.action_origin, self.hovered_station, "caravan")
                    if path:
                        map_view.show_path(path)
    
    def select_station(self, station_name: str, map_view):
        """
        Select a station and update visual feedback
        
        Args:
            station_name: Name of station to select
            map_view: MapView instance to update
        """
        self.selected_station = station_name
        map_view.select_station(station_name)
        
        # Show adjacent stations
        adjacent = self.metro_map.get_adjacent_stations(station_name)
        self.highlighted_stations = adjacent
        map_view.renderer.set_highlighted_stations(adjacent)
        
        # Trigger callback
        if self.on_station_selected:
            self.on_station_selected(station_name)
        
        self.logger.info(f"Selected station: {station_name}")
    
    def deselect_station(self, map_view):
        """Deselect current station"""
        self.selected_station = None
        map_view.select_station(None)
        
        # Clear highlights
        self.highlighted_stations.clear()
        self.highlighted_paths.clear()
        map_view.clear_highlights()
        
        self.logger.debug("Deselected station")
    
    def initiate_action(self, action: str, origin_station: str, map_view):
        """
        Initiate an action that requires target selection
        
        Args:
            action: Action name (attack, trade, etc.)
            origin_station: Station where action originates
            map_view: MapView instance to update
        """
        self.pending_action = action
        self.action_origin = origin_station
        self.set_mode(InteractionMode.ACTION_TARGET)
        
        # Show valid targets based on action type
        valid_targets = self._get_valid_targets(action, origin_station)
        map_view.renderer.set_highlighted_stations(valid_targets)
        
        self.logger.info(f"Initiated action '{action}' from {origin_station}")
    
    def _get_valid_targets(self, action: str, origin: str) -> List[str]:
        """Get list of valid target stations for an action"""
        valid_targets = []
        origin_station = self.metro_map.get_station(origin)
        
        if not origin_station:
            return valid_targets
        
        for station_name, station in self.metro_map.stations.items():
            if station_name == origin:
                continue
            
            # Check if target is valid based on action type
            if action == "attack":
                # Can attack hostile stations within range
                if self._is_hostile_faction(origin_station.controlling_faction, station.controlling_faction):
                    path = self.metro_map.find_path(origin, station_name, "military")
                    if path and len(path) <= 5:  # Within 5 stations
                        valid_targets.append(station_name)
            
            elif action == "trade":
                # Can trade with neutral or friendly stations
                if not self._is_hostile_faction(origin_station.controlling_faction, station.controlling_faction):
                    path = self.metro_map.find_path(origin, station_name, "caravan")
                    if path:
                        valid_targets.append(station_name)
            
            elif action == "diplomacy":
                # Can conduct diplomacy with any foreign station
                if station.controlling_faction != origin_station.controlling_faction:
                    valid_targets.append(station_name)
            
            elif action == "scout":
                # Can scout adjacent stations
                adjacent = self.metro_map.get_adjacent_stations(origin)
                if station_name in adjacent:
                    valid_targets.append(station_name)
        
        return valid_targets
    
    def _is_hostile_faction(self, faction_a: str, faction_b: str) -> bool:
        """Check if two factions are hostile"""
        # Simplified hostility check - in full game this would use relationship matrix
        hostile_pairs = [
            ("Rangers", "Fourth Reich"),
            ("Rangers", "Red Line"),
            ("Fourth Reich", "Red Line"),
            ("Polis", "Invisible Watchers")
        ]
        
        return ((faction_a, faction_b) in hostile_pairs or 
                (faction_b, faction_a) in hostile_pairs)
    
    def confirm_action(self, target_station: str):
        """
        Confirm and execute the pending action
        
        Args:
            target_station: Target station for the action
        """
        if not self.pending_action or not self.action_origin:
            return
        
        # Trigger callback
        if self.on_action_confirmed:
            self.on_action_confirmed(self.pending_action, self.action_origin, target_station)
        
        self.logger.info(f"Confirmed action '{self.pending_action}': {self.action_origin} -> {target_station}")
        
        # Reset action state
        self.cancel_action(None)
    
    def cancel_action(self, map_view):
        """Cancel the pending action"""
        if self.pending_action:
            self.logger.debug(f"Cancelled action '{self.pending_action}'")
        
        self.pending_action = None
        self.action_origin = None
        self.set_mode(InteractionMode.NORMAL)
        
        if map_view:
            map_view.clear_highlights()
    
    def show_path_to_station(self, target_station: str, map_view):
        """
        Show path from selected station to target
        
        Args:
            target_station: Destination station
            map_view: MapView instance to update
        """
        if not self.selected_station:
            return
        
        path = self.metro_map.find_path(self.selected_station, target_station, "military")
        if path:
            map_view.show_path(path)
            self.highlighted_paths = [path]
            
            # Calculate path cost
            total_cost = 0
            for i in range(len(path) - 1):
                tunnel = self.metro_map.get_tunnel(path[i], path[i + 1])
                if tunnel:
                    total_cost += tunnel.calculate_travel_cost("military")
            
            self.logger.info(f"Path to {target_station}: {' -> '.join(path)} (cost: {total_cost})")
    
    def show_reachable_area(self, origin: str, max_cost: int, unit_type: str, map_view):
        """
        Show all stations reachable within cost limit
        
        Args:
            origin: Starting station
            max_cost: Maximum movement cost
            unit_type: Type of unit for movement calculation
            map_view: MapView instance to update
        """
        self.reachable_stations = self.metro_map.find_all_paths_within_range(origin, max_cost, unit_type)
        reachable_list = list(self.reachable_stations.keys())
        
        map_view.renderer.set_highlighted_stations(reachable_list)
        self.set_mode(InteractionMode.RANGE_DISPLAY)
        
        self.logger.info(f"Showing {len(reachable_list)} stations reachable from {origin}")
    
    def show_station_context_menu(self, station_name: str, pos: tuple):
        """
        Show context menu for a station
        
        Args:
            station_name: Station to show menu for
            pos: Mouse position for menu placement
        """
        # For now, just log the context menu request
        # In a full implementation, this would show a popup menu
        station = self.metro_map.get_station(station_name)
        if station:
            self.logger.info(f"Context menu for {station_name} ({station.controlling_faction})")
    
    def set_mode(self, mode: InteractionMode):
        """
        Set interaction mode
        
        Args:
            mode: New interaction mode
        """
        old_mode = self.mode
        self.mode = mode
        
        if old_mode != mode:
            self.logger.debug(f"Interaction mode: {old_mode.value} -> {mode.value}")
    
    def handle_keyboard_shortcut(self, key: int, map_view) -> bool:
        """
        Handle keyboard shortcuts for interactions
        
        Args:
            key: Pygame key constant
            map_view: MapView instance
            
        Returns:
            True if shortcut was handled
        """
        if not self.selected_station:
            return False
        
        # Handle mode-specific shortcuts
        if self.mode == InteractionMode.NORMAL:
            if key == pygame.K_p:  # 'P' for pathfinding mode
                self.set_mode(InteractionMode.PATHFINDING)
                return True
            elif key == pygame.K_r and pygame.key.get_pressed()[pygame.K_LSHIFT]:  # Shift+R for range
                self.show_reachable_area(self.selected_station, 10, "military", map_view)
                return True
        
        elif self.mode == InteractionMode.PATHFINDING:
            if key == pygame.K_ESCAPE:
                self.set_mode(InteractionMode.NORMAL)
                map_view.clear_highlights()
                return True
        
        elif self.mode == InteractionMode.ACTION_TARGET:
            if key == pygame.K_ESCAPE:
                self.cancel_action(map_view)
                return True
        
        elif self.mode == InteractionMode.RANGE_DISPLAY:
            if key == pygame.K_ESCAPE:
                self.set_mode(InteractionMode.NORMAL)
                map_view.clear_highlights()
                return True
        
        return False
    
    def get_interaction_status(self) -> Dict[str, Any]:
        """
        Get current interaction status for UI display
        
        Returns:
            Dictionary containing interaction state information
        """
        return {
            "mode": self.mode.value,
            "selected_station": self.selected_station,
            "hovered_station": self.hovered_station,
            "pending_action": self.pending_action,
            "action_origin": self.action_origin,
            "highlighted_count": len(self.highlighted_stations),
            "reachable_count": len(self.reachable_stations)
        }
    
    def get_station_actions(self, station_name: str, player_faction: str) -> List[Dict[str, Any]]:
        """
        Get available actions for a station
        
        Args:
            station_name: Station to get actions for
            player_faction: Player's faction name
            
        Returns:
            List of action dictionaries with name, description, and requirements
        """
        station = self.metro_map.get_station(station_name)
        if not station:
            return []
        
        actions = []
        
        # Universal actions
        actions.append({
            "name": "scout",
            "description": "Gather intelligence about this station",
            "cost": {"fuel": 10},
            "available": True
        })
        
        if station.controlling_faction == player_faction:
            # Own station actions
            actions.extend([
                {
                    "name": "develop",
                    "description": "Build or upgrade infrastructure",
                    "cost": {"scrap": 20},
                    "available": True
                },
                {
                    "name": "recruit",
                    "description": "Train military units",
                    "cost": {"food": 15, "scrap": 10},
                    "available": station.population >= 50
                },
                {
                    "name": "fortify",
                    "description": "Improve station defenses",
                    "cost": {"scrap": 30, "mgr_rounds": 5},
                    "available": True
                }
            ])
        else:
            # Foreign station actions
            is_hostile = self._is_hostile_faction(player_faction, station.controlling_faction)
            
            if not is_hostile:
                actions.append({
                    "name": "trade",
                    "description": "Exchange resources",
                    "cost": {"mgr_rounds": 2},
                    "available": True
                })
            
            actions.extend([
                {
                    "name": "diplomacy",
                    "description": "Conduct diplomatic negotiations",
                    "cost": {"mgr_rounds": 5},
                    "available": True
                },
                {
                    "name": "attack",
                    "description": "Launch military assault",
                    "cost": {"mgr_rounds": 50},
                    "available": is_hostile,
                    "preview_available": True
                }
            ])
        
        return actions