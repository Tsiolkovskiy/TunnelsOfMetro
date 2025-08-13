"""
Heads-Up Display (HUD) System
Minimalist UI overlay showing critical game information
"""

import pygame
import logging
from typing import Dict, Any, Optional, Tuple

from core.config import Config
from data.resources import ResourcePool


class HUD:
    """
    Minimalist HUD system for displaying critical game information
    
    Features:
    - Resource display in top-left corner
    - MGR display in top-right corner with distinctive styling
    - Turn counter and faction information
    - Clean, unobtrusive design
    """
    
    def __init__(self, config: Config):
        """
        Initialize HUD system
        
        Args:
            config: Game configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize fonts
        pygame.font.init()
        self.font_small = pygame.font.SysFont('Arial', 14)
        self.font_medium = pygame.font.SysFont('Arial', 16)
        self.font_large = pygame.font.SysFont('Arial', 18, bold=True)
        
        # Colors
        self.colors = self._setup_colors()
        
        # HUD state
        self.visible = True
        self.player_faction = "Rangers"  # Default player faction
        self.current_turn = 1
        
        # Resource icons (simple colored rectangles for now)
        self.resource_icons = self._create_resource_icons()
        
        self.logger.info("HUD system initialized")
    
    def _setup_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Setup color palette for HUD elements"""
        base_colors = self.config.COLORS
        
        return {
            # Base colors
            "WHITE": base_colors["WHITE"],
            "BLACK": base_colors["BLACK"],
            "GRAY": base_colors["GRAY"],
            "DARK_GRAY": base_colors["DARK_GRAY"],
            
            # Resource colors
            "FOOD": (139, 69, 19),        # Brown
            "WATER": (0, 191, 255),       # Deep sky blue
            "SCRAP": (169, 169, 169),     # Dark gray
            "MEDICINE": (255, 20, 147),   # Deep pink
            "MGR": (255, 215, 0),         # Gold
            
            # UI colors
            "HUD_BG": (0, 0, 0, 128),     # Semi-transparent black
            "HUD_BORDER": (100, 100, 100), # Gray border
            "CRITICAL": (255, 0, 0),      # Red for critical resources
            "WARNING": (255, 255, 0),     # Yellow for low resources
            "GOOD": (0, 255, 0),          # Green for abundant resources
        }
    
    def _create_resource_icons(self) -> Dict[str, pygame.Surface]:
        """Create simple colored icons for resources"""
        icons = {}
        icon_size = 12
        
        resource_colors = {
            "food": self.colors["FOOD"],
            "clean_water": self.colors["WATER"],
            "scrap": self.colors["SCRAP"],
            "medicine": self.colors["MEDICINE"],
            "mgr_rounds": self.colors["MGR"]
        }
        
        for resource, color in resource_colors.items():
            icon = pygame.Surface((icon_size, icon_size))
            icon.fill(color)
            pygame.draw.rect(icon, self.colors["WHITE"], icon.get_rect(), 1)
            icons[resource] = icon
        
        return icons
    
    def render(self, surface: pygame.Surface, game_state: Dict[str, Any]):
        """
        Render the complete HUD
        
        Args:
            surface: Pygame surface to render on
            game_state: Current game state information
        """
        if not self.visible:
            return
        
        # Update HUD state from game state
        self._update_state(game_state)
        
        # Render HUD components
        self._render_resource_panel(surface, game_state.get("player_resources"))
        self._render_mgr_display(surface, game_state.get("player_resources"))
        self._render_turn_info(surface)
        self._render_faction_info(surface)
        self._render_military_panel(surface, game_state)
        self._render_construction_panel(surface, game_state)
        self._render_production_panel(surface, game_state)
        self._render_events_panel(surface, game_state)
        self._render_victory_panel(surface, game_state)
        self._render_diplomatic_status(surface, game_state)
    
    def _update_state(self, game_state: Dict[str, Any]):
        """Update HUD state from game state"""
        self.current_turn = game_state.get("current_turn", 1)
        self.player_faction = game_state.get("player_faction", "Rangers")
    
    def _render_resource_panel(self, surface: pygame.Surface, resources: Optional[ResourcePool]):
        """Render resource display in top-left corner"""
        if not resources:
            return
        
        panel_x = 10
        panel_y = 10
        panel_width = 200
        panel_height = 120
        
        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        self._draw_panel_background(surface, panel_rect)
        
        # Panel header
        header_text = "Resources"
        header_surface = self.font_medium.render(header_text, True, self.colors["WHITE"])
        surface.blit(header_surface, (panel_x + 10, panel_y + 8))
        
        # Resource list
        y_offset = panel_y + 30
        resource_data = [
            ("food", "Food", resources.food),
            ("clean_water", "Water", resources.clean_water),
            ("scrap", "Scrap", resources.scrap),
            ("medicine", "Medicine", resources.medicine)
        ]
        
        for resource_key, display_name, amount in resource_data:
            self._render_resource_item(surface, panel_x + 10, y_offset, 
                                     resource_key, display_name, amount)
            y_offset += 20
    
    def _render_resource_item(self, surface: pygame.Surface, x: int, y: int, 
                            resource_key: str, display_name: str, amount: int):
        """Render a single resource item"""
        # Resource icon
        if resource_key in self.resource_icons:
            surface.blit(self.resource_icons[resource_key], (x, y + 2))
        
        # Resource name
        name_surface = self.font_small.render(display_name + ":", True, self.colors["WHITE"])
        surface.blit(name_surface, (x + 20, y))
        
        # Resource amount with color coding
        amount_color = self._get_resource_amount_color(resource_key, amount)
        amount_surface = self.font_small.render(str(amount), True, amount_color)
        surface.blit(amount_surface, (x + 120, y))
    
    def _get_resource_amount_color(self, resource_key: str, amount: int) -> Tuple[int, int, int]:
        """Get color for resource amount based on quantity"""
        # Define thresholds for different resources
        thresholds = {
            "food": {"critical": 10, "warning": 30},
            "clean_water": {"critical": 5, "warning": 15},
            "scrap": {"critical": 10, "warning": 25},
            "medicine": {"critical": 3, "warning": 10}
        }
        
        resource_thresholds = thresholds.get(resource_key, {"critical": 5, "warning": 15})
        
        if amount <= resource_thresholds["critical"]:
            return self.colors["CRITICAL"]
        elif amount <= resource_thresholds["warning"]:
            return self.colors["WARNING"]
        else:
            return self.colors["WHITE"]
    
    def _render_mgr_display(self, surface: pygame.Surface, resources: Optional[ResourcePool]):
        """Render MGR display in top-right corner with distinctive styling"""
        if not resources:
            return
        
        panel_width = 150
        panel_height = 60
        panel_x = surface.get_width() - panel_width - 10
        panel_y = 10
        
        # Draw distinctive MGR panel
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        self._draw_mgr_panel_background(surface, panel_rect)
        
        # MGR icon (larger and more prominent)
        mgr_icon_size = 20
        mgr_icon = pygame.Surface((mgr_icon_size, mgr_icon_size))
        mgr_icon.fill(self.colors["MGR"])
        pygame.draw.rect(mgr_icon, self.colors["WHITE"], mgr_icon.get_rect(), 2)
        surface.blit(mgr_icon, (panel_x + 10, panel_y + 10))
        
        # MGR label
        mgr_label = self.font_medium.render("MGR", True, self.colors["MGR"])
        surface.blit(mgr_label, (panel_x + 40, panel_y + 8))
        
        # MGR amount (large and prominent)
        mgr_amount = resources.mgr_rounds
        amount_color = self.colors["MGR"] if mgr_amount >= 10 else self.colors["CRITICAL"]
        amount_surface = self.font_large.render(str(mgr_amount), True, amount_color)
        surface.blit(amount_surface, (panel_x + 40, panel_y + 28))
    
    def _render_turn_info(self, surface: pygame.Surface):
        """Render turn counter and game time information"""
        panel_width = 120
        panel_height = 40
        panel_x = surface.get_width() - panel_width - 10
        panel_y = 80
        
        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        self._draw_panel_background(surface, panel_rect)
        
        # Turn counter
        turn_text = f"Turn {self.current_turn}"
        turn_surface = self.font_medium.render(turn_text, True, self.colors["WHITE"])
        surface.blit(turn_surface, (panel_x + 10, panel_y + 8))
        
        # Year (assuming each turn is a month, starting from 2033)
        year = 2033 + (self.current_turn - 1) // 12
        month = ((self.current_turn - 1) % 12) + 1
        date_text = f"{year}.{month:02d}"
        date_surface = self.font_small.render(date_text, True, self.colors["GRAY"])
        surface.blit(date_surface, (panel_x + 10, panel_y + 24))
    
    def _render_faction_info(self, surface: pygame.Surface):
        """Render player faction information"""
        panel_width = 120
        panel_height = 40
        panel_x = surface.get_width() - panel_width - 10
        panel_y = 130
        
        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        self._draw_panel_background(surface, panel_rect)
        
        # Faction name
        faction_surface = self.font_medium.render(self.player_faction, True, self.colors["WHITE"])
        surface.blit(faction_surface, (panel_x + 10, panel_y + 8))
        
        # Faction color indicator
        faction_colors = {
            "Rangers": (0, 200, 0),
            "Polis": (0, 100, 255),
            "Fourth Reich": (150, 0, 0),
            "Red Line": (255, 0, 0),
            "Hanza": (255, 165, 0)
        }
        
        faction_color = faction_colors.get(self.player_faction, self.colors["WHITE"])
        color_rect = pygame.Rect(panel_x + 10, panel_y + 24, 100, 8)
        pygame.draw.rect(surface, faction_color, color_rect)
        pygame.draw.rect(surface, self.colors["WHITE"], color_rect, 1)
    
    def _draw_panel_background(self, surface: pygame.Surface, rect: pygame.Rect):
        """Draw standard panel background"""
        # Semi-transparent background
        panel_surface = pygame.Surface((rect.width, rect.height))
        panel_surface.set_alpha(180)
        panel_surface.fill(self.colors["BLACK"])
        surface.blit(panel_surface, rect.topleft)
        
        # Border
        pygame.draw.rect(surface, self.colors["HUD_BORDER"], rect, 1)
    
    def _draw_mgr_panel_background(self, surface: pygame.Surface, rect: pygame.Rect):
        """Draw distinctive MGR panel background"""
        # Semi-transparent background with gold tint
        panel_surface = pygame.Surface((rect.width, rect.height))
        panel_surface.set_alpha(200)
        panel_surface.fill((20, 20, 0))  # Dark gold tint
        surface.blit(panel_surface, rect.topleft)
        
        # Gold border
        pygame.draw.rect(surface, self.colors["MGR"], rect, 2)
    
    def render_help_text(self, surface: pygame.Surface):
        """Render help text for keyboard shortcuts"""
        help_lines = [
            "Controls:",
            "H - Toggle HUD",
            "M - Toggle Messages", 
            "L - Toggle Legend",
            "SPACE - End Turn",
            "ESC - Exit"
        ]
        
        # Position in bottom left
        help_x = 10
        help_y = surface.get_height() - len(help_lines) * 16 - 10
        
        for i, line in enumerate(help_lines):
            color = self.colors["WHITE"] if i == 0 else self.colors["GRAY"]
            font = self.font_medium if i == 0 else self.font_small
            
            text_surface = font.render(line, True, color)
            surface.blit(text_surface, (help_x, help_y + i * 16))
    
    def render_resource_tooltip(self, surface: pygame.Surface, resource_type: str, 
                              pos: Tuple[int, int]):
        """
        Render detailed tooltip for a resource
        
        Args:
            surface: Surface to render on
            resource_type: Type of resource
            pos: Position to render tooltip
        """
        # Resource descriptions
        descriptions = {
            "food": "Essential for population survival and growth",
            "clean_water": "Required for health and station operations",
            "scrap": "Raw materials for construction and repairs",
            "medicine": "Medical supplies for treating injuries and disease",
            "mgr_rounds": "Military-Grade Rounds - premium currency and ammunition"
        }
        
        description = descriptions.get(resource_type, "Unknown resource")
        
        # Create tooltip
        tooltip_lines = [
            resource_type.replace("_", " ").title(),
            description
        ]
        
        # Calculate tooltip size
        max_width = max(self.font_small.size(line)[0] for line in tooltip_lines)
        tooltip_width = max_width + 20
        tooltip_height = len(tooltip_lines) * 16 + 10
        
        # Position tooltip
        tooltip_x = min(pos[0], surface.get_width() - tooltip_width)
        tooltip_y = max(0, pos[1] - tooltip_height)
        
        # Draw tooltip background
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        self._draw_panel_background(surface, tooltip_rect)
        
        # Draw tooltip text
        for i, line in enumerate(tooltip_lines):
            font = self.font_medium if i == 0 else self.font_small
            color = self.colors["WHITE"] if i == 0 else self.colors["GRAY"]
            
            text_surface = font.render(line, True, color)
            surface.blit(text_surface, (tooltip_x + 10, tooltip_y + 5 + i * 16))
    
    def toggle_visibility(self):
        """Toggle HUD visibility"""
        self.visible = not self.visible
        self.logger.debug(f"HUD visibility: {self.visible}")
    
    def set_player_faction(self, faction: str):
        """Set the player's faction"""
        self.player_faction = faction
        self.logger.info(f"Player faction set to: {faction}")
    
    def _render_military_panel(self, surface: pygame.Surface, game_state: Dict[str, Any]):
        """Render military status summary"""
        panel_width = 150
        panel_height = 100
        panel_x = 10
        panel_y = 140
        
        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        self._draw_panel_background(surface, panel_rect)
        
        # Panel header
        header_text = "Military"
        header_surface = self.font_medium.render(header_text, True, self.colors["WHITE"])
        surface.blit(header_surface, (panel_x + 10, panel_y + 8))
        
        # Military statistics
        y_offset = panel_y + 30
        statistics = game_state.get("statistics", {})
        
        # Total military strength
        total_strength = statistics.get("total_military_strength", 0)
        strength_text = f"Strength: {total_strength}"
        strength_surface = self.font_small.render(strength_text, True, self.colors["WHITE"])
        surface.blit(strength_surface, (panel_x + 10, y_offset))
        
        # Units recruited
        units_recruited = statistics.get("units_recruited", 0)
        units_text = f"Units: {units_recruited}"
        units_surface = self.font_small.render(units_text, True, self.colors["WHITE"])
        surface.blit(units_surface, (panel_x + 10, y_offset + 16))
        
        # Battles won
        battles_won = statistics.get("battles_won", 0)
        battles_text = f"Victories: {battles_won}"
        battles_surface = self.font_small.render(battles_text, True, self.colors["WHITE"])
        surface.blit(battles_surface, (panel_x + 10, y_offset + 32))
        
        # Maintenance cost indicator (military + buildings)
        military_maintenance = game_state.get("military_maintenance_cost", {})
        building_maintenance = game_state.get("building_maintenance_cost", {})
        
        total_maintenance = sum(military_maintenance.values()) + sum(building_maintenance.values())
        if total_maintenance > 0:
            maintenance_text = f"Upkeep: {total_maintenance}"
            maintenance_color = self.colors["WARNING"] if total_maintenance > 20 else self.colors["WHITE"]
            maintenance_surface = self.font_small.render(maintenance_text, True, maintenance_color)
            surface.blit(maintenance_surface, (panel_x + 10, y_offset + 48))
    
    def _render_construction_panel(self, surface: pygame.Surface, game_state: Dict[str, Any]):
        """Render construction projects status"""
        construction_projects = game_state.get("construction_projects", [])
        if not construction_projects:
            return
        
        panel_width = 200
        panel_height = min(120, 30 + len(construction_projects) * 20)
        panel_x = surface.get_width() - panel_width - 10
        panel_y = 180
        
        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        self._draw_panel_background(surface, panel_rect)
        
        # Panel header
        header_text = "Construction"
        header_surface = self.font_medium.render(header_text, True, self.colors["WHITE"])
        surface.blit(header_surface, (panel_x + 10, panel_y + 8))
        
        # Construction projects
        y_offset = panel_y + 30
        for project in construction_projects[:4]:  # Show max 4 projects
            building_name = project["building_type"].replace("_", " ").title()
            progress = int(project["progress"] * 100)
            remaining = project["remaining_time"]
            
            project_text = f"{building_name}: {progress}%"
            project_surface = self.font_small.render(project_text, True, self.colors["WHITE"])
            surface.blit(project_surface, (panel_x + 10, y_offset))
            
            # Progress bar
            bar_width = 100
            bar_height = 4
            bar_x = panel_x + 10
            bar_y = y_offset + 12
            
            # Background bar
            pygame.draw.rect(surface, self.colors["DARK_GRAY"], 
                           (bar_x, bar_y, bar_width, bar_height))
            
            # Progress bar
            progress_width = int(bar_width * project["progress"])
            if progress_width > 0:
                pygame.draw.rect(surface, self.colors["GOOD"], 
                               (bar_x, bar_y, progress_width, bar_height))
            
            y_offset += 20
    
    def _render_production_panel(self, surface: pygame.Surface, game_state: Dict[str, Any]):
        """Render production summary panel"""
        production_summary = game_state.get("production_summary", {})
        if not production_summary:
            return
        
        panel_width = 180
        panel_height = 100
        panel_x = 10
        panel_y = 340
        
        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        self._draw_panel_background(surface, panel_rect)
        
        # Panel header
        header_text = "Production"
        header_surface = self.font_medium.render(header_text, True, self.colors["WHITE"])
        surface.blit(header_surface, (panel_x + 10, panel_y + 8))
        
        # Production efficiency
        avg_efficiency = production_summary.get("average_efficiency", 1.0)
        efficiency_text = f"Efficiency: {avg_efficiency:.1f}x"
        efficiency_color = self.colors["GOOD"] if avg_efficiency >= 1.0 else self.colors["WARNING"]
        efficiency_surface = self.font_small.render(efficiency_text, True, efficiency_color)
        surface.blit(efficiency_surface, (panel_x + 10, panel_y + 30))
        
        # Current season
        season = production_summary.get("current_season", "unknown")
        season_text = f"Season: {season.title()}"
        season_surface = self.font_small.render(season_text, True, self.colors["WHITE"])
        surface.blit(season_surface, (panel_x + 10, panel_y + 46))
        
        # Net production summary
        net_production = production_summary.get("net_production", {})
        y_offset = panel_y + 62
        
        for resource, amount in net_production.items():
            if amount != 0:
                color = self.colors["GOOD"] if amount > 0 else self.colors["CRITICAL"]
                text = f"{resource.replace('_', ' ').title()}: {amount:+d}"
                text_surface = self.font_small.render(text, True, color)
                surface.blit(text_surface, (panel_x + 10, y_offset))
                y_offset += 12
                
                if y_offset > panel_y + panel_height - 10:
                    break
    
    def _render_events_panel(self, surface: pygame.Surface, game_state: Dict[str, Any]):
        """Render active events panel"""
        active_events = game_state.get("active_events", [])
        triggered_events = game_state.get("triggered_events", [])
        
        # Show triggered events or active events
        events_to_show = triggered_events if triggered_events else active_events
        
        if not events_to_show:
            return
        
        panel_width = 250
        panel_height = min(150, 40 + len(events_to_show) * 30)
        panel_x = surface.get_width() - panel_width - 10
        panel_y = surface.get_height() - panel_height - 10
        
        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        self._draw_panel_background(surface, panel_rect)
        
        # Panel header
        header_text = "Recent Events" if triggered_events else "Active Events"
        header_surface = self.font_medium.render(header_text, True, self.colors["WHITE"])
        surface.blit(header_surface, (panel_x + 10, panel_y + 8))
        
        # Event list
        y_offset = panel_y + 30
        for event in events_to_show[:4]:  # Show max 4 events
            # Event severity color
            severity = event.get("severity", "minor")
            if severity == "catastrophic":
                event_color = self.colors["CRITICAL"]
            elif severity == "major":
                event_color = (255, 165, 0)  # Orange
            elif severity == "moderate":
                event_color = self.colors["WARNING"]
            else:
                event_color = self.colors["WHITE"]
            
            # Event title
            title = event.get("title", "Unknown Event")
            if len(title) > 30:
                title = title[:27] + "..."
            
            title_surface = self.font_small.render(title, True, event_color)
            surface.blit(title_surface, (panel_x + 10, y_offset))
            
            # Event target/location
            target = event.get("target", "")
            if target:
                target_text = f"@ {target}"
                target_surface = self.font_small.render(target_text, True, self.colors["GRAY"])
                surface.blit(target_surface, (panel_x + 10, y_offset + 12))
            
            y_offset += 30
            
            if y_offset > panel_y + panel_height - 20:
                break
    
    def _render_events_panel(self, surface: pygame.Surface, game_state: Dict[str, Any]):
        """Render active events and recent triggers"""
        triggered_events = game_state.get("triggered_events", [])
        active_events = game_state.get("active_events", [])
        
        # Only show panel if there are events
        if not triggered_events and not active_events:
            return
        
        panel_width = 250
        panel_height = min(150, 40 + (len(triggered_events) + len(active_events)) * 25)
        panel_x = surface.get_width() - panel_width - 10
        panel_y = 350
        
        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        self._draw_panel_background(surface, panel_rect)
        
        # Panel header
        header_text = "Events"
        header_surface = self.font_medium.render(header_text, True, self.colors["WHITE"])
        surface.blit(header_surface, (panel_x + 10, panel_y + 8))
        
        y_offset = panel_y + 30
        
        # Show triggered events (new this turn)
        if triggered_events:
            for event in triggered_events[:3]:  # Show max 3 recent events
                severity_color = self._get_event_severity_color(event.get('severity', 'minor'))
                
                # Event title
                title = event.get('title', 'Unknown Event')
                if len(title) > 25:
                    title = title[:25] + "..."
                title_surface = self.font_small.render(f"🎲 {title}", True, severity_color)
                surface.blit(title_surface, (panel_x + 10, y_offset))
                
                y_offset += 20
                if y_offset > panel_y + panel_height - 20:
                    break
        
        # Show active events (ongoing)
        if active_events and y_offset < panel_y + panel_height - 20:
            for event in active_events[:2]:  # Show max 2 active events
                remaining = event.get('remaining_duration', 0)
                title = event.get('title', 'Unknown Event')
                if len(title) > 20:
                    title = title[:20] + "..."
                
                active_text = f"⏳ {title} ({remaining}t)"
                active_surface = self.font_small.render(active_text, True, self.colors["WARNING"])
                surface.blit(active_surface, (panel_x + 10, y_offset))
                
                y_offset += 15
    
    def _get_event_severity_color(self, severity: str) -> Tuple[int, int, int]:
        """Get color for event severity"""
        severity_colors = {
            "minor": self.colors["WHITE"],
            "moderate": self.colors["WARNING"],
            "major": self.colors["CRITICAL"],
            "catastrophic": (255, 0, 255)  # Magenta for catastrophic
        }
        return severity_colors.get(severity, self.colors["WHITE"])
    
    def _render_victory_panel(self, surface: pygame.Surface, game_state: Dict[str, Any]):
        """Render victory progress panel"""
        victory_progress = game_state.get("victory_progress", {})
        closest_victory = game_state.get("closest_victory")
        game_ended = game_state.get("game_ended", False)
        
        if not victory_progress and not game_ended:
            return
        
        panel_width = 200
        panel_height = 120
        panel_x = surface.get_width() - panel_width - 10
        panel_y = 450
        
        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        self._draw_panel_background(surface, panel_rect)
        
        # Panel header
        if game_ended:
            header_text = "VICTORY!"
            header_color = self.colors["GOOD"]
        else:
            header_text = "Victory Progress"
            header_color = self.colors["WHITE"]
        
        header_surface = self.font_medium.render(header_text, True, header_color)
        surface.blit(header_surface, (panel_x + 10, panel_y + 8))
        
        y_offset = panel_y + 30
        
        if game_ended:
            # Show victory achievement
            victory_status = game_state.get("victory_status", {})
            victory_type = victory_status.get("victory_achieved", "Unknown")
            victory_turn = victory_status.get("victory_turn", 0)
            victory_score = victory_status.get("victory_score", 0)
            
            victory_text = f"{victory_type.replace('_', ' ').title()}"
            victory_surface = self.font_small.render(victory_text, True, self.colors["GOOD"])
            surface.blit(victory_surface, (panel_x + 10, y_offset))
            
            turn_text = f"Turn {victory_turn}"
            turn_surface = self.font_small.render(turn_text, True, self.colors["WHITE"])
            surface.blit(turn_surface, (panel_x + 10, y_offset + 15))
            
            score_text = f"Score: {victory_score}"
            score_surface = self.font_small.render(score_text, True, self.colors["WHITE"])
            surface.blit(score_surface, (panel_x + 10, y_offset + 30))
        
        else:
            # Show closest victory progress
            if closest_victory:
                victory_type, progress = closest_victory
                progress_percent = int(progress * 100)
                
                closest_text = f"Closest: {victory_type.value.replace('_', ' ').title()}"
                closest_surface = self.font_small.render(closest_text, True, self.colors["WHITE"])
                surface.blit(closest_surface, (panel_x + 10, y_offset))
                
                progress_text = f"Progress: {progress_percent}%"
                progress_color = self.colors["GOOD"] if progress_percent >= 75 else self.colors["WARNING"] if progress_percent >= 50 else self.colors["WHITE"]
                progress_surface = self.font_small.render(progress_text, True, progress_color)
                surface.blit(progress_surface, (panel_x + 10, y_offset + 15))
                
                # Progress bar
                bar_width = 180
                bar_height = 6
                bar_x = panel_x + 10
                bar_y = y_offset + 35
                
                # Background bar
                pygame.draw.rect(surface, self.colors["DARK_GRAY"], 
                               (bar_x, bar_y, bar_width, bar_height))
                
                # Progress bar
                progress_width = int(bar_width * progress)
                if progress_width > 0:
                    pygame.draw.rect(surface, progress_color, 
                                   (bar_x, bar_y, progress_width, bar_height))
            
            else:
                # Show general progress
                no_progress_text = "No significant progress"
                no_progress_surface = self.font_small.render(no_progress_text, True, self.colors["GRAY"])
                surface.blit(no_progress_surface, (panel_x + 10, y_offset))
    
    def _render_diplomatic_status(self, surface: pygame.Surface, game_state: Dict[str, Any]):
        """Render diplomatic status summary"""
        panel_width = 150
        panel_height = 80
        panel_x = 10
        panel_y = 250
        
        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        self._draw_panel_background(surface, panel_rect)
        
        # Panel header
        header_text = "Diplomacy"
        header_surface = self.font_medium.render(header_text, True, self.colors["WHITE"])
        surface.blit(header_surface, (panel_x + 10, panel_y + 8))
        
        # Show relationship counts (simplified)
        y_offset = panel_y + 30
        
        # This would be populated from game state in full implementation
        status_text = [
            "Allies: 1",
            "Neutral: 3", 
            "Enemies: 2"
        ]
        
        for i, text in enumerate(status_text):
            text_surface = self.font_small.render(text, True, self.colors["WHITE"])
            surface.blit(text_surface, (panel_x + 10, y_offset + i * 14))
    
    def get_hud_info(self) -> Dict[str, Any]:
        """Get current HUD state information"""
        return {
            "visible": self.visible,
            "player_faction": self.player_faction,
            "current_turn": self.current_turn
        }