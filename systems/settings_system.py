"""
Settings and Configuration Management System
Handles game settings, user preferences, and configuration persistence
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum


class GraphicsQuality(Enum):
    """Graphics quality settings"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class AudioQuality(Enum):
    """Audio quality settings"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Difficulty(Enum):
    """Game difficulty levels"""
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    NIGHTMARE = "nightmare"


@dataclass
class GraphicsSettings:
    """Graphics configuration settings"""
    quality: GraphicsQuality = GraphicsQuality.MEDIUM
    fullscreen: bool = False
    vsync: bool = True
    fps_limit: int = 60
    resolution_width: int = 1024
    resolution_height: int = 768
    ui_scale: float = 1.0
    show_fps: bool = False
    particle_effects: bool = True
    screen_shake: bool = True


@dataclass
class AudioSettings:
    """Audio configuration settings"""
    master_volume: float = 0.8
    music_volume: float = 0.7
    sfx_volume: float = 0.8
    ui_volume: float = 0.6
    quality: AudioQuality = AudioQuality.MEDIUM
    mute_when_unfocused: bool = True


@dataclass
class GameplaySettings:
    """Gameplay configuration settings"""
    difficulty: Difficulty = Difficulty.NORMAL
    auto_save_frequency: int = 5  # turns
    auto_save_enabled: bool = True
    pause_on_events: bool = True
    show_tooltips: bool = True
    animation_speed: float = 1.0
    confirm_destructive_actions: bool = True
    auto_end_turn: bool = False
    show_resource_warnings: bool = True
    tutorial_enabled: bool = True


@dataclass
class ControlSettings:
    """Control and input settings"""
    mouse_sensitivity: float = 1.0
    scroll_speed: float = 1.0
    edge_scrolling: bool = True
    invert_zoom: bool = False
    double_click_speed: int = 500  # milliseconds
    
    # Keyboard shortcuts (key codes or names)
    key_end_turn: str = "SPACE"
    key_quick_save: str = "F5"
    key_quick_load: str = "F9"
    key_pause: str = "PAUSE"
    key_screenshot: str = "F12"
    key_toggle_hud: str = "H"
    key_toggle_messages: str = "M"
    key_toggle_legend: str = "L"


@dataclass
class UISettings:
    """User interface settings"""
    hud_opacity: float = 0.8
    message_duration: float = 5.0
    show_station_names: bool = True
    show_faction_colors: bool = True
    compact_ui: bool = False
    font_size: int = 12
    color_blind_mode: bool = False
    high_contrast: bool = False


@dataclass
class GameSettings:
    """Complete game settings configuration"""
    graphics: GraphicsSettings = None
    audio: AudioSettings = None
    gameplay: GameplaySettings = None
    controls: ControlSettings = None
    ui: UISettings = None
    
    def __post_init__(self):
        if self.graphics is None:
            self.graphics = GraphicsSettings()
        if self.audio is None:
            self.audio = AudioSettings()
        if self.gameplay is None:
            self.gameplay = GameplaySettings()
        if self.controls is None:
            self.controls = ControlSettings()
        if self.ui is None:
            self.ui = UISettings()


class SettingsSystem:
    """
    Settings and configuration management system
    
    Features:
    - Settings system for graphics, audio, and gameplay options
    - Configuration file management with JSON persistence
    - Settings validation and default value handling
    - Hot-reloading of settings during gameplay
    - Settings categories and organization
    """
    
    def __init__(self, settings_file: str = "settings.json"):
        """
        Initialize settings system
        
        Args:
            settings_file: Path to settings file
        """
        self.logger = logging.getLogger(__name__)
        self.settings_file = Path(settings_file)
        self.settings_directory = self.settings_file.parent
        self.settings_directory.mkdir(exist_ok=True)
        
        # Current settings
        self.settings = GameSettings()
        
        # Settings change callbacks
        self.change_callbacks: Dict[str, list] = {}
        
        # Load settings from file
        self.load_settings()
        
        self.logger.info(f"Settings system initialized with file: {self.settings_file}")
    
    def load_settings(self) -> Dict[str, Any]:
        """
        Load settings from file
        
        Returns:
            Result dictionary with success status and message
        """
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings_data = json.load(f)
                
                # Reconstruct settings from data
                self.settings = self._deserialize_settings(settings_data)
                
                self.logger.info("Settings loaded successfully")
                return {
                    "success": True,
                    "message": "Settings loaded successfully"
                }
            else:
                # Create default settings file
                self.save_settings()
                self.logger.info("Created default settings file")
                return {
                    "success": True,
                    "message": "Created default settings"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            # Use default settings on error
            self.settings = GameSettings()
            return {
                "success": False,
                "message": f"Failed to load settings: {str(e)}",
                "error": str(e)
            }
    
    def save_settings(self) -> Dict[str, Any]:
        """
        Save current settings to file
        
        Returns:
            Result dictionary with success status and message
        """
        try:
            settings_data = self._serialize_settings(self.settings)
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings_data, f, indent=2)
            
            self.logger.info("Settings saved successfully")
            return {
                "success": True,
                "message": "Settings saved successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            return {
                "success": False,
                "message": f"Failed to save settings: {str(e)}",
                "error": str(e)
            }
    
    def get_setting(self, category: str, setting_name: str) -> Any:
        """
        Get a specific setting value
        
        Args:
            category: Settings category (graphics, audio, gameplay, controls, ui)
            setting_name: Name of the setting
            
        Returns:
            Setting value or None if not found
        """
        try:
            category_obj = getattr(self.settings, category)
            return getattr(category_obj, setting_name)
        except AttributeError:
            self.logger.warning(f"Setting not found: {category}.{setting_name}")
            return None
    
    def set_setting(self, category: str, setting_name: str, value: Any) -> Dict[str, Any]:
        """
        Set a specific setting value
        
        Args:
            category: Settings category
            setting_name: Name of the setting
            value: New value for the setting
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            category_obj = getattr(self.settings, category)
            old_value = getattr(category_obj, setting_name)
            
            # Validate and convert value if needed
            validated_value = self._validate_setting_value(category, setting_name, value)
            
            setattr(category_obj, setting_name, validated_value)
            
            # Trigger change callbacks
            self._trigger_setting_change(category, setting_name, old_value, validated_value)
            
            self.logger.debug(f"Setting changed: {category}.{setting_name} = {validated_value}")
            return {
                "success": True,
                "message": f"Setting {category}.{setting_name} updated",
                "old_value": old_value,
                "new_value": validated_value
            }
            
        except AttributeError:
            return {
                "success": False,
                "message": f"Setting not found: {category}.{setting_name}"
            }
        except ValueError as e:
            return {
                "success": False,
                "message": f"Invalid value for {category}.{setting_name}: {str(e)}"
            }
        except Exception as e:
            self.logger.error(f"Failed to set setting: {e}")
            return {
                "success": False,
                "message": f"Failed to set setting: {str(e)}",
                "error": str(e)
            }
    
    def reset_to_defaults(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Reset settings to default values
        
        Args:
            category: Specific category to reset, or None for all
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            if category:
                # Reset specific category
                if category == "graphics":
                    self.settings.graphics = GraphicsSettings()
                elif category == "audio":
                    self.settings.audio = AudioSettings()
                elif category == "gameplay":
                    self.settings.gameplay = GameplaySettings()
                elif category == "controls":
                    self.settings.controls = ControlSettings()
                elif category == "ui":
                    self.settings.ui = UISettings()
                else:
                    return {
                        "success": False,
                        "message": f"Unknown category: {category}"
                    }
                
                message = f"Reset {category} settings to defaults"
            else:
                # Reset all settings
                self.settings = GameSettings()
                message = "Reset all settings to defaults"
            
            # Save the reset settings
            self.save_settings()
            
            self.logger.info(message)
            return {
                "success": True,
                "message": message
            }
            
        except Exception as e:
            self.logger.error(f"Failed to reset settings: {e}")
            return {
                "success": False,
                "message": f"Failed to reset settings: {str(e)}",
                "error": str(e)
            }
    
    def register_change_callback(self, category: str, setting_name: str, callback):
        """
        Register a callback for when a setting changes
        
        Args:
            category: Settings category
            setting_name: Name of the setting
            callback: Function to call when setting changes
        """
        key = f"{category}.{setting_name}"
        if key not in self.change_callbacks:
            self.change_callbacks[key] = []
        self.change_callbacks[key].append(callback)
    
    def get_settings_summary(self) -> Dict[str, Any]:
        """Get a summary of current settings"""
        return {
            "graphics": {
                "quality": self.settings.graphics.quality.value,
                "fullscreen": self.settings.graphics.fullscreen,
                "resolution": f"{self.settings.graphics.resolution_width}x{self.settings.graphics.resolution_height}",
                "fps_limit": self.settings.graphics.fps_limit
            },
            "audio": {
                "master_volume": self.settings.audio.master_volume,
                "music_volume": self.settings.audio.music_volume,
                "quality": self.settings.audio.quality.value
            },
            "gameplay": {
                "difficulty": self.settings.gameplay.difficulty.value,
                "auto_save": self.settings.gameplay.auto_save_enabled,
                "auto_save_frequency": self.settings.gameplay.auto_save_frequency
            }
        }
    
    def _serialize_settings(self, settings: GameSettings) -> Dict[str, Any]:
        """Serialize settings to dictionary"""
        return {
            "graphics": {
                "quality": settings.graphics.quality.value,
                "fullscreen": settings.graphics.fullscreen,
                "vsync": settings.graphics.vsync,
                "fps_limit": settings.graphics.fps_limit,
                "resolution_width": settings.graphics.resolution_width,
                "resolution_height": settings.graphics.resolution_height,
                "ui_scale": settings.graphics.ui_scale,
                "show_fps": settings.graphics.show_fps,
                "particle_effects": settings.graphics.particle_effects,
                "screen_shake": settings.graphics.screen_shake
            },
            "audio": {
                "master_volume": settings.audio.master_volume,
                "music_volume": settings.audio.music_volume,
                "sfx_volume": settings.audio.sfx_volume,
                "ui_volume": settings.audio.ui_volume,
                "quality": settings.audio.quality.value,
                "mute_when_unfocused": settings.audio.mute_when_unfocused
            },
            "gameplay": {
                "difficulty": settings.gameplay.difficulty.value,
                "auto_save_frequency": settings.gameplay.auto_save_frequency,
                "auto_save_enabled": settings.gameplay.auto_save_enabled,
                "pause_on_events": settings.gameplay.pause_on_events,
                "show_tooltips": settings.gameplay.show_tooltips,
                "animation_speed": settings.gameplay.animation_speed,
                "confirm_destructive_actions": settings.gameplay.confirm_destructive_actions,
                "auto_end_turn": settings.gameplay.auto_end_turn,
                "show_resource_warnings": settings.gameplay.show_resource_warnings,
                "tutorial_enabled": settings.gameplay.tutorial_enabled
            },
            "controls": {
                "mouse_sensitivity": settings.controls.mouse_sensitivity,
                "scroll_speed": settings.controls.scroll_speed,
                "edge_scrolling": settings.controls.edge_scrolling,
                "invert_zoom": settings.controls.invert_zoom,
                "double_click_speed": settings.controls.double_click_speed,
                "key_end_turn": settings.controls.key_end_turn,
                "key_quick_save": settings.controls.key_quick_save,
                "key_quick_load": settings.controls.key_quick_load,
                "key_pause": settings.controls.key_pause,
                "key_screenshot": settings.controls.key_screenshot,
                "key_toggle_hud": settings.controls.key_toggle_hud,
                "key_toggle_messages": settings.controls.key_toggle_messages,
                "key_toggle_legend": settings.controls.key_toggle_legend
            },
            "ui": {
                "hud_opacity": settings.ui.hud_opacity,
                "message_duration": settings.ui.message_duration,
                "show_station_names": settings.ui.show_station_names,
                "show_faction_colors": settings.ui.show_faction_colors,
                "compact_ui": settings.ui.compact_ui,
                "font_size": settings.ui.font_size,
                "color_blind_mode": settings.ui.color_blind_mode,
                "high_contrast": settings.ui.high_contrast
            }
        }
    
    def _deserialize_settings(self, data: Dict[str, Any]) -> GameSettings:
        """Deserialize settings from dictionary"""
        settings = GameSettings()
        
        # Graphics settings
        if "graphics" in data:
            g = data["graphics"]
            settings.graphics = GraphicsSettings(
                quality=GraphicsQuality(g.get("quality", "medium")),
                fullscreen=g.get("fullscreen", False),
                vsync=g.get("vsync", True),
                fps_limit=g.get("fps_limit", 60),
                resolution_width=g.get("resolution_width", 1024),
                resolution_height=g.get("resolution_height", 768),
                ui_scale=g.get("ui_scale", 1.0),
                show_fps=g.get("show_fps", False),
                particle_effects=g.get("particle_effects", True),
                screen_shake=g.get("screen_shake", True)
            )
        
        # Audio settings
        if "audio" in data:
            a = data["audio"]
            settings.audio = AudioSettings(
                master_volume=a.get("master_volume", 0.8),
                music_volume=a.get("music_volume", 0.7),
                sfx_volume=a.get("sfx_volume", 0.8),
                ui_volume=a.get("ui_volume", 0.6),
                quality=AudioQuality(a.get("quality", "medium")),
                mute_when_unfocused=a.get("mute_when_unfocused", True)
            )
        
        # Gameplay settings
        if "gameplay" in data:
            gp = data["gameplay"]
            settings.gameplay = GameplaySettings(
                difficulty=Difficulty(gp.get("difficulty", "normal")),
                auto_save_frequency=gp.get("auto_save_frequency", 5),
                auto_save_enabled=gp.get("auto_save_enabled", True),
                pause_on_events=gp.get("pause_on_events", True),
                show_tooltips=gp.get("show_tooltips", True),
                animation_speed=gp.get("animation_speed", 1.0),
                confirm_destructive_actions=gp.get("confirm_destructive_actions", True),
                auto_end_turn=gp.get("auto_end_turn", False),
                show_resource_warnings=gp.get("show_resource_warnings", True),
                tutorial_enabled=gp.get("tutorial_enabled", True)
            )
        
        # Control settings
        if "controls" in data:
            c = data["controls"]
            settings.controls = ControlSettings(
                mouse_sensitivity=c.get("mouse_sensitivity", 1.0),
                scroll_speed=c.get("scroll_speed", 1.0),
                edge_scrolling=c.get("edge_scrolling", True),
                invert_zoom=c.get("invert_zoom", False),
                double_click_speed=c.get("double_click_speed", 500),
                key_end_turn=c.get("key_end_turn", "SPACE"),
                key_quick_save=c.get("key_quick_save", "F5"),
                key_quick_load=c.get("key_quick_load", "F9"),
                key_pause=c.get("key_pause", "PAUSE"),
                key_screenshot=c.get("key_screenshot", "F12"),
                key_toggle_hud=c.get("key_toggle_hud", "H"),
                key_toggle_messages=c.get("key_toggle_messages", "M"),
                key_toggle_legend=c.get("key_toggle_legend", "L")
            )
        
        # UI settings
        if "ui" in data:
            u = data["ui"]
            settings.ui = UISettings(
                hud_opacity=u.get("hud_opacity", 0.8),
                message_duration=u.get("message_duration", 5.0),
                show_station_names=u.get("show_station_names", True),
                show_faction_colors=u.get("show_faction_colors", True),
                compact_ui=u.get("compact_ui", False),
                font_size=u.get("font_size", 12),
                color_blind_mode=u.get("color_blind_mode", False),
                high_contrast=u.get("high_contrast", False)
            )
        
        return settings
    
    def _validate_setting_value(self, category: str, setting_name: str, value: Any) -> Any:
        """Validate and convert setting value"""
        # Get the expected type from the current setting
        current_value = self.get_setting(category, setting_name)
        
        if current_value is None:
            raise ValueError(f"Unknown setting: {category}.{setting_name}")
        
        # Type validation and conversion
        if isinstance(current_value, bool):
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)
        
        elif isinstance(current_value, int):
            return int(value)
        
        elif isinstance(current_value, float):
            return float(value)
        
        elif isinstance(current_value, str):
            return str(value)
        
        elif isinstance(current_value, Enum):
            if isinstance(value, str):
                # Try to create enum from string value
                enum_class = type(current_value)
                return enum_class(value)
            return value
        
        return value
    
    def _trigger_setting_change(self, category: str, setting_name: str, old_value: Any, new_value: Any):
        """Trigger callbacks for setting changes"""
        key = f"{category}.{setting_name}"
        if key in self.change_callbacks:
            for callback in self.change_callbacks[key]:
                try:
                    callback(category, setting_name, old_value, new_value)
                except Exception as e:
                    self.logger.error(f"Error in setting change callback: {e}")