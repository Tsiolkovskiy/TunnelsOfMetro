"""
Message and Feedback System
Comprehensive system for displaying messages, notifications, and feedback
"""

import pygame
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass

from core.config import Config


class MessageType(Enum):
    """Types of messages"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    COMBAT = "combat"
    TRADE = "trade"
    DIPLOMACY = "diplomacy"
    EVENT = "event"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Message:
    """Individual message data"""
    text: str
    message_type: MessageType
    priority: MessagePriority
    timestamp: float
    duration: float = 5.0
    fade_duration: float = 1.0
    persistent: bool = False
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()
    
    def is_expired(self, current_time: float) -> bool:
        """Check if message has expired"""
        if self.persistent:
            return False
        return current_time > self.timestamp + self.duration
    
    def get_alpha(self, current_time: float) -> int:
        """Get alpha value for fade effect"""
        if self.persistent:
            return 255
        
        age = current_time - self.timestamp
        
        if age < self.duration - self.fade_duration:
            return 255
        elif age < self.duration:
            # Fade out
            fade_progress = (age - (self.duration - self.fade_duration)) / self.fade_duration
            return int(255 * (1.0 - fade_progress))
        else:
            return 0


class StatusMessage:
    """Temporary status message overlay"""
    
    def __init__(self, text: str, message_type: MessageType, duration: float = 3.0):
        self.text = text
        self.message_type = message_type
        self.duration = duration
        self.timestamp = time.time()
        self.fade_duration = 0.5
    
    def is_expired(self, current_time: float) -> bool:
        return current_time > self.timestamp + self.duration
    
    def get_alpha(self, current_time: float) -> int:
        age = current_time - self.timestamp
        
        if age < self.duration - self.fade_duration:
            return 255
        elif age < self.duration:
            fade_progress = (age - (self.duration - self.fade_duration)) / self.fade_duration
            return int(255 * (1.0 - fade_progress))
        else:
            return 0


class MessageSystem:
    """
    Complete message and feedback system
    
    Features:
    - Status message overlay
    - Event feed with scrolling history
    - Message filtering and prioritization
    - Visual feedback effects
    - Sound integration (ready for implementation)
    """
    
    def __init__(self, config: Config):
        """
        Initialize message system
        
        Args:
            config: Game configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize fonts
        pygame.font.init()
        self.font_small = pygame.font.SysFont('Arial', 11)
        self.font_medium = pygame.font.SysFont('Arial', 13)
        self.font_large = pygame.font.SysFont('Arial', 16, bold=True)
        
        # Colors
        self.colors = self._setup_colors()
        
        # Message storage
        self.messages: List[Message] = []
        self.status_messages: List[StatusMessage] = []
        self.max_messages = 50  # Maximum messages to keep in history
        
        # Event feed settings
        self.event_feed_visible = True
        self.event_feed_width = 300
        self.event_feed_height = 200
        self.event_feed_max_lines = 10
        
        # Status message settings
        self.status_message_duration = 3.0
        
        self.logger.info("Message system initialized")
    
    def _setup_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Setup color palette for messages"""
        return {
            # Message type colors
            "info": (200, 200, 255),
            "success": (100, 255, 100),
            "warning": (255, 255, 100),
            "error": (255, 100, 100),
            "combat": (255, 150, 150),
            "trade": (150, 255, 150),
            "diplomacy": (150, 150, 255),
            "event": (255, 200, 100),
            
            # UI colors
            "background": (0, 0, 0, 180),
            "border": (100, 100, 100),
            "text_shadow": (0, 0, 0),
            "timestamp": (150, 150, 150),
            
            # Priority colors
            "priority_low": (100, 100, 100),
            "priority_normal": (200, 200, 200),
            "priority_high": (255, 255, 200),
            "priority_critical": (255, 200, 200)
        }
    
    def add_message(self, text: str, message_type: MessageType = MessageType.INFO, 
                   priority: MessagePriority = MessagePriority.NORMAL,
                   duration: float = 5.0, persistent: bool = False):
        """
        Add a message to the system
        
        Args:
            text: Message text
            message_type: Type of message
            priority: Message priority
            duration: How long to display the message
            persistent: Whether message stays until manually cleared
        """
        message = Message(
            text=text,
            message_type=message_type,
            priority=priority,
            timestamp=time.time(),
            duration=duration,
            persistent=persistent
        )
        
        self.messages.append(message)
        
        # Keep only the most recent messages
        if len(self.messages) > self.max_messages:
            # Remove oldest non-persistent messages
            self.messages = [msg for msg in self.messages if msg.persistent] + \
                           self.messages[-(self.max_messages - len([msg for msg in self.messages if msg.persistent])):]
        
        self.logger.debug(f"Added {message_type.value} message: {text}")
    
    def add_status_message(self, text: str, message_type: MessageType = MessageType.INFO,
                          duration: float = None):
        """
        Add a temporary status message overlay
        
        Args:
            text: Message text
            message_type: Type of message
            duration: How long to display (uses default if None)
        """
        if duration is None:
            duration = self.status_message_duration
        
        status_message = StatusMessage(text, message_type, duration)
        self.status_messages.append(status_message)
        
        self.logger.debug(f"Added status message: {text}")
    
    def add_action_feedback(self, action: str, station: str, result: Dict[str, Any]):
        """
        Add feedback for a player action
        
        Args:
            action: Action that was performed
            station: Station where action was performed
            result: Result dictionary from action execution
        """
        success = result.get("success", False)
        message = result.get("message", "Action completed")
        
        # Determine message type based on action and result
        if success:
            if action in ["attack", "combat"]:
                msg_type = MessageType.COMBAT
            elif action in ["trade"]:
                msg_type = MessageType.TRADE
            elif action in ["diplomacy"]:
                msg_type = MessageType.DIPLOMACY
            else:
                msg_type = MessageType.SUCCESS
        else:
            msg_type = MessageType.ERROR
        
        # Add to both event feed and status overlay
        self.add_message(f"{action.title()} at {station}: {message}", msg_type)
        self.add_status_message(message, msg_type)
    
    def add_event_message(self, event_text: str, priority: MessagePriority = MessagePriority.NORMAL):
        """
        Add a game event message
        
        Args:
            event_text: Event description
            priority: Event priority
        """
        self.add_message(event_text, MessageType.EVENT, priority, duration=8.0)
        
        # High priority events also get status overlay
        if priority in [MessagePriority.HIGH, MessagePriority.CRITICAL]:
            self.add_status_message(event_text, MessageType.EVENT, duration=4.0)
    
    def add_turn_message(self, turn_number: int):
        """Add turn advancement message"""
        self.add_message(f"Turn {turn_number} begins", MessageType.INFO, 
                        MessagePriority.LOW, duration=3.0)
    
    def add_resource_warning(self, resource: str, amount: int):
        """Add resource shortage warning"""
        self.add_message(f"Low {resource}: {amount} remaining", MessageType.WARNING,
                        MessagePriority.HIGH, duration=6.0)
        self.add_status_message(f"Warning: Low {resource}!", MessageType.WARNING)
    
    def clear_messages(self, message_type: Optional[MessageType] = None):
        """
        Clear messages
        
        Args:
            message_type: Specific type to clear, or None for all
        """
        if message_type:
            self.messages = [msg for msg in self.messages if msg.message_type != message_type]
        else:
            self.messages.clear()
        
        self.logger.debug(f"Cleared messages: {message_type.value if message_type else 'all'}")
    
    def update(self, dt: float):
        """
        Update message system
        
        Args:
            dt: Delta time since last update
        """
        current_time = time.time()
        
        # Remove expired messages
        self.messages = [msg for msg in self.messages if not msg.is_expired(current_time)]
        self.status_messages = [msg for msg in self.status_messages if not msg.is_expired(current_time)]
    
    def render_status_messages(self, surface: pygame.Surface):
        """Render temporary status message overlays"""
        if not self.status_messages:
            return
        
        current_time = time.time()
        y_offset = surface.get_height() // 2 - 50
        
        for status_msg in self.status_messages:
            alpha = status_msg.get_alpha(current_time)
            if alpha <= 0:
                continue
            
            # Get message color
            color = self.colors.get(status_msg.message_type.value, self.colors["info"])
            
            # Create message surface
            text_surface = self.font_large.render(status_msg.text, True, color)
            text_rect = text_surface.get_rect()
            
            # Position at center
            msg_x = (surface.get_width() - text_rect.width) // 2
            msg_y = y_offset
            
            # Create background
            bg_width = text_rect.width + 40
            bg_height = text_rect.height + 20
            bg_x = msg_x - 20
            bg_y = msg_y - 10
            
            # Draw background with alpha
            bg_surface = pygame.Surface((bg_width, bg_height))
            bg_surface.set_alpha(min(alpha, 180))
            bg_surface.fill((0, 0, 0))
            surface.blit(bg_surface, (bg_x, bg_y))
            
            # Draw border
            border_color = (*color, min(alpha, 255))
            pygame.draw.rect(surface, color, (bg_x, bg_y, bg_width, bg_height), 2)
            
            # Draw text with alpha
            if alpha < 255:
                text_surface.set_alpha(alpha)
            surface.blit(text_surface, (msg_x, msg_y))
            
            y_offset += bg_height + 10
    
    def render_event_feed(self, surface: pygame.Surface):
        """Render the event feed"""
        if not self.event_feed_visible or not self.messages:
            return
        
        # Position event feed at bottom right
        feed_x = surface.get_width() - self.event_feed_width - 10
        feed_y = surface.get_height() - self.event_feed_height - 10
        
        # Draw background
        feed_rect = pygame.Rect(feed_x, feed_y, self.event_feed_width, self.event_feed_height)
        bg_surface = pygame.Surface((self.event_feed_width, self.event_feed_height))
        bg_surface.set_alpha(180)
        bg_surface.fill((0, 0, 0))
        surface.blit(bg_surface, (feed_x, feed_y))
        
        # Draw border
        pygame.draw.rect(surface, self.colors["border"], feed_rect, 1)
        
        # Draw header
        header_text = "Event Feed"
        header_surface = self.font_medium.render(header_text, True, (255, 255, 255))
        surface.blit(header_surface, (feed_x + 10, feed_y + 5))
        
        # Draw messages
        current_time = time.time()
        visible_messages = []
        
        # Get recent messages, prioritizing by importance
        sorted_messages = sorted(self.messages, key=lambda m: (m.timestamp, m.priority.value), reverse=True)
        
        for message in sorted_messages[:self.event_feed_max_lines]:
            alpha = message.get_alpha(current_time)
            if alpha > 50:  # Only show messages that are still reasonably visible
                visible_messages.append((message, alpha))
        
        # Render messages
        line_height = 16
        start_y = feed_y + 25
        
        for i, (message, alpha) in enumerate(visible_messages):
            if start_y + i * line_height > feed_y + self.event_feed_height - 10:
                break
            
            # Get message color
            color = self.colors.get(message.message_type.value, self.colors["info"])
            
            # Truncate long messages
            max_chars = 35
            display_text = message.text
            if len(display_text) > max_chars:
                display_text = display_text[:max_chars-3] + "..."
            
            # Render message text
            text_surface = self.font_small.render(display_text, True, color)
            if alpha < 255:
                text_surface.set_alpha(alpha)
            
            surface.blit(text_surface, (feed_x + 10, start_y + i * line_height))
            
            # Render timestamp
            age = current_time - message.timestamp
            if age < 60:
                time_text = f"{int(age)}s"
            elif age < 3600:
                time_text = f"{int(age/60)}m"
            else:
                time_text = f"{int(age/3600)}h"
            
            time_surface = self.font_small.render(time_text, True, self.colors["timestamp"])
            if alpha < 255:
                time_surface.set_alpha(alpha)
            
            time_x = feed_x + self.event_feed_width - 30
            surface.blit(time_surface, (time_x, start_y + i * line_height))
    
    def render_action_feedback_effects(self, surface: pygame.Surface, effects: List[Dict[str, Any]]):
        """
        Render visual feedback effects for actions
        
        Args:
            surface: Surface to render on
            effects: List of effect dictionaries
        """
        current_time = time.time()
        
        for effect in effects:
            effect_type = effect.get("type", "")
            position = effect.get("position", (0, 0))
            timestamp = effect.get("timestamp", current_time)
            duration = effect.get("duration", 1.0)
            
            age = current_time - timestamp
            if age > duration:
                continue
            
            # Calculate effect progress (0.0 to 1.0)
            progress = age / duration
            alpha = int(255 * (1.0 - progress))
            
            if effect_type == "resource_gain":
                self._render_resource_gain_effect(surface, position, effect, alpha, progress)
            elif effect_type == "resource_loss":
                self._render_resource_loss_effect(surface, position, effect, alpha, progress)
            elif effect_type == "combat_hit":
                self._render_combat_effect(surface, position, effect, alpha, progress)
            elif effect_type == "trade_success":
                self._render_trade_effect(surface, position, effect, alpha, progress)
    
    def _render_resource_gain_effect(self, surface: pygame.Surface, position: Tuple[int, int],
                                   effect: Dict[str, Any], alpha: int, progress: float):
        """Render resource gain effect"""
        resource = effect.get("resource", "")
        amount = effect.get("amount", 0)
        
        # Floating text effect
        text = f"+{amount} {resource}"
        color = self.colors["success"]
        
        # Float upward
        y_offset = int(progress * 30)
        text_pos = (position[0], position[1] - y_offset)
        
        text_surface = self.font_medium.render(text, True, color)
        text_surface.set_alpha(alpha)
        surface.blit(text_surface, text_pos)
    
    def _render_resource_loss_effect(self, surface: pygame.Surface, position: Tuple[int, int],
                                   effect: Dict[str, Any], alpha: int, progress: float):
        """Render resource loss effect"""
        resource = effect.get("resource", "")
        amount = effect.get("amount", 0)
        
        # Floating text effect
        text = f"-{amount} {resource}"
        color = self.colors["error"]
        
        # Float upward
        y_offset = int(progress * 30)
        text_pos = (position[0], position[1] - y_offset)
        
        text_surface = self.font_medium.render(text, True, color)
        text_surface.set_alpha(alpha)
        surface.blit(text_surface, text_pos)
    
    def _render_combat_effect(self, surface: pygame.Surface, position: Tuple[int, int],
                            effect: Dict[str, Any], alpha: int, progress: float):
        """Render combat effect"""
        # Flash effect
        if progress < 0.3:
            flash_alpha = int(alpha * (1.0 - progress / 0.3))
            flash_surface = pygame.Surface((40, 40))
            flash_surface.set_alpha(flash_alpha)
            flash_surface.fill(self.colors["combat"])
            surface.blit(flash_surface, (position[0] - 20, position[1] - 20))
    
    def _render_trade_effect(self, surface: pygame.Surface, position: Tuple[int, int],
                           effect: Dict[str, Any], alpha: int, progress: float):
        """Render trade effect"""
        # Expanding circle effect
        radius = int(progress * 20)
        if radius > 0:
            pygame.draw.circle(surface, self.colors["trade"], position, radius, 2)
    
    def toggle_event_feed(self):
        """Toggle event feed visibility"""
        self.event_feed_visible = not self.event_feed_visible
        self.logger.debug(f"Event feed visibility: {self.event_feed_visible}")
    
    def get_message_count(self, message_type: Optional[MessageType] = None) -> int:
        """Get count of messages"""
        if message_type:
            return len([msg for msg in self.messages if msg.message_type == message_type])
        return len(self.messages)
    
    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """Get most recent messages"""
        return sorted(self.messages, key=lambda m: m.timestamp, reverse=True)[:count]