"""
Map Renderer
Handles visual representation of the Metro map using Pygame
"""

import pygame
import logging
import math
from typing import Dict, List, Tuple, Optional, Any

from systems.metro_map import MetroMap
from data.station import Station, StationStatus
from data.tunnel import Tunnel, TunnelState
from core.config import Config


class MapRenderer:
    """
    Renders the Metro map with stations, tunnels, and visual indicators
    
    Features:
    - Faction color-coding for stations
    - Tunnel state visualization
    - Station status indicators
    - Interactive elements highlighting
    """
    
    def __init__(self, config: Config):
        """
        Initialize the map renderer
        
        Args:
            config: Game configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize fonts
        pygame.font.init()
        self.font_small = pygame.font.SysFont('Arial', 12)
        self.font_medium = pygame.font.SysFont('Arial', 16)
        self.font_large = pygame.font.SysFont('Arial', 20)
        
        # Color definitions
        self.colors = self._setup_colors()
        
        # Rendering settings
        self.station_radius = config.get("STATION_RADIUS", 10)
        self.station_name_offset = config.get("STATION_NAME_OFFSET", 15)
        self.tunnel_width = config.get("TUNNEL_WIDTH", 2)
        
        # Selection and highlighting
        self.selected_station: Optional[str] = None
        self.highlighted_stations: List[str] = []
        
        self.logger.info("Map renderer initialized")
    
    def _setup_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Setup color palette for map rendering"""
        base_colors = self.config.COLORS
        
        return {
            # Base colors
            "BLACK": base_colors["BLACK"],
            "WHITE": base_colors["WHITE"],
            "GRAY": base_colors["GRAY"],
            "DARK_GRAY": base_colors["DARK_GRAY"],
            
            # Faction colors
            "RANGERS": (0, 200, 0),      # Bright green
            "POLIS": (0, 100, 255),      # Blue
            "FOURTH_REICH": (150, 0, 0), # Dark red
            "RED_LINE": (255, 0, 0),     # Bright red
            "HANZA": (255, 165, 0),      # Orange
            "INVISIBLE_WATCHERS": (128, 0, 128),  # Purple
            "INDEPENDENT": (128, 128, 128),       # Gray
            
            # Station status colors
            "OPERATIONAL": (255, 255, 255),  # White
            "DAMAGED": (255, 255, 0),        # Yellow
            "RUINED": (255, 100, 0),         # Orange
            "INFESTED": (200, 0, 200),       # Magenta
            "ANOMALOUS": (100, 0, 255),      # Purple
            
            # Tunnel state colors
            "TUNNEL_CLEAR": (100, 100, 100),      # Light gray
            "TUNNEL_HAZARDOUS": (255, 255, 0),    # Yellow
            "TUNNEL_INFESTED": (255, 0, 255),     # Magenta
            "TUNNEL_ANOMALOUS": (128, 0, 255),    # Purple
            "TUNNEL_COLLAPSED": (255, 0, 0),      # Red
            
            # UI colors
            "SELECTION": (255, 255, 255),    # White
            "HIGHLIGHT": (255, 255, 100),    # Light yellow
            "TEXT_SHADOW": (0, 0, 0),        # Black
        }
    
    def get_faction_color(self, faction: str) -> Tuple[int, int, int]:
        """
        Get color for a faction
        
        Args:
            faction: Faction name
            
        Returns:
            RGB color tuple
        """
        faction_key = faction.upper().replace(" ", "_")
        return self.colors.get(faction_key, self.colors["INDEPENDENT"])
    
    def get_station_status_color(self, status: StationStatus) -> Tuple[int, int, int]:
        """
        Get color for station status
        
        Args:
            status: Station status enum
            
        Returns:
            RGB color tuple
        """
        status_key = status.value.upper()
        return self.colors.get(status_key, self.colors["OPERATIONAL"])
    
    def get_tunnel_state_color(self, state: TunnelState) -> Tuple[int, int, int]:
        """
        Get color for tunnel state
        
        Args:
            state: Tunnel state enum
            
        Returns:
            RGB color tuple
        """
        state_key = f"TUNNEL_{state.value.upper()}"
        return self.colors.get(state_key, self.colors["TUNNEL_CLEAR"])
    
    def render_map(self, surface: pygame.Surface, metro_map: MetroMap, visible_stations: Optional[Set[str]] = None):
        """
        Render the complete Metro map
        
        Args:
            surface: Pygame surface to render on
            metro_map: MetroMap instance to render
            visible_stations: Set of stations visible to player (for fog of war)
        """
        # Clear background
        surface.fill(self.colors["BLACK"])
        
        # Render tunnels first (so they appear behind stations)
        self._render_tunnels(surface, metro_map, visible_stations)
        
        # Render stations
        self._render_stations(surface, metro_map, visible_stations)
        
        # Render selection and highlights
        self._render_selection_indicators(surface, metro_map)
        
        # Render station names
        self._render_station_names(surface, metro_map, visible_stations)
    
    def render_trade_elements(self, surface: pygame.Surface, metro_map: MetroMap, 
                            caravans: Dict[str, Any], trade_routes: Dict[str, Any]):
        """
        Render trade-related elements on the map
        
        Args:
            surface: Surface to render on
            metro_map: MetroMap instance
            caravans: Active caravans data
            trade_routes: Trade routes data
        """
        # Render trade routes (supply lines)
        self._render_trade_routes(surface, metro_map, trade_routes)
        
        # Render caravans
        self._render_caravans(surface, metro_map, caravans)
    
    def render_combat_effects(self, surface: pygame.Surface, metro_map: MetroMap, 
                            battle_sites: List[str], hostile_stations: List[str]):
        """
        Render combat-related visual effects
        
        Args:
            surface: Surface to render on
            metro_map: MetroMap instance
            battle_sites: Stations where battles recently occurred
            hostile_stations: Stations that can be attacked
        """
        # Render battle sites with pulsing red effect
        for station_name in battle_sites:
            station = metro_map.get_station(station_name)
            if station:
                self._render_battle_effect(surface, station.position)
        
        # Render hostile stations with red border
        for station_name in hostile_stations:
            station = metro_map.get_station(station_name)
            if station:
                self._render_hostile_indicator(surface, station.position)
    
    def _render_battle_effect(self, surface: pygame.Surface, position: Tuple[int, int]):
        """Render battle effect at position"""
        import time
        
        # Pulsing red circle
        pulse = abs(int((time.time() * 3) % 2 - 1))  # 0 to 1 and back
        alpha = 100 + pulse * 100
        radius = 15 + pulse * 5
        
        # Create surface for alpha blending
        effect_surface = pygame.Surface((radius * 2, radius * 2))
        effect_surface.set_alpha(alpha)
        effect_surface.fill((255, 0, 0))
        
        # Draw circle
        pygame.draw.circle(effect_surface, (255, 0, 0), (radius, radius), radius)
        
        # Blit to main surface
        surface.blit(effect_surface, (position[0] - radius, position[1] - radius))
    
    def _render_hostile_indicator(self, surface: pygame.Surface, position: Tuple[int, int]):
        """Render indicator for hostile stations"""
        # Red border around station
        pygame.draw.circle(surface, (255, 100, 100), position, self.station_radius + 2, 2)
    
    def _render_trade_routes(self, surface: pygame.Surface, metro_map: MetroMap, 
                           trade_routes: Dict[str, Any]):
        """Render trade routes as dashed lines"""
        for route_data in trade_routes.values():
            stations = route_data["stations"]
            status = route_data["status"]
            
            if len(stations) != 2:
                continue
            
            station_a = metro_map.get_station(stations[0])
            station_b = metro_map.get_station(stations[1])
            
            if not station_a or not station_b:
                continue
            
            # Color based on route status
            if status == "active":
                color = (0, 255, 0, 128)  # Green for active
            elif status == "disrupted":
                color = (255, 255, 0, 128)  # Yellow for disrupted
            else:
                color = (128, 128, 128, 128)  # Gray for inactive
            
            # Draw dashed line for trade route
            self._draw_dashed_line(surface, station_a.position, station_b.position, color, 3)
    
    def _render_caravans(self, surface: pygame.Surface, metro_map: MetroMap, 
                        caravans: Dict[str, Any]):
        """Render caravans on the map"""
        for caravan_data in caravans.values():
            current_pos = caravan_data["current_position"]
            status = caravan_data["status"]
            
            station = metro_map.get_station(current_pos)
            if not station:
                continue
            
            # Caravan icon color based on status
            if status == "traveling":
                color = (255, 255, 0)  # Yellow for traveling
            elif status == "trading":
                color = (0, 255, 255)  # Cyan for trading
            else:
                color = (128, 128, 128)  # Gray for other states
            
            # Draw caravan icon (small square)
            caravan_size = 6
            caravan_rect = pygame.Rect(
                station.position[0] - caravan_size // 2,
                station.position[1] - caravan_size // 2 - 15,  # Above station
                caravan_size,
                caravan_size
            )
            
            pygame.draw.rect(surface, color, caravan_rect)
            pygame.draw.rect(surface, (255, 255, 255), caravan_rect, 1)
            
            # Draw caravan ID
            font = pygame.font.SysFont('Arial', 8)
            id_text = caravan_data["id"].split("_")[-1]  # Just the number
            text_surface = font.render(id_text, True, (255, 255, 255))
            text_x = station.position[0] - text_surface.get_width() // 2
            text_y = station.position[1] - 25
            surface.blit(text_surface, (text_x, text_y))
    
    def _draw_dashed_line(self, surface: pygame.Surface, start: Tuple[int, int], 
                         end: Tuple[int, int], color: Tuple[int, int, int, int], width: int):
        """Draw a dashed line between two points"""
        import math
        
        # Calculate line parameters
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance == 0:
            return
        
        # Normalize direction
        dx /= distance
        dy /= distance
        
        # Draw dashes
        dash_length = 8
        gap_length = 4
        current_distance = 0
        
        while current_distance < distance:
            # Start of dash
            dash_start_x = start[0] + dx * current_distance
            dash_start_y = start[1] + dy * current_distance
            
            # End of dash
            dash_end_distance = min(current_distance + dash_length, distance)
            dash_end_x = start[0] + dx * dash_end_distance
            dash_end_y = start[1] + dy * dash_end_distance
            
            # Draw dash
            pygame.draw.line(surface, color[:3], 
                           (int(dash_start_x), int(dash_start_y)),
                           (int(dash_end_x), int(dash_end_y)), width)
            
            current_distance += dash_length + gap_length
    
    def _render_tunnels(self, surface: pygame.Surface, metro_map: MetroMap, visible_stations: Optional[Set[str]] = None):
        """Render all tunnel connections"""
        for tunnel in metro_map.tunnels:
            station_a = metro_map.get_station(tunnel.station_a)
            station_b = metro_map.get_station(tunnel.station_b)
            
            if not station_a or not station_b:
                continue
            
            # Apply fog of war
            if visible_stations is not None:
                if tunnel.station_a not in visible_stations and tunnel.station_b not in visible_stations:
                    continue  # Don't render tunnels between unknown stations
            
            # Get tunnel color based on state
            tunnel_color = self.get_tunnel_state_color(tunnel.state)
            
            # Adjust line width based on tunnel state
            line_width = self.tunnel_width
            if tunnel.state == TunnelState.COLLAPSED:
                line_width = max(1, self.tunnel_width // 2)  # Thinner for collapsed
            elif tunnel.state in [TunnelState.INFESTED, TunnelState.ANOMALOUS]:
                line_width = self.tunnel_width + 1  # Thicker for dangerous
            
            # Draw tunnel line
            pygame.draw.line(
                surface,
                tunnel_color,
                station_a.position,
                station_b.position,
                line_width
            )
            
            # Draw hazard indicators for dangerous tunnels
            if tunnel.state != TunnelState.CLEAR:
                self._draw_tunnel_hazard_indicator(surface, tunnel, station_a.position, station_b.position)
    
    def _draw_tunnel_hazard_indicator(
        self,
        surface: pygame.Surface,
        tunnel: Tunnel,
        pos_a: Tuple[int, int],
        pos_b: Tuple[int, int]
    ):
        """Draw hazard indicators on dangerous tunnels"""
        # Calculate midpoint
        mid_x = (pos_a[0] + pos_b[0]) // 2
        mid_y = (pos_a[1] + pos_b[1]) // 2
        
        # Draw different indicators based on tunnel state
        if tunnel.state == TunnelState.HAZARDOUS:
            # Radiation symbol (triangle with dots)
            points = [
                (mid_x, mid_y - 5),
                (mid_x - 4, mid_y + 3),
                (mid_x + 4, mid_y + 3)
            ]
            pygame.draw.polygon(surface, self.colors["TUNNEL_HAZARDOUS"], points)
            
        elif tunnel.state == TunnelState.INFESTED:
            # Mutant indicator (jagged circle)
            for i in range(8):
                angle = i * math.pi / 4
                x = mid_x + int(4 * math.cos(angle))
                y = mid_y + int(4 * math.sin(angle))
                pygame.draw.circle(surface, self.colors["TUNNEL_INFESTED"], (x, y), 2)
                
        elif tunnel.state == TunnelState.ANOMALOUS:
            # Anomaly indicator (pulsing circle)
            pygame.draw.circle(surface, self.colors["TUNNEL_ANOMALOUS"], (mid_x, mid_y), 6, 2)
            pygame.draw.circle(surface, self.colors["TUNNEL_ANOMALOUS"], (mid_x, mid_y), 3)
            
        elif tunnel.state == TunnelState.COLLAPSED:
            # Collapsed indicator (X mark)
            pygame.draw.line(surface, self.colors["TUNNEL_COLLAPSED"], 
                           (mid_x - 4, mid_y - 4), (mid_x + 4, mid_y + 4), 2)
            pygame.draw.line(surface, self.colors["TUNNEL_COLLAPSED"], 
                           (mid_x - 4, mid_y + 4), (mid_x + 4, mid_y - 4), 2)
    
    def _render_stations(self, surface: pygame.Surface, metro_map: MetroMap, visible_stations: Optional[Set[str]] = None):
        """Render all stations with faction colors and status indicators"""
        for station in metro_map.stations.values():
            # Apply fog of war
            if visible_stations is not None and station.name not in visible_stations:
                continue  # Don't render unknown stations
            
            # Get faction color
            faction_color = self.get_faction_color(station.controlling_faction)
            
            # Draw station circle
            pygame.draw.circle(
                surface,
                faction_color,
                station.position,
                self.station_radius
            )
            
            # Draw status indicator (inner circle)
            status_color = self.get_station_status_color(station.status)
            if station.status != StationStatus.OPERATIONAL:
                pygame.draw.circle(
                    surface,
                    status_color,
                    station.position,
                    self.station_radius - 3
                )
            
            # Draw population indicator (small dots around station)
            self._draw_population_indicator(surface, station)
            
            # Draw infrastructure indicators
            self._draw_infrastructure_indicators(surface, station)
    
    def _draw_population_indicator(self, surface: pygame.Surface, station: Station):
        """Draw population level indicator around station"""
        # Population levels: 0-50 (small), 51-150 (medium), 151+ (large)
        if station.population <= 50:
            dot_count = 2
        elif station.population <= 150:
            dot_count = 4
        else:
            dot_count = 6
        
        # Draw dots around station
        for i in range(dot_count):
            angle = (2 * math.pi * i) / dot_count
            x = station.position[0] + int((self.station_radius + 5) * math.cos(angle))
            y = station.position[1] + int((self.station_radius + 5) * math.sin(angle))
            
            # Color based on morale
            if station.morale >= 70:
                dot_color = (0, 255, 0)  # Green
            elif station.morale >= 40:
                dot_color = (255, 255, 0)  # Yellow
            else:
                dot_color = (255, 0, 0)  # Red
            
            pygame.draw.circle(surface, dot_color, (x, y), 2)
    
    def _draw_infrastructure_indicators(self, surface: pygame.Surface, station: Station):
        """Draw small indicators for station infrastructure"""
        if not station.infrastructure:
            return
        
        # Draw small squares for each building type
        building_count = len(station.infrastructure)
        start_x = station.position[0] - (building_count * 3)
        y = station.position[1] - self.station_radius - 8
        
        for i, (building_type, infrastructure) in enumerate(station.infrastructure.items()):
            x = start_x + (i * 6)
            
            # Color based on building type
            building_colors = {
                "mushroom_farm": (0, 150, 0),
                "water_filter": (0, 100, 255),
                "scrap_workshop": (150, 150, 150),
                "med_bay": (255, 100, 100),
                "barracks": (100, 100, 0),
                "fortifications": (100, 50, 0),
                "market": (255, 200, 0),
                "library": (150, 0, 150)
            }
            
            building_color = building_colors.get(building_type.value, self.colors["WHITE"])
            
            # Draw building indicator
            rect = pygame.Rect(x - 2, y - 2, 4, 4)
            pygame.draw.rect(surface, building_color, rect)
            
            # Add efficiency level indicator
            if infrastructure.efficiency_level > 1:
                for level in range(infrastructure.efficiency_level - 1):
                    pygame.draw.circle(surface, building_color, (x, y - 6 - level * 2), 1)
    
    def _render_selection_indicators(self, surface: pygame.Surface, metro_map: MetroMap):
        """Render selection and highlight indicators"""
        # Render selected station
        if self.selected_station and self.selected_station in metro_map.stations:
            station = metro_map.stations[self.selected_station]
            pygame.draw.circle(
                surface,
                self.colors["SELECTION"],
                station.position,
                self.station_radius + 3,
                3
            )
        
        # Render highlighted stations
        for station_name in self.highlighted_stations:
            if station_name in metro_map.stations:
                station = metro_map.stations[station_name]
                pygame.draw.circle(
                    surface,
                    self.colors["HIGHLIGHT"],
                    station.position,
                    self.station_radius + 2,
                    2
                )
    
    def _render_station_names(self, surface: pygame.Surface, metro_map: MetroMap, visible_stations: Optional[Set[str]] = None):
        """Render station names with text shadows"""
        for station in metro_map.stations.values():
            # Apply fog of war
            if visible_stations is not None and station.name not in visible_stations:
                continue  # Don't render names for unknown stations
            
            # Create text surface
            text_surface = self.font_small.render(station.name, True, self.colors["WHITE"])
            text_rect = text_surface.get_rect()
            
            # Position text below station
            text_x = station.position[0] - text_rect.width // 2
            text_y = station.position[1] + self.station_name_offset
            
            # Draw text shadow
            shadow_surface = self.font_small.render(station.name, True, self.colors["TEXT_SHADOW"])
            surface.blit(shadow_surface, (text_x + 1, text_y + 1))
            
            # Draw main text
            surface.blit(text_surface, (text_x, text_y))
    
    def set_selected_station(self, station_name: Optional[str]):
        """Set the currently selected station"""
        self.selected_station = station_name
        self.logger.debug(f"Selected station: {station_name}")
    
    def set_highlighted_stations(self, station_names: List[str]):
        """Set stations to highlight"""
        self.highlighted_stations = station_names.copy()
    
    def get_station_at_position(self, metro_map: MetroMap, pos: Tuple[int, int]) -> Optional[str]:
        """
        Get station name at the given screen position
        
        Args:
            metro_map: MetroMap instance
            pos: Screen position (x, y)
            
        Returns:
            Station name if found, None otherwise
        """
        click_x, click_y = pos
        
        for station in metro_map.stations.values():
            station_x, station_y = station.position
            
            # Calculate distance from click to station center
            distance = math.sqrt((click_x - station_x) ** 2 + (click_y - station_y) ** 2)
            
            # Check if click is within station radius
            if distance <= self.station_radius + 2:  # Small tolerance
                return station.name
        
        return None
    
    def render_legend(self, surface: pygame.Surface, x: int, y: int):
        """
        Render a legend explaining colors and symbols
        
        Args:
            surface: Surface to render on
            x: Legend x position
            y: Legend y position
        """
        legend_items = [
            ("Factions:", None),
            ("Rangers", self.colors["RANGERS"]),
            ("Polis", self.colors["POLIS"]),
            ("Fourth Reich", self.colors["FOURTH_REICH"]),
            ("Red Line", self.colors["RED_LINE"]),
            ("Hanza", self.colors["HANZA"]),
            ("", None),
            ("Tunnel States:", None),
            ("Clear", self.colors["TUNNEL_CLEAR"]),
            ("Hazardous", self.colors["TUNNEL_HAZARDOUS"]),
            ("Infested", self.colors["TUNNEL_INFESTED"]),
            ("Collapsed", self.colors["TUNNEL_COLLAPSED"]),
            ("", None),
            ("Trade:", None),
            ("Active Route", (0, 255, 0)),
            ("Caravan", (255, 255, 0))
        ]
        
        current_y = y
        for item_text, item_color in legend_items:
            if item_color:
                # Draw color indicator
                pygame.draw.circle(surface, item_color, (x + 10, current_y + 8), 6)
                
                # Draw text
                text_surface = self.font_small.render(item_text, True, self.colors["WHITE"])
                surface.blit(text_surface, (x + 25, current_y))
            else:
                # Header text
                if item_text:
                    text_surface = self.font_medium.render(item_text, True, self.colors["WHITE"])
                    surface.blit(text_surface, (x, current_y))
            
            current_y += 18