"""
Rendering Optimization System
Optimizes rendering performance through batching, caching, and culling
"""

import pygame
import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from enum import Enum

from utils.performance_profiler import get_profiler, ProfileCategory


class RenderLayer(Enum):
    """Rendering layers for depth sorting"""
    BACKGROUND = 0
    MAP_BASE = 1
    TUNNELS = 2
    STATIONS = 3
    UNITS = 4
    EFFECTS = 5
    UI_BACKGROUND = 6
    UI_ELEMENTS = 7
    UI_OVERLAY = 8
    DEBUG = 9


@dataclass
class RenderCommand:
    """Individual rendering command"""
    layer: RenderLayer
    position: Tuple[int, int]
    surface: pygame.Surface
    rect: pygame.Rect
    alpha: int = 255
    blend_mode: int = 0


class SurfaceCache:
    """Cache for pre-rendered surfaces to reduce redundant drawing"""
    
    def __init__(self, max_size: int = 100):
        """
        Initialize surface cache
        
        Args:
            max_size: Maximum number of surfaces to cache
        """
        self.cache: Dict[str, pygame.Surface] = {}
        self.access_order: List[str] = []
        self.max_size = max_size
        self.logger = logging.getLogger(__name__)
    
    def get(self, key: str) -> Optional[pygame.Surface]:
        """Get cached surface"""
        if key in self.cache:
            # Move to end of access order (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, surface: pygame.Surface):
        """Cache a surface"""
        if key in self.cache:
            # Update existing entry
            self.cache[key] = surface
            self.access_order.remove(key)
            self.access_order.append(key)
        else:
            # Add new entry
            if len(self.cache) >= self.max_size:
                # Remove least recently used
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]
            
            self.cache[key] = surface
            self.access_order.append(key)
    
    def clear(self):
        """Clear all cached surfaces"""
        self.cache.clear()
        self.access_order.clear()
        self.logger.debug("Surface cache cleared")
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "cached_surfaces": len(self.cache),
            "max_size": self.max_size,
            "memory_usage": sum(s.get_size()[0] * s.get_size()[1] * s.get_bitsize() // 8 
                              for s in self.cache.values())
        }


class RenderBatch:
    """Batch similar rendering operations for efficiency"""
    
    def __init__(self):
        """Initialize render batch"""
        self.commands: List[RenderCommand] = []
        self.dirty = True
        self.cached_surface: Optional[pygame.Surface] = None
        self.cached_rect: Optional[pygame.Rect] = None
    
    def add_command(self, command: RenderCommand):
        """Add a render command to the batch"""
        self.commands.append(command)
        self.dirty = True
    
    def clear(self):
        """Clear all commands"""
        self.commands.clear()
        self.dirty = True
        self.cached_surface = None
        self.cached_rect = None
    
    def render(self, target_surface: pygame.Surface, camera_rect: pygame.Rect):
        """Render all commands in the batch"""
        if not self.commands:
            return
        
        # Sort commands by layer
        self.commands.sort(key=lambda cmd: cmd.layer.value)
        
        # Render each command
        for command in self.commands:
            # Frustum culling - skip if outside camera view
            if not camera_rect.colliderect(command.rect):
                continue
            
            # Apply alpha blending if needed
            if command.alpha < 255:
                command.surface.set_alpha(command.alpha)
            
            # Render to target
            target_surface.blit(command.surface, command.position, blend_flags=command.blend_mode)


class RenderOptimizer:
    """
    Rendering optimization system
    
    Features:
    - Render command batching and sorting
    - Surface caching for static elements
    - Frustum culling for off-screen objects
    - Dirty rectangle tracking for partial updates
    - Level-of-detail (LOD) rendering
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        """
        Initialize render optimizer
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.logger = logging.getLogger(__name__)
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Rendering state
        self.render_batches: Dict[RenderLayer, RenderBatch] = {
            layer: RenderBatch() for layer in RenderLayer
        }
        
        # Surface caching
        self.surface_cache = SurfaceCache(max_size=200)
        
        # Dirty rectangle tracking
        self.dirty_rects: List[pygame.Rect] = []
        self.full_redraw = True
        
        # Camera/viewport
        self.camera_x = 0
        self.camera_y = 0
        self.camera_zoom = 1.0
        
        # Performance settings
        self.enable_frustum_culling = True
        self.enable_surface_caching = True
        self.enable_dirty_rect_tracking = True
        self.enable_lod_rendering = True
        
        # LOD thresholds
        self.lod_distance_thresholds = {
            "high": 200,    # Full detail within 200 pixels
            "medium": 500,  # Medium detail within 500 pixels
            "low": 1000     # Low detail within 1000 pixels
        }
        
        self.logger.info("Render optimizer initialized")
    
    def set_camera(self, x: int, y: int, zoom: float = 1.0):
        """Set camera position and zoom"""
        if self.camera_x != x or self.camera_y != y or self.camera_zoom != zoom:
            self.camera_x = x
            self.camera_y = y
            self.camera_zoom = zoom
            self.full_redraw = True
    
    def get_camera_rect(self) -> pygame.Rect:
        """Get camera viewport rectangle"""
        width = int(self.screen_width / self.camera_zoom)
        height = int(self.screen_height / self.camera_zoom)
        return pygame.Rect(self.camera_x, self.camera_y, width, height)
    
    def world_to_screen(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates"""
        screen_x = int((world_x - self.camera_x) * self.camera_zoom)
        screen_y = int((world_y - self.camera_y) * self.camera_zoom)
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """Convert screen coordinates to world coordinates"""
        world_x = int(screen_x / self.camera_zoom + self.camera_x)
        world_y = int(screen_y / self.camera_zoom + self.camera_y)
        return world_x, world_y
    
    def add_render_command(self, layer: RenderLayer, position: Tuple[int, int], 
                          surface: pygame.Surface, alpha: int = 255, blend_mode: int = 0):
        """
        Add a rendering command
        
        Args:
            layer: Rendering layer
            position: World position
            surface: Surface to render
            alpha: Alpha transparency (0-255)
            blend_mode: Pygame blend mode
        """
        profiler = get_profiler()
        with profiler.time_operation(ProfileCategory.RENDERING, "add_render_command"):
            # Convert to screen coordinates
            screen_pos = self.world_to_screen(position[0], position[1])
            
            # Create render command
            command = RenderCommand(
                layer=layer,
                position=screen_pos,
                surface=surface,
                rect=pygame.Rect(screen_pos[0], screen_pos[1], surface.get_width(), surface.get_height()),
                alpha=alpha,
                blend_mode=blend_mode
            )
            
            # Add to appropriate batch
            self.render_batches[layer].add_command(command)
            
            # Mark area as dirty
            if self.enable_dirty_rect_tracking:
                self.dirty_rects.append(command.rect)
    
    def get_cached_surface(self, cache_key: str) -> Optional[pygame.Surface]:
        """Get a cached surface"""
        if self.enable_surface_caching:
            return self.surface_cache.get(cache_key)
        return None
    
    def cache_surface(self, cache_key: str, surface: pygame.Surface):
        """Cache a surface for reuse"""
        if self.enable_surface_caching:
            self.surface_cache.put(cache_key, surface)
    
    def create_station_surface(self, station_name: str, faction_color: Tuple[int, int, int], 
                             size: int, selected: bool = False) -> pygame.Surface:
        """Create optimized station rendering surface"""
        cache_key = f"station_{station_name}_{faction_color}_{size}_{selected}"
        
        # Check cache first
        cached = self.get_cached_surface(cache_key)
        if cached:
            return cached
        
        # Create new surface
        surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        
        # Draw station circle
        pygame.draw.circle(surface, faction_color, (size, size), size)
        
        # Draw selection indicator
        if selected:
            pygame.draw.circle(surface, (255, 255, 255), (size, size), size + 2, 2)
        
        # Draw border
        pygame.draw.circle(surface, (0, 0, 0), (size, size), size, 2)
        
        # Cache the surface
        self.cache_surface(cache_key, surface)
        
        return surface
    
    def create_tunnel_surface(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                            condition: str, width: int = 3) -> pygame.Surface:
        """Create optimized tunnel rendering surface"""
        # Calculate tunnel dimensions
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = int((dx * dx + dy * dy) ** 0.5)
        
        cache_key = f"tunnel_{length}_{condition}_{width}"
        
        # Check cache first
        cached = self.get_cached_surface(cache_key)
        if cached:
            return cached
        
        # Create surface
        surface = pygame.Surface((length + width * 2, width * 2), pygame.SRCALPHA)
        
        # Choose color based on condition
        color_map = {
            "clear": (100, 100, 100),
            "hazardous": (150, 150, 50),
            "infested": (150, 50, 50),
            "collapsed": (50, 50, 50)
        }
        color = color_map.get(condition, (100, 100, 100))
        
        # Draw tunnel line
        pygame.draw.line(surface, color, (width, width), (length + width, width), width)
        
        # Cache the surface
        self.cache_surface(cache_key, surface)
        
        return surface
    
    def get_lod_level(self, distance: float) -> str:
        """Get level of detail based on distance from camera"""
        if not self.enable_lod_rendering:
            return "high"
        
        if distance <= self.lod_distance_thresholds["high"]:
            return "high"
        elif distance <= self.lod_distance_thresholds["medium"]:
            return "medium"
        else:
            return "low"
    
    def calculate_distance_to_camera(self, world_pos: Tuple[int, int]) -> float:
        """Calculate distance from world position to camera center"""
        camera_center_x = self.camera_x + (self.screen_width // 2) / self.camera_zoom
        camera_center_y = self.camera_y + (self.screen_height // 2) / self.camera_zoom
        
        dx = world_pos[0] - camera_center_x
        dy = world_pos[1] - camera_center_y
        
        return (dx * dx + dy * dy) ** 0.5
    
    def render_frame(self, target_surface: pygame.Surface):
        """Render complete frame with optimizations"""
        profiler = get_profiler()
        
        with profiler.time_operation(ProfileCategory.RENDERING, "render_frame"):
            camera_rect = self.get_camera_rect()
            
            # Clear target if full redraw
            if self.full_redraw:
                target_surface.fill((0, 0, 0))
            
            # Render each layer in order
            for layer in RenderLayer:
                batch = self.render_batches[layer]
                if batch.commands:
                    with profiler.time_operation(ProfileCategory.RENDERING, f"render_layer_{layer.value}"):
                        batch.render(target_surface, camera_rect)
            
            # Reset state for next frame
            self.clear_render_commands()
            self.full_redraw = False
            self.dirty_rects.clear()
    
    def clear_render_commands(self):
        """Clear all render commands"""
        for batch in self.render_batches.values():
            batch.clear()
    
    def force_full_redraw(self):
        """Force a full redraw on next frame"""
        self.full_redraw = True
        self.surface_cache.clear()
    
    def optimize_for_performance(self, target_fps: int = 30):
        """Automatically adjust settings for target performance"""
        profiler = get_profiler()
        current_fps = profiler.get_current_fps()
        
        if current_fps < target_fps * 0.8:  # Performance is below 80% of target
            # Reduce quality settings
            if self.enable_lod_rendering:
                # Increase LOD thresholds (reduce detail distance)
                self.lod_distance_thresholds["high"] = max(100, self.lod_distance_thresholds["high"] - 50)
                self.lod_distance_thresholds["medium"] = max(200, self.lod_distance_thresholds["medium"] - 100)
            
            # Reduce cache size to save memory
            if self.surface_cache.max_size > 50:
                self.surface_cache.max_size = max(50, self.surface_cache.max_size - 25)
            
            self.logger.info(f"Reduced rendering quality for performance (FPS: {current_fps:.1f})")
        
        elif current_fps > target_fps * 1.2:  # Performance is above 120% of target
            # Increase quality settings
            if self.enable_lod_rendering:
                # Decrease LOD thresholds (increase detail distance)
                self.lod_distance_thresholds["high"] = min(300, self.lod_distance_thresholds["high"] + 25)
                self.lod_distance_thresholds["medium"] = min(600, self.lod_distance_thresholds["medium"] + 50)
            
            # Increase cache size
            if self.surface_cache.max_size < 200:
                self.surface_cache.max_size = min(200, self.surface_cache.max_size + 25)
            
            self.logger.debug(f"Increased rendering quality (FPS: {current_fps:.1f})")
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get rendering optimization statistics"""
        total_commands = sum(len(batch.commands) for batch in self.render_batches.values())
        
        return {
            "total_render_commands": total_commands,
            "render_batches": len(self.render_batches),
            "surface_cache": self.surface_cache.get_stats(),
            "dirty_rects": len(self.dirty_rects),
            "camera_position": (self.camera_x, self.camera_y),
            "camera_zoom": self.camera_zoom,
            "lod_thresholds": self.lod_distance_thresholds.copy(),
            "optimizations_enabled": {
                "frustum_culling": self.enable_frustum_culling,
                "surface_caching": self.enable_surface_caching,
                "dirty_rect_tracking": self.enable_dirty_rect_tracking,
                "lod_rendering": self.enable_lod_rendering
            }
        }