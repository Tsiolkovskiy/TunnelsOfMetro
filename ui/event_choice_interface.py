"""
Event Choice Interface
Provides UI for player to make choices in response to events
"""

import pygame
import logging
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from core.config import Config


class ChoiceButtonState(Enum):
    """States for choice buttons"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    HOVERED = "hovered"
    SELECTED = "selected"


class EventChoiceButton:
    """Individual choice button for event responses"""
    
    def __init__(self, choice_data: Dict[str, Any], position: tuple, size: tuple):
        """
        Initialize choice button
        
        Args:
            choice_data: Choice information dictionary
            position: Button position (x, y)
            size: Button size (width, height)
        """
        self.choice_data = choice_data
        self.rect = pygame.Rect(position[0], position[1], size[0], size[1])
        self.state = ChoiceButtonState.AVAILABLE if choice_data.get("available", True) else ChoiceButtonState.UNAVAILABLE
        
        # Visual properties
        self.font_title = pygame.font.SysFont('Arial', 12, bold=True)
        self.font_desc = pygame.font.SysFont('Arial', 10)
        self.font_cost = pygame.font.SysFont('Arial', 9)
        
        # Colors
        self.colors = self._setup_colors()
        
        # Interaction state
        self.hovered = False
    
    def _setup_colors(self) -> Dict[str, tuple]:
        """Setup button colors"""
        return {
            "available_bg": (40, 60, 40),
            "available_border": (80, 120, 80),
            "available_text": (255, 255, 255),
            
            "unavailable_bg": (60, 40, 40),
            "unavailable_border": (120, 80, 80),
            "unavailable_text": (180, 180, 180),
            
            "hovered_bg": (60, 80, 60),
            "hovered_border": (120, 160, 120),
            "hovered_text": (255, 255, 255),
            
            "selected_bg": (80, 100, 80),
            "selected_border": (160, 200, 160),
            "selected_text": (255, 255, 255),
            
            "cost_text": (255, 255, 100),
            "requirement_text": (255, 150, 150)
        }
    
    def handle_mouse_motion(self, pos: tuple):
        """Handle mouse movement over button"""
        old_hovered = self.hovered
        self.hovered = self.rect.collidepoint(pos)
        
        if self.hovered != old_hovered and self.state == ChoiceButtonState.AVAILABLE:
            self.state = ChoiceButtonState.HOVERED if self.hovered else ChoiceButtonState.AVAILABLE
    
    def handle_mouse_click(self, pos: tuple, button: int) -> bool:
        """
        Handle mouse click on button
        
        Returns:
            True if button was clicked and choice should be executed
        """
        if not self.rect.collidepoint(pos) or self.state == ChoiceButtonState.UNAVAILABLE:
            return False
        
        if button == 1:  # Left click
            return True
        
        return False
    
    def render(self, surface: pygame.Surface):
        """Render the choice button"""
        # Get colors based on state
        if self.state == ChoiceButtonState.UNAVAILABLE:
            bg_color = self.colors["unavailable_bg"]
            border_color = self.colors["unavailable_border"]
            text_color = self.colors["unavailable_text"]
        elif self.state == ChoiceButtonState.HOVERED:
            bg_color = self.colors["hovered_bg"]
            border_color = self.colors["hovered_border"]
            text_color = self.colors["hovered_text"]
        elif self.state == ChoiceButtonState.SELECTED:
            bg_color = self.colors["selected_bg"]
            border_color = self.colors["selected_border"]
            text_color = self.colors["selected_text"]
        else:
            bg_color = self.colors["available_bg"]
            border_color = self.colors["available_border"]
            text_color = self.colors["available_text"]
        
        # Draw button background
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 2)
        
        # Draw choice content
        y_offset = self.rect.y + 8
        
        # Choice description (main text)
        description = self.choice_data.get("description", "Unknown choice")
        desc_lines = self._wrap_text(description, self.rect.width - 16, self.font_desc)
        
        for line in desc_lines[:3]:  # Max 3 lines
            text_surface = self.font_desc.render(line, True, text_color)
            surface.blit(text_surface, (self.rect.x + 8, y_offset))
            y_offset += 12
        
        # Show costs if any
        costs = self.choice_data.get("costs", {})
        if costs and y_offset < self.rect.bottom - 15:
            cost_text = "Cost: " + ", ".join(f"{amount} {resource}" for resource, amount in costs.items())
            cost_surface = self.font_cost.render(cost_text, True, self.colors["cost_text"])
            surface.blit(cost_surface, (self.rect.x + 8, y_offset))
            y_offset += 10
        
        # Show requirements if not met
        if not self.choice_data.get("available", True) and y_offset < self.rect.bottom - 10:
            req_text = self.choice_data.get("unavailable_reason", "Requirements not met")
            req_surface = self.font_cost.render(req_text, True, self.colors["requirement_text"])
            surface.blit(req_surface, (self.rect.x + 8, y_offset))
    
    def _wrap_text(self, text: str, max_width: int, font: pygame.font.Font) -> List[str]:
        """Wrap text to fit within max width"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines


class EventChoiceInterface:
    """
    Complete event choice interface system
    
    Features:
    - Event presentation with rich descriptions
    - Multiple choice buttons with costs and requirements
    - Consequence preview and explanation
    - Choice validation and confirmation
    """
    
    def __init__(self, config: Config):
        """
        Initialize event choice interface
        
        Args:
            config: Game configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Interface state
        self.visible = False
        self.current_event: Optional[Dict[str, Any]] = None
        self.choice_buttons: List[EventChoiceButton] = []
        self.selected_choice: Optional[str] = None
        
        # Layout settings
        self.panel_width = 600
        self.panel_height = 500
        self.choice_button_width = 280
        self.choice_button_height = 80
        self.choice_spacing = 10
        
        # Callbacks
        self.on_choice_selected: Optional[Callable[[str, str], None]] = None
        self.on_interface_closed: Optional[Callable[[], None]] = None
        
        # Colors and fonts
        self.colors = self._setup_colors()
        self.fonts = self._setup_fonts()
        
        self.logger.info("Event choice interface initialized")
    
    def _setup_colors(self) -> Dict[str, tuple]:
        """Setup interface colors"""
        return {
            "panel_bg": (20, 20, 30, 240),
            "panel_border": (100, 100, 120),
            "header_bg": (40, 40, 60),
            "header_text": (255, 255, 255),
            "event_text": (220, 220, 220),
            "flavor_text": (180, 180, 200),
            "severity_minor": (100, 150, 100),
            "severity_moderate": (150, 150, 100),
            "severity_major": (150, 100, 100),
            "severity_catastrophic": (200, 50, 50),
            "button_bg": (60, 60, 80),
            "button_border": (120, 120, 140)
        }
    
    def _setup_fonts(self) -> Dict[str, pygame.font.Font]:
        """Setup interface fonts"""
        return {
            "title": pygame.font.SysFont('Arial', 18, bold=True),
            "subtitle": pygame.font.SysFont('Arial', 14, bold=True),
            "body": pygame.font.SysFont('Arial', 12),
            "small": pygame.font.SysFont('Arial', 10),
            "flavor": pygame.font.SysFont('Arial', 11, italic=True)
        }
    
    def show_event(self, event_data: Dict[str, Any], position: Optional[tuple] = None):
        """
        Show event choice interface for a specific event
        
        Args:
            event_data: Event information dictionary
            position: Optional position to display interface
        """
        self.current_event = event_data
        self.visible = True
        self.selected_choice = None
        
        # Calculate panel position (center of screen by default)
        if position:
            panel_x, panel_y = position
        else:
            panel_x = (self.config.SCREEN_WIDTH - self.panel_width) // 2
            panel_y = (self.config.SCREEN_HEIGHT - self.panel_height) // 2
        
        self.panel_rect = pygame.Rect(panel_x, panel_y, self.panel_width, self.panel_height)
        
        # Create choice buttons
        self._create_choice_buttons()
        
        self.logger.info(f"Showing event choice interface for: {event_data.get('title', 'Unknown Event')}")
    
    def hide(self):
        """Hide the event choice interface"""
        self.visible = False
        self.current_event = None
        self.choice_buttons.clear()
        self.selected_choice = None
        
        if self.on_interface_closed:
            self.on_interface_closed()
        
        self.logger.debug("Event choice interface hidden")
    
    def _create_choice_buttons(self):
        """Create buttons for event choices"""
        self.choice_buttons.clear()
        
        if not self.current_event or not self.current_event.get("choices"):
            return
        
        choices = self.current_event["choices"]
        
        # Calculate button layout (2 columns)
        buttons_per_row = 2
        button_start_x = self.panel_rect.x + 20
        button_start_y = self.panel_rect.y + 200  # Leave space for event description
        
        for i, choice in enumerate(choices):
            row = i // buttons_per_row
            col = i % buttons_per_row
            
            button_x = button_start_x + col * (self.choice_button_width + self.choice_spacing)
            button_y = button_start_y + row * (self.choice_button_height + self.choice_spacing)
            
            # Don't create buttons that would overflow the panel
            if button_y + self.choice_button_height > self.panel_rect.bottom - 20:
                break
            
            button = EventChoiceButton(
                choice,
                (button_x, button_y),
                (self.choice_button_width, self.choice_button_height)
            )
            
            self.choice_buttons.append(button)
    
    def handle_mouse_motion(self, pos: tuple):
        """Handle mouse movement"""
        if not self.visible:
            return
        
        # Update button hover states
        for button in self.choice_buttons:
            button.handle_mouse_motion(pos)
    
    def handle_mouse_click(self, pos: tuple, button: int) -> Optional[str]:
        """
        Handle mouse click
        
        Returns:
            Choice ID if a choice was selected
        """
        if not self.visible or not self.current_event:
            return None
        
        # Check if click is outside panel (close interface)
        if not self.panel_rect.collidepoint(pos):
            self.hide()
            return None
        
        # Check choice buttons
        for choice_button in self.choice_buttons:
            if choice_button.handle_mouse_click(pos, button):
                choice_id = choice_button.choice_data.get("choice_id")
                if choice_id:
                    self.selected_choice = choice_id
                    
                    if self.on_choice_selected:
                        event_id = self.current_event.get("event_id")
                        self.on_choice_selected(event_id, choice_id)
                    
                    self.hide()
                    return choice_id
        
        return None
    
    def handle_keyboard_input(self, key: int) -> Optional[str]:
        """
        Handle keyboard shortcuts
        
        Returns:
            Choice ID if a shortcut was triggered
        """
        if not self.visible or not self.current_event:
            return None
        
        # Number keys for choices (1-4)
        choice_keys = {
            pygame.K_1: 0,
            pygame.K_2: 1,
            pygame.K_3: 2,
            pygame.K_4: 3
        }
        
        if key in choice_keys:
            choice_index = choice_keys[key]
            if choice_index < len(self.choice_buttons):
                choice_button = self.choice_buttons[choice_index]
                if choice_button.state != ChoiceButtonState.UNAVAILABLE:
                    choice_id = choice_button.choice_data.get("choice_id")
                    if choice_id:
                        self.selected_choice = choice_id
                        
                        if self.on_choice_selected:
                            event_id = self.current_event.get("event_id")
                            self.on_choice_selected(event_id, choice_id)
                        
                        self.hide()
                        return choice_id
        
        # ESC to close interface
        if key == pygame.K_ESCAPE:
            self.hide()
        
        return None
    
    def render(self, surface: pygame.Surface):
        """Render the event choice interface"""
        if not self.visible or not self.current_event:
            return
        
        # Draw panel background
        panel_surface = pygame.Surface((self.panel_width, self.panel_height))
        panel_surface.set_alpha(240)
        panel_surface.fill((20, 20, 30))
        surface.blit(panel_surface, self.panel_rect.topleft)
        
        # Draw panel border
        pygame.draw.rect(surface, self.colors["panel_border"], self.panel_rect, 3)
        
        # Draw event content
        self._render_event_header(surface)
        self._render_event_description(surface)
        self._render_event_details(surface)
        
        # Draw choice buttons
        for button in self.choice_buttons:
            button.render(surface)
        
        # Draw instructions
        self._render_instructions(surface)
    
    def _render_event_header(self, surface: pygame.Surface):
        """Render event header with title and severity"""
        header_rect = pygame.Rect(self.panel_rect.x, self.panel_rect.y, self.panel_width, 40)
        pygame.draw.rect(surface, self.colors["header_bg"], header_rect)
        
        # Event title
        title = self.current_event.get("title", "Unknown Event")
        title_surface = self.fonts["title"].render(title, True, self.colors["header_text"])
        surface.blit(title_surface, (self.panel_rect.x + 15, self.panel_rect.y + 8))
        
        # Event severity indicator
        severity = self.current_event.get("severity", "minor")
        severity_color = self.colors.get(f"severity_{severity}", self.colors["severity_minor"])
        
        severity_text = f"[{severity.upper()}]"
        severity_surface = self.fonts["subtitle"].render(severity_text, True, severity_color)
        severity_x = self.panel_rect.right - severity_surface.get_width() - 15
        surface.blit(severity_surface, (severity_x, self.panel_rect.y + 10))
    
    def _render_event_description(self, surface: pygame.Surface):
        """Render event description"""
        desc_y = self.panel_rect.y + 50
        
        # Main description
        description = self.current_event.get("description", "No description available.")
        desc_lines = self._wrap_text(description, self.panel_width - 40, self.fonts["body"])
        
        for i, line in enumerate(desc_lines[:4]):  # Max 4 lines
            text_surface = self.fonts["body"].render(line, True, self.colors["event_text"])
            surface.blit(text_surface, (self.panel_rect.x + 20, desc_y + i * 16))
        
        # Flavor text if available
        flavor_text = self.current_event.get("flavor_text", "")
        if flavor_text:
            flavor_y = desc_y + len(desc_lines[:4]) * 16 + 10
            flavor_lines = self._wrap_text(flavor_text, self.panel_width - 40, self.fonts["flavor"])
            
            for i, line in enumerate(flavor_lines[:2]):  # Max 2 lines
                text_surface = self.fonts["flavor"].render(line, True, self.colors["flavor_text"])
                surface.blit(text_surface, (self.panel_rect.x + 20, flavor_y + i * 14))
    
    def _render_event_details(self, surface: pygame.Surface):
        """Render event details like scope and duration"""
        details_y = self.panel_rect.y + 160
        
        # Event scope and target
        scope = self.current_event.get("scope", "unknown")
        target = self.current_event.get("target", "")
        
        if target:
            detail_text = f"Affects: {target} ({scope})"
        else:
            detail_text = f"Scope: {scope}"
        
        detail_surface = self.fonts["small"].render(detail_text, True, self.colors["event_text"])
        surface.blit(detail_surface, (self.panel_rect.x + 20, details_y))
        
        # Duration if applicable
        duration = self.current_event.get("remaining_duration", 0)
        if duration > 1:
            duration_text = f"Duration: {duration} turns remaining"
            duration_surface = self.fonts["small"].render(duration_text, True, self.colors["event_text"])
            surface.blit(duration_surface, (self.panel_rect.x + 20, details_y + 15))
    
    def _render_instructions(self, surface: pygame.Surface):
        """Render keyboard instructions"""
        instructions_y = self.panel_rect.bottom - 30
        
        instruction_text = "Press 1-4 to select choice, ESC to close"
        instruction_surface = self.fonts["small"].render(instruction_text, True, self.colors["flavor_text"])
        
        # Center the instruction text
        text_x = self.panel_rect.x + (self.panel_width - instruction_surface.get_width()) // 2
        surface.blit(instruction_surface, (text_x, instructions_y))
    
    def _wrap_text(self, text: str, max_width: int, font: pygame.font.Font) -> List[str]:
        """Wrap text to fit within max width"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def is_visible(self) -> bool:
        """Check if interface is visible"""
        return self.visible
    
    def get_current_event(self) -> Optional[Dict[str, Any]]:
        """Get currently displayed event"""
        return self.current_event