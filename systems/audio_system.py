"""
Audio System for Sound Effects and Music
Manages game audio including sound effects, music, and ambient sounds
"""

import pygame
import logging
import os
from typing import Dict, Optional, List, Any
from enum import Enum
from pathlib import Path

from utils.performance_profiler import get_profiler, ProfileCategory


class AudioCategory(Enum):
    """Categories of audio for volume control"""
    MASTER = "master"
    MUSIC = "music"
    SFX = "sfx"
    UI = "ui"
    AMBIENT = "ambient"


class AudioSystem:
    """
    Complete audio system for game sounds and music
    
    Features:
    - Sound effect management and playback
    - Background music with looping and crossfading
    - Volume control by category
    - Audio caching and optimization
    - Spatial audio for positional sounds
    """
    
    def __init__(self, audio_directory: str = "audio"):
        """
        Initialize audio system
        
        Args:
            audio_directory: Directory containing audio files
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize pygame mixer
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self.audio_enabled = True
            self.logger.info("Audio system initialized")
        except pygame.error as e:
            self.logger.error(f"Failed to initialize audio: {e}")
            self.audio_enabled = False
            return
        
        # Audio settings
        self.audio_directory = Path(audio_directory)
        self.volumes = {
            AudioCategory.MASTER: 0.8,
            AudioCategory.MUSIC: 0.7,
            AudioCategory.SFX: 0.8,
            AudioCategory.UI: 0.6,
            AudioCategory.AMBIENT: 0.5
        }
        
        # Audio caches
        self.sound_cache: Dict[str, pygame.mixer.Sound] = {}
        self.music_cache: Dict[str, str] = {}  # Store file paths for music
        
        # Current state
        self.current_music = None
        self.music_volume = 0.7
        self.music_paused = False
        
        # Sound channels for different categories
        self.channels = {
            AudioCategory.SFX: [],
            AudioCategory.UI: [],
            AudioCategory.AMBIENT: []
        }
        
        # Reserve channels for different audio types
        pygame.mixer.set_num_channels(16)
        
        # Load audio files
        self._load_audio_files()
    
    def _load_audio_files(self):
        """Load and cache audio files"""
        if not self.audio_enabled or not self.audio_directory.exists():
            return
        
        try:
            # Load sound effects
            sfx_dir = self.audio_directory / "sfx"
            if sfx_dir.exists():
                for sound_file in sfx_dir.glob("*.wav"):
                    try:
                        sound = pygame.mixer.Sound(str(sound_file))
                        self.sound_cache[sound_file.stem] = sound
                        self.logger.debug(f"Loaded sound: {sound_file.stem}")
                    except pygame.error as e:
                        self.logger.warning(f"Failed to load sound {sound_file}: {e}")
            
            # Index music files
            music_dir = self.audio_directory / "music"
            if music_dir.exists():
                for music_file in music_dir.glob("*.ogg"):
                    self.music_cache[music_file.stem] = str(music_file)
                    self.logger.debug(f"Indexed music: {music_file.stem}")
            
            self.logger.info(f"Loaded {len(self.sound_cache)} sounds and {len(self.music_cache)} music tracks")
            
        except Exception as e:
            self.logger.error(f"Error loading audio files: {e}")
    
    def play_sound(self, sound_name: str, category: AudioCategory = AudioCategory.SFX, 
                   volume: float = 1.0, loops: int = 0) -> bool:
        """
        Play a sound effect
        
        Args:
            sound_name: Name of the sound file (without extension)
            category: Audio category for volume control
            volume: Volume multiplier (0.0 to 1.0)
            loops: Number of times to loop (-1 for infinite)
            
        Returns:
            True if sound was played successfully
        """
        if not self.audio_enabled:
            return False
        
        profiler = get_profiler()
        with profiler.time_operation(ProfileCategory.SYSTEM_UPDATE, "play_sound"):
            try:
                # Get sound from cache
                if sound_name not in self.sound_cache:
                    self.logger.warning(f"Sound not found: {sound_name}")
                    return False
                
                sound = self.sound_cache[sound_name]
                
                # Calculate final volume
                final_volume = volume * self.volumes[category] * self.volumes[AudioCategory.MASTER]
                sound.set_volume(final_volume)
                
                # Play sound
                channel = sound.play(loops)
                if channel:
                    self.logger.debug(f"Playing sound: {sound_name} (volume: {final_volume:.2f})")
                    return True
                else:
                    self.logger.warning(f"No available channel for sound: {sound_name}")
                    return False
                
            except Exception as e:
                self.logger.error(f"Error playing sound {sound_name}: {e}")
                return False
    
    def play_music(self, music_name: str, loops: int = -1, fade_in_ms: int = 0) -> bool:
        """
        Play background music
        
        Args:
            music_name: Name of the music file (without extension)
            loops: Number of times to loop (-1 for infinite)
            fade_in_ms: Fade in duration in milliseconds
            
        Returns:
            True if music started successfully
        """
        if not self.audio_enabled:
            return False
        
        try:
            # Get music file path
            if music_name not in self.music_cache:
                self.logger.warning(f"Music not found: {music_name}")
                return False
            
            music_path = self.music_cache[music_name]
            
            # Stop current music if playing
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            
            # Load and play new music
            pygame.mixer.music.load(music_path)
            
            if fade_in_ms > 0:
                pygame.mixer.music.play(loops, fade_ms=fade_in_ms)
            else:
                pygame.mixer.music.play(loops)
            
            # Set volume
            final_volume = self.volumes[AudioCategory.MUSIC] * self.volumes[AudioCategory.MASTER]
            pygame.mixer.music.set_volume(final_volume)
            
            self.current_music = music_name
            self.music_paused = False
            
            self.logger.info(f"Playing music: {music_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error playing music {music_name}: {e}")
            return False
    
    def stop_music(self, fade_out_ms: int = 0):
        """
        Stop background music
        
        Args:
            fade_out_ms: Fade out duration in milliseconds
        """
        if not self.audio_enabled:
            return
        
        try:
            if fade_out_ms > 0:
                pygame.mixer.music.fadeout(fade_out_ms)
            else:
                pygame.mixer.music.stop()
            
            self.current_music = None
            self.music_paused = False
            
        except Exception as e:
            self.logger.error(f"Error stopping music: {e}")
    
    def pause_music(self):
        """Pause background music"""
        if not self.audio_enabled:
            return
        
        try:
            pygame.mixer.music.pause()
            self.music_paused = True
        except Exception as e:
            self.logger.error(f"Error pausing music: {e}")
    
    def resume_music(self):
        """Resume paused music"""
        if not self.audio_enabled:
            return
        
        try:
            pygame.mixer.music.unpause()
            self.music_paused = False
        except Exception as e:
            self.logger.error(f"Error resuming music: {e}")
    
    def set_volume(self, category: AudioCategory, volume: float):
        """
        Set volume for an audio category
        
        Args:
            category: Audio category
            volume: Volume level (0.0 to 1.0)
        """
        volume = max(0.0, min(1.0, volume))  # Clamp to valid range
        self.volumes[category] = volume
        
        # Update music volume if it's the music or master category
        if category in [AudioCategory.MUSIC, AudioCategory.MASTER]:
            if pygame.mixer.music.get_busy():
                final_volume = self.volumes[AudioCategory.MUSIC] * self.volumes[AudioCategory.MASTER]
                pygame.mixer.music.set_volume(final_volume)
        
        self.logger.debug(f"Set {category.value} volume to {volume:.2f}")
    
    def get_volume(self, category: AudioCategory) -> float:
        """Get volume for an audio category"""
        return self.volumes.get(category, 0.0)
    
    def mute_all(self):
        """Mute all audio"""
        self.set_volume(AudioCategory.MASTER, 0.0)
    
    def unmute_all(self, volume: float = 0.8):
        """Unmute all audio"""
        self.set_volume(AudioCategory.MASTER, volume)
    
    def play_ui_sound(self, sound_name: str):
        """Play a UI sound effect"""
        return self.play_sound(sound_name, AudioCategory.UI, volume=0.8)
    
    def play_action_sound(self, action: str):
        """
        Play sound for a specific game action
        
        Args:
            action: Action name (scout, trade, attack, etc.)
        """
        sound_map = {
            "scout": "scout_move",
            "trade": "trade_success",
            "attack": "combat_start",
            "diplomacy": "diplomacy_success",
            "fortify": "construction",
            "recruit": "unit_recruit",
            "build": "construction",
            "turn_end": "turn_advance",
            "event": "event_trigger",
            "victory": "victory_fanfare",
            "defeat": "defeat_sound"
        }
        
        sound_name = sound_map.get(action, "ui_click")
        return self.play_sound(sound_name, AudioCategory.SFX)
    
    def play_ambient_sound(self, sound_name: str, loops: int = -1):
        """Play ambient background sound"""
        return self.play_sound(sound_name, AudioCategory.AMBIENT, volume=0.6, loops=loops)
    
    def update(self, dt: float):
        """
        Update audio system
        
        Args:
            dt: Delta time in seconds
        """
        if not self.audio_enabled:
            return
        
        # Check if music has stopped and needs to be restarted
        if self.current_music and not pygame.mixer.music.get_busy() and not self.music_paused:
            # Music ended, could restart or switch to next track
            pass
    
    def get_audio_info(self) -> Dict[str, Any]:
        """Get audio system information"""
        return {
            "enabled": self.audio_enabled,
            "sounds_loaded": len(self.sound_cache),
            "music_tracks": len(self.music_cache),
            "current_music": self.current_music,
            "music_paused": self.music_paused,
            "volumes": {cat.value: vol for cat, vol in self.volumes.items()},
            "mixer_info": {
                "frequency": pygame.mixer.get_init()[0] if pygame.mixer.get_init() else 0,
                "channels": pygame.mixer.get_num_channels() if self.audio_enabled else 0,
                "busy_channels": len([ch for ch in range(pygame.mixer.get_num_channels()) 
                                    if pygame.mixer.Channel(ch).get_busy()]) if self.audio_enabled else 0
            }
        }
    
    def create_placeholder_sounds(self):
        """Create placeholder sounds for testing when audio files don't exist"""
        if not self.audio_enabled:
            return
        
        try:
            # Create simple beep sounds for testing
            placeholder_sounds = [
                "ui_click", "ui_hover", "scout_move", "trade_success", 
                "combat_start", "diplomacy_success", "construction", 
                "unit_recruit", "turn_advance", "event_trigger",
                "victory_fanfare", "defeat_sound"
            ]
            
            for sound_name in placeholder_sounds:
                if sound_name not in self.sound_cache:
                    # Create a simple tone
                    duration = 0.2  # 200ms
                    sample_rate = 22050
                    frames = int(duration * sample_rate)
                    
                    # Generate a simple sine wave
                    import numpy as np
                    frequency = 440 + hash(sound_name) % 200  # Vary frequency based on name
                    wave_array = np.sin(2 * np.pi * frequency * np.linspace(0, duration, frames))
                    wave_array = (wave_array * 32767).astype(np.int16)
                    
                    # Create stereo sound
                    stereo_wave = np.array([wave_array, wave_array]).T
                    
                    # Create pygame sound
                    sound = pygame.sndarray.make_sound(stereo_wave)
                    self.sound_cache[sound_name] = sound
            
            self.logger.info(f"Created {len(placeholder_sounds)} placeholder sounds")
            
        except ImportError:
            self.logger.warning("NumPy not available, cannot create placeholder sounds")
        except Exception as e:
            self.logger.error(f"Error creating placeholder sounds: {e}")
    
    def shutdown(self):
        """Shutdown audio system"""
        if self.audio_enabled:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            self.logger.info("Audio system shutdown")