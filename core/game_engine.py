"""
Core Game Engine
Manages the main game loop and system coordination
"""

import pygame
import logging
from typing import Optional

from core.config import Config
from systems.metro_map import MetroMap
from systems.game_state import GameStateManager
from systems.settings_system import SettingsSystem
from utils.performance_profiler import get_profiler, ProfileCategory
from utils.render_optimizer import RenderOptimizer
from ui.map_view import MapView
from ui.hud import HUD
from ui.message_system import MessageSystem, MessageType, MessagePriority
from ui.event_choice_interface import EventChoiceInterface
from utils.map_loader import MapLoader


class GameEngine:
    """Main game engine that coordinates all game systems"""
    
    def __init__(self, config: Config):
        """Initialize the game engine"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.clock = pygame.time.Clock()
        self.screen: Optional[pygame.Surface] = None
        
        # Game systems
        self.metro_map: Optional[MetroMap] = None
        self.game_state: Optional[GameStateManager] = None
        self.map_view: Optional[MapView] = None
        self.hud: Optional[HUD] = None
        self.message_system: Optional[MessageSystem] = None
        self.event_choice_interface: Optional[EventChoiceInterface] = None
        self.settings_system: Optional[SettingsSystem] = None
        self.render_optimizer: Optional[RenderOptimizer] = None
        self.profiler = get_profiler()
        
        # Initialize display
        self._init_display()
        
        # Initialize game systems
        self._init_game_systems()
        
    def _init_display(self):
        """Initialize the game display"""
        self.screen = pygame.display.set_mode(
            (self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption(self.config.GAME_TITLE)
        self.logger.info(f"Display initialized: {self.config.SCREEN_WIDTH}x{self.config.SCREEN_HEIGHT}")
        
    def _init_game_systems(self):
        """Initialize all game systems"""
        try:
            # Load the Metro map
            map_loader = MapLoader()
            self.metro_map = map_loader.load_default_map()
            self.logger.info("Metro map loaded successfully")
            
            # Initialize game state manager
            self.game_state = GameStateManager(self.metro_map)
            self.logger.info("Game state manager initialized")
            
            # Initialize map view
            self.map_view = MapView(self.config, self.metro_map)
            
            # Set up action interface callback
            self.map_view.action_interface.on_action_selected = self._on_action_selected
            
            # Connect game state to map view for fog of war
            self.map_view.set_game_state(self.game_state)
            
            self.logger.info("Map view initialized")
            
            # Initialize HUD
            self.hud = HUD(self.config)
            self.logger.info("HUD initialized")
            
            # Initialize message system
            self.message_system = MessageSystem(self.config)
            self.logger.info("Message system initialized")
            
            # Initialize event choice interface
            self.event_choice_interface = EventChoiceInterface(self.config)
            self.event_choice_interface.on_choice_selected = self._on_event_choice_selected
            self.logger.info("Event choice interface initialized")
            
            # Initialize settings system
            self.settings_system = SettingsSystem()
            self.logger.info("Settings system initialized")
            
            # Add welcome message
            self.message_system.add_message(
                "Welcome to the Metro. Survive at all costs.",
                MessageType.INFO,
                MessagePriority.NORMAL,
                duration=5.0
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize game systems: {e}")
            raise
        
    def run(self):
        """Main game loop"""
        self.running = True
        self.logger.info("Starting main game loop")
        
        while self.running:
            # Handle events
            self._handle_events()
            
            # Update game state
            self._update()
            
            # Render frame
            self._render()
            
            # Maintain target FPS
            self.clock.tick(self.config.TARGET_FPS)
            
        self.logger.info("Game loop ended")
        
    def _handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.logger.info("Quit event received")
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.logger.info("Escape key pressed - exiting")
                    self.running = False
                elif event.key == pygame.K_l:
                    # Toggle legend
                    if self.map_view:
                        self.map_view.toggle_legend()
                elif event.key == pygame.K_h:
                    # Toggle HUD
                    if self.hud:
                        self.hud.toggle_visibility()
                elif event.key == pygame.K_m:
                    # Toggle message feed
                    if self.message_system:
                        self.message_system.toggle_event_feed()
                elif event.key == pygame.K_SPACE:
                    # End turn (only if no interfaces are visible)
                    if not (self.map_view and self.map_view.action_interface.is_visible()) and \
                       not (self.event_choice_interface and self.event_choice_interface.is_visible()):
                        self._end_turn()
                elif event.key == pygame.K_F5:
                    # Quick save
                    self._quick_save()
                elif event.key == pygame.K_F9:
                    # Quick load (for now, just show message)
                    self._show_load_menu()
                elif event.key == pygame.K_s and (pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]):
                    # Ctrl+S for save
                    self._show_save_menu()
                else:
                    # Handle event choice interface first
                    if self.event_choice_interface and self.event_choice_interface.is_visible():
                        choice_id = self.event_choice_interface.handle_keyboard_input(event.key)
                        if choice_id:
                            self.logger.info(f"Event choice selected via keyboard: {choice_id}")
                    # Handle map keyboard shortcuts
                    elif self.map_view:
                        action = self.map_view.handle_keyboard_input(event.key)
                        if action:
                            self._handle_map_action(action)
                            
            elif event.type == pygame.MOUSEMOTION:
                # Handle event choice interface first
                if self.event_choice_interface and self.event_choice_interface.is_visible():
                    self.event_choice_interface.handle_mouse_motion(event.pos)
                # Handle map mouse movement
                elif self.map_view:
                    self.map_view.handle_mouse_motion(event.pos)
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle event choice interface first
                if self.event_choice_interface and self.event_choice_interface.is_visible():
                    choice_id = self.event_choice_interface.handle_mouse_click(event.pos, event.button)
                    if choice_id:
                        self.logger.info(f"Event choice selected via mouse: {choice_id}")
                # Handle map mouse clicks
                elif self.map_view:
                    clicked_station = self.map_view.handle_mouse_click(event.pos, event.button)
                    if clicked_station:
                        self._on_station_selected(clicked_station)
                    
                    # Show action interface on right-click
                    if event.button == 3 and self.map_view.interaction_manager.selected_station:
                        self.map_view._show_action_interface_for_selected()
                    
    def _update(self):
        """Update game state"""
        # Calculate delta time
        dt = self.clock.get_time() / 1000.0  # Convert to seconds
        
        # Update map view
        if self.map_view:
            self.map_view.update(dt)
        
        # Update message system
        if self.message_system:
            self.message_system.update(dt)
        
    def _render(self):
        """Render the current frame"""
        # Clear screen with dark background
        self.screen.fill(self.config.COLORS['BLACK'])
        
        # Render map view
        if self.map_view:
            self.map_view.render(self.screen)
        
        # Render HUD
        if self.hud and self.game_state:
            self.hud.render(self.screen, self.game_state.get_game_state())
        
        # Render message system
        if self.message_system:
            self.message_system.render_event_feed(self.screen)
            self.message_system.render_status_messages(self.screen)
        
        # Render UI overlay
        self._render_ui_overlay()
        
        # Render event choice interface (on top of everything)
        if self.event_choice_interface:
            self.event_choice_interface.render(self.screen)
        
        # Update display
        pygame.display.flip()
        
    def _render_ui_overlay(self):
        """Render UI elements over the map"""
        # Render selected station info
        if self.map_view and self.map_view.selected_station:
            self._render_station_info_panel()
    
    def _render_station_info_panel(self):
        """Render information panel for selected station"""
        station_info = self.map_view.get_selected_station_info()
        if not station_info:
            return
        
        # Create info panel
        panel_width = 280
        panel_height = 300
        panel_x = self.config.SCREEN_WIDTH - panel_width - 10
        panel_y = 10
        
        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), panel_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), panel_rect, 2)
        
        # Render station information
        font = pygame.font.SysFont('Arial', 12)
        font_bold = pygame.font.SysFont('Arial', 14, bold=True)
        y_offset = panel_y + 10
        
        # Station header
        header_text = f"{station_info['name']}"
        header_surface = font_bold.render(header_text, True, (255, 255, 255))
        self.screen.blit(header_surface, (panel_x + 10, y_offset))
        y_offset += 25
        
        info_lines = [
            f"Faction: {station_info['faction']}",
            f"Population: {station_info['population']}",
            f"Morale: {station_info['morale']}%",
            f"Status: {station_info['status']}",
            "",
            "Resources:",
        ]
        
        # Add resource information
        resources = station_info.get('resources', {})
        for resource, amount in resources.items():
            if amount > 0:
                info_lines.append(f"  {resource}: {amount}")
        
        # Add production information
        production = station_info.get('production', {})
        if any(amount > 0 for amount in production.values()):
            info_lines.append("")
            info_lines.append("Production:")
            for resource, amount in production.items():
                if amount > 0:
                    info_lines.append(f"  +{amount} {resource}/turn")
        
        # Add available actions
        actions = self.map_view.get_available_actions("Rangers")  # Assuming Rangers is player
        if actions:
            info_lines.append("")
            info_lines.append("Available Actions:")
            for action in actions[:5]:  # Show first 5 actions
                key_hint = {
                    "scout": "(S)",
                    "trade": "(T)", 
                    "attack": "(A)",
                    "diplomacy": "(D)",
                    "fortify": "(F)",
                    "recruit": "(R)",
                    "develop": "(B)"
                }.get(action.get("name", ""), "")
                
                action_text = f"  {action.get('name', '').title()} {key_hint}"
                if not action.get("available", True):
                    action_text += " (unavailable)"
                
                info_lines.append(action_text)
        
        # Render text lines
        for i, line in enumerate(info_lines):
            if y_offset + i * 14 > panel_y + panel_height - 20:
                break  # Don't overflow panel
                
            text_surface = font.render(line, True, (255, 255, 255))
            self.screen.blit(text_surface, (panel_x + 10, y_offset + i * 14))
    
    def _on_station_selected(self, station_name: str):
        """Handle station selection"""
        self.logger.info(f"Station selected: {station_name}")
        
        # Show available actions for the station
        if self.map_view:
            actions = self.map_view.get_available_actions("Rangers")  # Assuming Rangers is player faction
            self.logger.debug(f"Available actions: {actions}")
    
    def _handle_map_action(self, action: str):
        """Handle map action triggered by keyboard shortcut"""
        if not self.map_view or not self.map_view.selected_station or not self.game_state:
            return
        
        station_name = self.map_view.selected_station
        self.logger.info(f"Executing action '{action}' on station {station_name}")
        
        # Execute action through game state manager
        # For actions that need targets, we'll use the selected station as both origin and target for now
        result = self.game_state.execute_action(action, station_name, station_name)
        
        # Show result message through message system
        if self.message_system:
            self.message_system.add_action_feedback(action, station_name, result)
        
        self.logger.info(f"Action result: {result['message']}")
    
    def _on_action_selected(self, action: str, station: str):
        """Handle action selected from action interface"""
        if not self.game_state:
            return
        
        self.logger.info(f"Action selected from interface: {action} on {station}")
        
        # Execute action through game state manager
        result = self.game_state.execute_action(action, station, station)
        
        # Show result message through message system
        if self.message_system:
            self.message_system.add_action_feedback(action, station, result)
        
        self.logger.info(f"Action result: {result['message']}")
    
    def _check_resource_warnings(self):
        """Check for low resources and add warnings"""
        if not self.game_state or not self.message_system:
            return
        
        resources = self.game_state.get_player_resource_amounts()
        
        # Define warning thresholds
        thresholds = {
            "food": 20,
            "clean_water": 10,
            "scrap": 15,
            "medicine": 5,
            "mgr_rounds": 10
        }
        
        for resource, threshold in thresholds.items():
            amount = resources.get(resource, 0)
            if amount <= threshold:
                self.message_system.add_resource_warning(resource, amount)
    
    def _check_victory_status(self):
        """Check for victory conditions and show victory messages"""
        if not self.game_state or not self.message_system:
            return
        
        if self.game_state.is_game_ended():
            victory_status = self.game_state.get_victory_status()
            victory_type = victory_status.get("victory_achieved")
            victory_turn = victory_status.get("victory_turn")
            victory_score = victory_status.get("victory_score")
            
            if victory_type and victory_turn:
                victory_message = f"Victory achieved! {victory_type.replace('_', ' ').title()} victory on turn {victory_turn}"
                self.message_system.add_message(
                    victory_message,
                    MessageType.SUCCESS,
                    MessagePriority.CRITICAL,
                    duration=15.0
                )
                
                score_message = f"Final Score: {victory_score}"
                self.message_system.add_message(
                    score_message,
                    MessageType.INFO,
                    MessagePriority.HIGH,
                    duration=10.0
                )
                
                self.logger.info(f"Game ended with {victory_type} victory on turn {victory_turn}, score: {victory_score}")
    
    def _quick_save(self):
        """Create a quick save"""
        if not self.game_state:
            return
        
        result = self.game_state.create_quick_save()
        
        if self.message_system:
            if result["success"]:
                self.message_system.add_message(
                    "Game saved successfully",
                    MessageType.SUCCESS,
                    MessagePriority.NORMAL,
                    duration=3.0
                )
            else:
                self.message_system.add_message(
                    f"Save failed: {result['message']}",
                    MessageType.ERROR,
                    MessagePriority.HIGH,
                    duration=5.0
                )
        
        self.logger.info(f"Quick save result: {result['message']}")
    
    def _show_save_menu(self):
        """Show save menu (placeholder for now)"""
        if self.message_system:
            self.message_system.add_message(
                "Save menu not yet implemented. Use F5 for quick save.",
                MessageType.INFO,
                MessagePriority.NORMAL,
                duration=3.0
            )
    
    def _show_load_menu(self):
        """Show load menu (placeholder for now)"""
        if self.message_system:
            self.message_system.add_message(
                "Load menu not yet implemented.",
                MessageType.INFO,
                MessagePriority.NORMAL,
                duration=3.0
            )
    
    def _create_auto_save(self):
        """Create an auto-save if enabled"""
        if not self.game_state or not self.settings_system:
            return
        
        # Check if auto-save is enabled
        auto_save_enabled = self.settings_system.get_setting("gameplay", "auto_save_enabled")
        auto_save_frequency = self.settings_system.get_setting("gameplay", "auto_save_frequency")
        
        if auto_save_enabled and self.game_state.current_turn % auto_save_frequency == 0:
            result = self.game_state.create_auto_save()
            
            if result["success"]:
                self.logger.info(f"Auto-save created for turn {self.game_state.current_turn}")
                if self.message_system:
                    self.message_system.add_message(
                        "Auto-save created",
                        MessageType.INFO,
                        MessagePriority.LOW,
                        duration=2.0
                    )
            else:
                self.logger.warning(f"Auto-save failed: {result['message']}")
    
    def _end_turn(self):
        """End current turn and advance to next"""
        if not self.game_state:
            return
        
        self.game_state.advance_turn()
        self.logger.info(f"Turn ended. Now turn {self.game_state.current_turn}")
        
        # Show turn advancement message
        if self.message_system:
            self.message_system.add_turn_message(self.game_state.current_turn)
        
        # Check for resource warnings
        self._check_resource_warnings()
        
        # Check for victory conditions
        self._check_victory_status()
        
        # Check for triggered events that need player choices
        self._check_triggered_events()
        
        # Create auto-save if needed
        self._create_auto_save()
        
    def _check_triggered_events(self):
        """Check for events that were triggered this turn and need player choices"""
        if not self.game_state or not self.event_choice_interface:
            return
        
        triggered_events = self.game_state.get_triggered_events()
        
        for event in triggered_events:
            # Show events that have choices and aren't resolved
            if event.get("choices") and not event.get("resolved", False):
                self.event_choice_interface.show_event(event)
                
                # Add message about the event
                if self.message_system:
                    severity = event.get("severity", "minor")
                    message_type = MessageType.WARNING if severity in ["major", "catastrophic"] else MessageType.INFO
                    
                    self.message_system.add_message(
                        f"Event: {event.get('title', 'Unknown Event')}",
                        message_type,
                        MessagePriority.HIGH,
                        duration=8.0
                    )
                
                # Only show one event at a time
                break
    
    def _on_event_choice_selected(self, event_id: str, choice_id: str):
        """Handle event choice selection"""
        if not self.game_state:
            return
        
        self.logger.info(f"Processing event choice: {event_id} -> {choice_id}")
        
        # Resolve the choice through the game state
        result = self.game_state.resolve_event_choice(event_id, choice_id)
        
        if result["success"]:
            # Show success message
            if self.message_system:
                self.message_system.add_message(
                    result.get("message", "Event choice resolved"),
                    MessageType.SUCCESS,
                    MessagePriority.NORMAL,
                    duration=5.0
                )
            
            # Check for immediate consequences
            effects = result.get("effects", {})
            if effects:
                self._show_event_consequences(effects)
        else:
            # Show error message
            if self.message_system:
                self.message_system.add_message(
                    f"Failed to resolve choice: {result.get('message', 'Unknown error')}",
                    MessageType.ERROR,
                    MessagePriority.HIGH,
                    duration=5.0
                )
    
    def _show_event_consequences(self, effects: Dict[str, Any]):
        """Show consequences of event choices"""
        if not self.message_system:
            return
        
        # Show resource changes
        if "resources_gained" in effects:
            resources = effects["resources_gained"]
            resource_text = ", ".join(f"+{amount} {resource}" for resource, amount in resources.items())
            self.message_system.add_message(
                f"Resources gained: {resource_text}",
                MessageType.SUCCESS,
                MessagePriority.NORMAL,
                duration=4.0
            )
        
        if "mgr_gained" in effects:
            mgr_amount = effects["mgr_gained"]
            self.message_system.add_message(
                f"Gained {mgr_amount} MGR rounds",
                MessageType.SUCCESS,
                MessagePriority.NORMAL,
                duration=4.0
            )
        
        # Show tunnel changes
        if "tunnel_cleared" in effects:
            tunnel = effects["tunnel_cleared"]
            self.message_system.add_message(
                f"Tunnel cleared: {tunnel}",
                MessageType.INFO,
                MessagePriority.NORMAL,
                duration=4.0
            )
    
    def shutdown(self):
        """Clean shutdown of the game engine"""
        self.running = False
        self.logger.info("Game engine shutdown requested")