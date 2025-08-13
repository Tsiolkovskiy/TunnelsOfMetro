"""
Visual Effects System
Manages particle effects, animations, and visual polish
"""

import pygame
import math
import random
import logging
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from utils.performance_profiler import get_profiler, ProfileCategory


class EffectType(Enum):
    """Types of visual effects"""
    PARTICLE_BURST = "particle_burst"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    PULSE = "pulse"
    SHAKE = "shake"
    FLOAT_TEXT = "float_text"
    TRAIL = "trail"
    EXPLOSION = "explosion"
    SPARKLE = "sparkle"


@dataclass
class Particle:
    """Individual particle for effects"""
    x: float
    y: float
    vel_x: float
    vel_y: float
    life: float
    max_life: float
    size: float
    color: Tuple[int, int, int]
    alpha: int = 255
    
    def update(self, dt: float):
        """Update particle state"""
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        self.life -= dt
        
        # Fade out over time
        life_ratio = self.life / self.max_life
        self.alpha = int(255 * life_ratio)
        
        # Apply gravity
        self.vel_y += 200 * dt  # Gravity acceleration
        
        # Air resistance
        self.vel_x *= 0.98
        self.vel_y *= 0.98
    
    def is_alive(self) -> bool:
        """Check if particle is still alive"""
        return self.life > 0
    
    def render(self, surface: pygame.Surface, camera_x: int = 0, camera_y: int = 0):
        """Render particle to surface"""
        if not self.is_alive():
            return
        
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        # Create particle surface with alpha
        particle_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color, self.alpha)
        pygame.draw.circle(particle_surface, color_with_alpha, 
                         (int(self.size), int(self.size)), int(self.size))
        
        surface.blit(particle_surface, (screen_x - self.size, screen_y - self.size))


@dataclass
class FloatingText:
    """Floating text effect"""
    x: float
    y: float
    text: str
    color: Tuple[int, int, int]
    font_size: int
    life: float
    max_life: float
    vel_y: float = -50  # Float upward
    
    def update(self, dt: float):
        """Update floating text"""
        self.y += self.vel_y * dt
        self.life -= dt
    
    def is_alive(self) -> bool:
        """Check if text is still alive"""
        return self.life > 0
    
    def render(self, surface: pygame.Surface, camera_x: int = 0, camera_y: int = 0):
        """Render floating text"""
        if not self.is_alive():
            return
        
        # Calculate alpha based on remaining life
        life_ratio = self.life / self.max_life
        alpha = int(255 * life_ratio)
        
        # Create font and render text
        font = pygame.font.SysFont('Arial', self.font_size, bold=True)
        text_surface = font.render(self.text, True, self.color)
        
        # Apply alpha
        text_surface.set_alpha(alpha)
        
        # Position on screen
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        # Center text
        text_rect = text_surface.get_rect()
        text_rect.center = (screen_x, screen_y)
        
        surface.blit(text_surface, text_rect)


class VisualEffect:
    """Base class for visual effects"""
    
    def __init__(self, x: float, y: float, duration: float):
        """
        Initialize visual effect
        
        Args:
            x: X position
            y: Y position
            duration: Effect duration in seconds
        """
        self.x = x
        self.y = y
        self.duration = duration
        self.elapsed = 0.0
        self.active = True
    
    def update(self, dt: float):
        """Update effect state"""
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
    
    def is_active(self) -> bool:
        """Check if effect is still active"""
        return self.active
    
    def get_progress(self) -> float:
        """Get effect progress (0.0 to 1.0)"""
        return min(1.0, self.elapsed / self.duration)
    
    def render(self, surface: pygame.Surface, camera_x: int = 0, camera_y: int = 0):
        """Render effect (override in subclasses)"""
        pass


class ParticleEffect(VisualEffect):
    """Particle burst effect"""
    
    def __init__(self, x: float, y: float, particle_count: int = 20, 
                 color: Tuple[int, int, int] = (255, 255, 255)):
        """
        Initialize particle effect
        
        Args:
            x: X position
            y: Y position
            particle_count: Number of particles to create
            color: Particle color
        """
        super().__init__(x, y, 2.0)  # 2 second duration
        self.particles: List[Particle] = []
        
        # Create particles
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 200)
            vel_x = math.cos(angle) * speed
            vel_y = math.sin(angle) * speed
            
            particle = Particle(
                x=x + random.uniform(-5, 5),
                y=y + random.uniform(-5, 5),
                vel_x=vel_x,
                vel_y=vel_y,
                life=random.uniform(1.0, 2.0),
                max_life=2.0,
                size=random.uniform(2, 6),
                color=color
            )
            self.particles.append(particle)
    
    def update(self, dt: float):
        """Update particle effect"""
        super().update(dt)
        
        # Update particles
        for particle in self.particles[:]:
            particle.update(dt)
            if not particle.is_alive():
                self.particles.remove(particle)
        
        # Effect is done when no particles remain
        if not self.particles:
            self.active = False
    
    def render(self, surface: pygame.Surface, camera_x: int = 0, camera_y: int = 0):
        """Render particle effect"""
        for particle in self.particles:
            particle.render(surface, camera_x, camera_y)


class PulseEffect(VisualEffect):
    """Pulsing circle effect"""
    
    def __init__(self, x: float, y: float, max_radius: float = 50, 
                 color: Tuple[int, int, int] = (255, 255, 0)):
        """
        Initialize pulse effect
        
        Args:
            x: X position
            y: Y position
            max_radius: Maximum pulse radius
            color: Pulse color
        """
        super().__init__(x, y, 1.0)  # 1 second duration
        self.max_radius = max_radius
        self.color = color
    
    def render(self, surface: pygame.Surface, camera_x: int = 0, camera_y: int = 0):
        """Render pulse effect"""
        if not self.is_active():
            return
        
        progress = self.get_progress()
        radius = int(self.max_radius * progress)
        alpha = int(255 * (1.0 - progress))  # Fade out as it expands
        
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        # Create surface with alpha
        pulse_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color, alpha)
        pygame.draw.circle(pulse_surface, color_with_alpha, (radius, radius), radius, 3)
        
        surface.blit(pulse_surface, (screen_x - radius, screen_y - radius))


class VisualEffectsSystem:
    """
    Visual effects management system
    
    Features:
    - Particle effects for actions and events
    - Floating text for feedback
    - Screen shake and camera effects
    - Animation and transition effects
    - Performance-optimized rendering
    """
    
    def __init__(self):
        """Initialize visual effects system"""
        self.logger = logging.getLogger(__name__)
        
        # Effect lists
        self.effects: List[VisualEffect] = []
        self.particles: List[Particle] = []
        self.floating_texts: List[FloatingText] = []
        
        # Screen shake
        self.shake_intensity = 0.0
        self.shake_duration = 0.0
        self.shake_elapsed = 0.0
        
        # Performance settings
        self.max_particles = 500
        self.max_effects = 100
        self.effects_enabled = True
        
        self.logger.info("Visual effects system initialized")
    
    def create_particle_burst(self, x: float, y: float, particle_count: int = 20, 
                            color: Tuple[int, int, int] = (255, 255, 255)):
        """Create particle burst effect"""
        if not self.effects_enabled:
            return
        
        effect = ParticleEffect(x, y, particle_count, color)
        self.add_effect(effect)
    
    def create_pulse_effect(self, x: float, y: float, max_radius: float = 50, 
                          color: Tuple[int, int, int] = (255, 255, 0)):
        """Create pulse effect"""
        if not self.effects_enabled:
            return
        
        effect = PulseEffect(x, y, max_radius, color)
        self.add_effect(effect)
    
    def create_floating_text(self, x: float, y: float, text: str, 
                           color: Tuple[int, int, int] = (255, 255, 255), 
                           font_size: int = 16, duration: float = 2.0):
        """Create floating text effect"""
        if not self.effects_enabled:
            return
        
        floating_text = FloatingText(
            x=x, y=y, text=text, color=color, 
            font_size=font_size, life=duration, max_life=duration
        )
        self.floating_texts.append(floating_text)
    
    def add_effect(self, effect: VisualEffect):
        """Add visual effect to the system"""
        if len(self.effects) < self.max_effects:
            self.effects.append(effect)
        else:
            # Remove oldest effect to make room
            self.effects.pop(0)
            self.effects.append(effect)
    
    def start_screen_shake(self, intensity: float, duration: float):
        """
        Start screen shake effect
        
        Args:
            intensity: Shake intensity (pixels)
            duration: Shake duration in seconds
        """
        self.shake_intensity = intensity
        self.shake_duration = duration
        self.shake_elapsed = 0.0
    
    def get_screen_shake_offset(self) -> Tuple[int, int]:
        """Get current screen shake offset"""
        if self.shake_elapsed >= self.shake_duration:
            return (0, 0)
        
        # Calculate shake intensity based on remaining time
        progress = self.shake_elapsed / self.shake_duration
        current_intensity = self.shake_intensity * (1.0 - progress)
        
        # Random offset
        offset_x = random.uniform(-current_intensity, current_intensity)
        offset_y = random.uniform(-current_intensity, current_intensity)
        
        return (int(offset_x), int(offset_y))
    
    def update(self, dt: float):
        """Update all visual effects"""
        if not self.effects_enabled:
            return
        
        profiler = get_profiler()
        with profiler.time_operation(ProfileCategory.SYSTEM_UPDATE, "visual_effects_update"):
            # Update screen shake
            if self.shake_elapsed < self.shake_duration:
                self.shake_elapsed += dt
            
            # Update effects
            for effect in self.effects[:]:
                effect.update(dt)
                if not effect.is_active():
                    self.effects.remove(effect)
            
            # Update floating texts
            for text in self.floating_texts[:]:
                text.update(dt)
                if not text.is_alive():
                    self.floating_texts.remove(text)
            
            # Limit particle count for performance
            if len(self.particles) > self.max_particles:
                self.particles = self.particles[-self.max_particles:]
    
    def render(self, surface: pygame.Surface, camera_x: int = 0, camera_y: int = 0):
        """Render all visual effects"""
        if not self.effects_enabled:
            return
        
        profiler = get_profiler()
        with profiler.time_operation(ProfileCategory.RENDERING, "visual_effects_render"):
            # Apply screen shake offset
            shake_x, shake_y = self.get_screen_shake_offset()
            adjusted_camera_x = camera_x + shake_x
            adjusted_camera_y = camera_y + shake_y
            
            # Render effects
            for effect in self.effects:
                effect.render(surface, adjusted_camera_x, adjusted_camera_y)
            
            # Render floating texts
            for text in self.floating_texts:
                text.render(surface, adjusted_camera_x, adjusted_camera_y)
    
    def create_action_effect(self, action: str, x: float, y: float):
        """
        Create visual effect for a specific game action
        
        Args:
            action: Action name
            x: X position
            y: Y position
        """
        effect_map = {
            "scout": {"color": (0, 255, 255), "particles": 15},
            "trade": {"color": (255, 215, 0), "particles": 20},
            "attack": {"color": (255, 0, 0), "particles": 30},
            "diplomacy": {"color": (0, 255, 0), "particles": 10},
            "fortify": {"color": (128, 128, 128), "particles": 25},
            "recruit": {"color": (0, 0, 255), "particles": 15},
            "build": {"color": (165, 42, 42), "particles": 20}
        }
        
        effect_config = effect_map.get(action, {"color": (255, 255, 255), "particles": 15})
        
        # Create particle burst
        self.create_particle_burst(x, y, effect_config["particles"], effect_config["color"])
        
        # Create pulse effect for important actions
        if action in ["attack", "diplomacy", "victory"]:
            self.create_pulse_effect(x, y, 60, effect_config["color"])
    
    def create_resource_effect(self, resource_type: str, amount: int, x: float, y: float):
        """
        Create visual effect for resource changes
        
        Args:
            resource_type: Type of resource
            amount: Amount gained/lost
            x: X position
            y: Y position
        """
        color_map = {
            "food": (139, 69, 19),
            "clean_water": (0, 191, 255),
            "scrap": (169, 169, 169),
            "medicine": (255, 20, 147),
            "mgr_rounds": (255, 215, 0)
        }
        
        color = color_map.get(resource_type, (255, 255, 255))
        text = f"+{amount}" if amount > 0 else str(amount)
        
        self.create_floating_text(x, y, text, color, 14, 1.5)
    
    def create_combat_effect(self, x: float, y: float, damage: int):
        """Create visual effect for combat"""
        # Explosion effect
        self.create_particle_burst(x, y, 40, (255, 100, 0))
        
        # Screen shake for impact
        self.start_screen_shake(5.0, 0.3)
        
        # Damage text
        if damage > 0:
            self.create_floating_text(x, y - 20, f"-{damage}", (255, 0, 0), 18, 2.0)
    
    def create_victory_effect(self, x: float, y: float):
        """Create celebration effect for victory"""
        # Multiple particle bursts
        colors = [(255, 215, 0), (255, 255, 0), (255, 165, 0)]
        for i, color in enumerate(colors):
            offset_x = x + (i - 1) * 20
            self.create_particle_burst(offset_x, y, 50, color)
        
        # Large pulse
        self.create_pulse_effect(x, y, 100, (255, 215, 0))
        
        # Victory text
        self.create_floating_text(x, y - 50, "VICTORY!", (255, 215, 0), 24, 3.0)
    
    def clear_all_effects(self):
        """Clear all active effects"""
        self.effects.clear()
        self.particles.clear()
        self.floating_texts.clear()
        self.shake_intensity = 0.0
        self.shake_duration = 0.0
        self.shake_elapsed = 0.0
    
    def set_effects_enabled(self, enabled: bool):
        """Enable or disable visual effects"""
        self.effects_enabled = enabled
        if not enabled:
            self.clear_all_effects()
    
    def get_effects_info(self) -> Dict[str, Any]:
        """Get visual effects system information"""
        return {
            "enabled": self.effects_enabled,
            "active_effects": len(self.effects),
            "floating_texts": len(self.floating_texts),
            "screen_shake_active": self.shake_elapsed < self.shake_duration,
            "max_effects": self.max_effects,
            "max_particles": self.max_particles
        }