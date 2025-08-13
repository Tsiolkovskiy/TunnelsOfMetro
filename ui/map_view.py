"""
Map View Component
Manages the interactive map display and user interactions
"""

import pygame
import logging
from typing import Optional, Tuple, List, Dict, Any

from ui.map_renderer import MapRenderer
from ui.interaction_manager import InteractionManager, InteractionMode
from ui.station_actions import StationActionInterface
from systems.metro_map import MetroMap
from core.config import Config


class MapView:
    """
    Interactive map view component
    
    Handles:
    - Map rendering and display
    - Mouse interaction and station selection
    - Visual feedback for user actions
    - Map viewport management
    """
    
    def __init__(self, config: Config, metro_map: MetroMap):
        """
        Initialize map view
        
        Args:
            config: Game configuration
            metro_map: MetroMap instance to display
        """
        self.config = config
        self.metro_map = metro_map
        self.logger = logging.getLogger(__name__)
        
        # Initialize renderer, interaction manager, and action interface
        self.renderer = MapRenderer(config)
        self.interaction_manager = InteractionManager(metro_map)
        self.action_interface = StationActionInterface(config)
        
        # View state
        self.viewport_offset = (0, 0)
        self.zoom_level = 1.0
        self.show_legend = True
        
        # Interaction state (delegated to interaction manager)
        self.mouse_position = (0, 0)
        
        # Visual effects
        self.highlighted_paths: List[List[str]] = []
        self.highlighted_stations: List[str] = []
        
        # Set up interaction callbacks
        self.interaction_manager.on_station_selected = self._on_station_selected
        self.interaction_manager.on_action_confirmed = self._on_action_confirmed
        
        # Action interface callback will be set by game engine
        
        self.logger.info("Map view initialized")
    
    def handle_mouse_motion(self, pos: Tuple[int, int]):
        """
        Handle mouse movement over the map
        
        Args:
            pos: Mouse position (x, y)
        """
        self.mouse_position = pos
        self.interaction_manager.handle_mouse_motion(pos, self)
        self.action_interface.handle_mouse_motion(pos)
    
    def handle_mouse_click(self, pos: Tuple[int, int], button: int) -> Optional[str]:
        """
        Handle mouse click on the map
        
        Args:
            pos: Click position (x, y)
            button: Mouse button (1=left, 2=middle, 3=right)
            
        Returns:
            Name of clicked station, or None if no station was clicked
        """
        # First check if action interface handles the click
        action_result = self.action_interface.handle_mouse_click(pos, button)
        if action_result:
            return None  # Action interface handled it
        
        # Then check interaction manager
        handled = self.interaction_manager.handle_mouse_click(pos, button, self)
        
        if handled and self.interaction_manager.selected_station:
            return self.interaction_manager.selected_station
        
        return None
    
    def select_station(self, station_name: Optional[str]):
        """
        Select a station and update visual indicators
        
        Args:
            station_name: Name of station to select, or None to deselect
        """
        self.renderer.set_selected_station(station_name)
        
        # Update highlighted stations based on selection
        if station_name:
            self._update_selection_highlights(station_name)
        else:
            self.highlighted_stations.clear()
            self.renderer.set_highlighted_stations([])
    
    def _update_selection_highlights(self, station_name: str):
        """Update station highlights based on current selection"""
        # Highlight adjacent stations
        adjacent_stations = self.metro_map.get_adjacent_stations(station_name)
        self.highlighted_stations = adjacent_stations
        self.renderer.set_highlighted_stations(adjacent_stations)
    
    def _on_station_selected(self, station_name: str):
        """Callback for when a station is selected"""
        self.logger.info(f"Station selected via interaction manager: {station_name}")
    
    def _on_action_confirmed(self, action: str, origin: str, target: str):
        """Callback for when an action is confirmed"""
        self.logger.info(f"Action confirmed: {action} from {origin} to {target}")
        # This would trigger the actual game action in the full implementation
    
    def _on_action_interface_selected(self, action: str, station: str):
        """Callback for when an action is selected from the interface"""
        self.logger.info(f"Action selected from interface: {action} on {station}")
        # This would trigger the actual game action
    
    def _show_action_interface_for_selected(self):
        """Show action interface for the currently selected station"""
        selected_station = self.interaction_manager.selected_station
        if not selected_station:
            return
        
        station_info = self.get_selected_station_info()
        actions = self.get_available_actions("Rangers")  # Assuming Rangers is player
        
        if station_info and actions:
            # Position interface near the station
            station = self.metro_map.get_station(selected_station)
            if station:
                self.action_interface.show_for_station(
                    selected_station,
                    station_info,
                    actions,
                    station.position
                )
    
    def show_path(self, path: List[str]):
        """
        Highlight a path on the map
        
        Args:
            path: List of station names forming the path
        """
        if path:
            self.highlighted_paths = [path]
            self.highlighted_stations = path
            self.renderer.set_highlighted_stations(path)
            self.logger.debug(f"Showing path: {' -> '.join(path)}")
    
    def show_reachable_stations(self, origin: str, max_cost: int, unit_type: str = "military"):
        """
        Highlight all stations reachable from origin within cost limit
        
        Args:
            origin: Starting station name
            max_cost: Maximum movement cost
            unit_type: Type of unit for movement calculation
        """
        reachable = self.metro_map.find_all_paths_within_range(origin, max_cost, unit_type)
        reachable_stations = list(reachable.keys())
        
        self.highlighted_stations = reachable_stations
        self.renderer.set_highlighted_stations(reachable_stations)
        
        self.logger.debug(f"Showing {len(reachable_stations)} reachable stations from {origin}")
    
    def clear_highlights(self):
        """Clear all path and station highlights"""
        self.highlighted_paths.clear()
        self.highlighted_stations.clear()
        self.renderer.set_highlighted_stations([])
    
    def render(self, surface: pygame.Surface):
        """
        Render the map view
        
        Args:
            surface: Pygame surface to render on
        """
        # Get visible stations for fog of war
        visible_stations = None
        if hasattr(self, 'game_state') and self.game_state:
            visible_stations = self.game_state.get_visible_stations()
        
        # Render the main map
        self.renderer.render_map(surface, self.metro_map, visible_stations)
        
        # Render trade elements if game state is available
        if hasattr(self, 'game_state') and self.game_state:
            caravans = self.game_state.get_active_caravans()
            trade_routes = self.game_state.get_trade_routes()
            self.renderer.render_trade_elements(surface, self.metro_map, caravans, trade_routes)
            
            # Render combat effects
            battle_history = self.game_state.get_battle_history(3)
            recent_battle_sites = [battle["defender"] for battle in battle_history 
                                 if self.game_state.current_turn - battle["turn"] <= 2]
            
            # Get hostile stations (simplified - stations that can be attacked)
            hostile_stations = []
            if self.interaction_manager.selected_station:
                for station_name in self.metro_map.stations:
                    can_attack, _ = self.game_state.can_attack_station(station_name)
                    if can_attack:
                        hostile_stations.append(station_name)
            
            self.renderer.render_combat_effects(surface, self.metro_map, recent_battle_sites, hostile_stations)
        
        # Render legend if enabled
        if self.show_legend:
            self.renderer.render_legend(surface, 10, 10)
        
        # Render station info tooltip if hovering
        if self.interaction_manager.hovered_station:
            self._render_station_tooltip(surface)
        
        # Render interaction mode indicator
        self._render_interaction_mode_indicator(surface)
        
        # Render action interface
        station_info = self.get_selected_station_info()
        self.action_interface.render(surface, station_info)
        
        # Render quick action hints if station is selected but interface is not shown
        if (self.interaction_manager.selected_station and 
            not self.action_interface.is_visible()):
            actions = self.get_available_actions("Rangers")  # Assuming Rangers is player
            self.action_interface.render_quick_actions(
                surface, 
                self.interaction_manager.selected_station, 
                actions
            )
    
    def _render_station_tooltip(self, surface: pygame.Surface):
        """Render tooltip for hovered station"""
        hovered_station = self.interaction_manager.hovered_station
        if not hovered_station or hovered_station not in self.metro_map.stations:
            return
        
        station = self.metro_map.stations[hovered_station]
        
        # Create tooltip text
        tooltip_lines = [
            f"{station.name}",
            f"Faction: {station.controlling_faction}",
            f"Population: {station.population}",
            f"Morale: {station.morale}%"
        ]
        
        # Add resource info if station is controlled by player or allied
        if station.controlling_faction in ["Rangers", "Polis"]:  # Assuming Rangers is player
            production = station.get_resource_production()
            tooltip_lines.append("Production:")
            for resource, amount in production.items():
                if amount > 0:
                    tooltip_lines.append(f"  {resource}: +{amount}")
        
        # Render tooltip background
        font = pygame.font.SysFont('Arial', 14)
        line_height = 18
        tooltip_width = max(font.size(line)[0] for line in tooltip_lines) + 20
        tooltip_height = len(tooltip_lines) * line_height + 10
        
        # Position tooltip near mouse but keep on screen
        tooltip_x = min(self.mouse_position[0] + 15, surface.get_width() - tooltip_width)
        tooltip_y = min(self.mouse_position[1] + 15, surface.get_height() - tooltip_height)
        
        # Draw tooltip background
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        pygame.draw.rect(surface, (0, 0, 0, 200), tooltip_rect)
        pygame.draw.rect(surface, (255, 255, 255), tooltip_rect, 2)
        
        # Draw tooltip text
        for i, line in enumerate(tooltip_lines):
            text_surface = font.render(line, True, (255, 255, 255))
            text_y = tooltip_y + 5 + i * line_height
            surface.blit(text_surface, (tooltip_x + 10, text_y))
    
    def get_selected_station_info(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about the selected station
        
        Returns:
            Station information dictionary or None if no selection
        """
        selected_station = self.interaction_manager.selected_station
        if not selected_station or selected_station not in self.metro_map.stations:
            return None
        
        station = self.metro_map.stations[selected_station]
        return station.get_info()
    
    def get_available_actions(self, player_faction: str) -> List[Dict[str, Any]]:
        """
        Get list of available actions for the selected station
        
        Args:
            player_faction: Name of the player's faction
            
        Returns:
            List of available action dictionaries
        """
        selected_station = self.interaction_manager.selected_station
        if not selected_station:
            return []
        
        return self.interaction_manager.get_station_actions(selected_station, player_faction)
    
    def toggle_legend(self):
        """Toggle legend visibility"""
        self.show_legend = not self.show_legend
        self.logger.debug(f"Legend visibility: {self.show_legend}")
    
    def center_on_station(self, station_name: str):
        """
        Center the view on a specific station
        
        Args:
            station_name: Name of station to center on
        """
        if station_name in self.metro_map.stations:
            station = self.metro_map.stations[station_name]
            # For now, just select the station
            # In a full implementation, this would adjust viewport_offset
            self.select_station(station_name)
            self.logger.debug(f"Centered on station: {station_name}")
    
    def get_map_statistics(self) -> Dict[str, Any]:
        """Get current map statistics for display"""
        return self.metro_map.get_map_statistics()
    
    def update(self, dt: float):
        """
        Update map view (for animations, etc.)
        
        Args:
            dt: Delta time since last update
        """
        # For now, no animations to update
        # Future: pulsing effects, moving units, etc.
        pass
    
    def handle_keyboard_input(self, key: int) -> Optional[str]:
        """
        Handle keyboard input for map shortcuts
        
        Args:
            key: Pygame key constant
            
        Returns:
            Action name if a shortcut was triggered
        """
        # First check action interface shortcuts
        action_result = self.action_interface.handle_keyboard_input(key)
        if action_result:
            return action_result
        
        # Then check interaction manager shortcuts
        if self.interaction_manager.handle_keyboard_shortcut(key, self):
            return None
        
        selected_station = self.interaction_manager.selected_station
        if not selected_station:
            return None
        
        # Show action interface on Enter or Right-click equivalent
        if key == pygame.K_RETURN or key == pygame.K_SPACE:
            self._show_action_interface_for_selected()
            return None
        
        # Map keyboard shortcuts to actions
        key_actions = {
            pygame.K_s: "scout",
            pygame.K_t: "trade",
            pygame.K_a: "attack",
            pygame.K_d: "diplomacy",
            pygame.K_f: "fortify",
            pygame.K_r: "recruit",
            pygame.K_b: "develop"  # 'b' for build
        }
        
        action = key_actions.get(key)
        if action:
            self.logger.debug(f"Keyboard shortcut triggered: {action}")
            # Initiate action through interaction manager
            self.interaction_manager.initiate_action(action, selected_station, self)
        
        return action
    
    def _render_interaction_mode_indicator(self, surface: pygame.Surface):
        """Render indicator for current interaction mode"""
        mode = self.interaction_manager.mode
        
        if mode == InteractionMode.NORMAL:
            return  # No indicator needed for normal mode
        
        # Create mode indicator text
        mode_text = {
            InteractionMode.PATHFINDING: "PATHFINDING MODE - Click station to show path",
            InteractionMode.RANGE_DISPLAY: "RANGE DISPLAY - ESC to exit",
            InteractionMode.ACTION_TARGET: f"SELECT TARGET - {self.interaction_manager.pending_action.upper()}"
        }.get(mode, f"MODE: {mode.value.upper()}")
        
        # Render mode indicator
        font = pygame.font.SysFont('Arial', 16, bold=True)
        text_surface = font.render(mode_text, True, (255, 255, 0))
        
        # Position at top center
        text_rect = text_surface.get_rect()
        text_x = (surface.get_width() - text_rect.width) // 2
        text_y = 10
        
        # Draw background
        bg_rect = pygame.Rect(text_x - 10, text_y - 5, text_rect.width + 20, text_rect.height + 10)
        pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect)
        pygame.draw.rect(surface, (255, 255, 0), bg_rect, 2)
        
        # Draw text
        surface.blit(text_surface, (text_x, text_y))
    
    def initiate_action(self, action: str, origin_station: str):
        """
        Initiate an action that requires target selection
        
        Args:
            action: Action name
            origin_station: Station where action originates
        """
        self.interaction_manager.initiate_action(action, origin_station, self)
    
    def get_interaction_status(self) -> Dict[str, Any]:
        """Get current interaction status"""
        return self.interaction_manager.get_interaction_status()
    
    @property
    def selected_station(self) -> Optional[str]:
        """Get currently selected station"""
        return self.interaction_manager.selected_station
    
    def set_game_state(self, game_state):
        """Set game state for fog of war and intelligence"""
        self.game_state = game_state