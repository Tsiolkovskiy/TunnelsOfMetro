"""
Save/Load System for Game State Persistence
Handles serialization and deserialization of complete game state
"""

import json
import pickle
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import asdict

from systems.metro_map import MetroMap
from systems.game_state import GameStateManager
from data.resources import ResourcePool
from data.station import Station
from data.infrastructure import Infrastructure, BuildingType
from data.military_unit import MilitaryUnit, UnitType


class SaveSystem:
    """
    Complete save/load system for game state persistence
    
    Features:
    - Save system for all game state data (map, factions, resources, relationships)
    - Load system with error handling and validation
    - Multiple save slot management
    - Compressed save files with metadata
    - Backward compatibility checking
    """
    
    def __init__(self, save_directory: str = "saves"):
        """
        Initialize save system
        
        Args:
            save_directory: Directory to store save files
        """
        self.logger = logging.getLogger(__name__)
        self.save_directory = Path(save_directory)
        self.save_directory.mkdir(exist_ok=True)
        
        # Save file format version for compatibility
        self.save_version = "1.0"
        self.max_save_slots = 10
        
        self.logger.info(f"Save system initialized with directory: {self.save_directory}")
    
    def save_game(self, game_state: GameStateManager, slot_name: str, 
                  description: str = "") -> Dict[str, Any]:
        """
        Save complete game state to file
        
        Args:
            game_state: GameStateManager instance to save
            slot_name: Name/identifier for the save slot
            description: Optional description for the save
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            # Create save data structure
            save_data = self._serialize_game_state(game_state)
            
            # Add metadata
            save_data["metadata"] = {
                "save_version": self.save_version,
                "timestamp": datetime.now().isoformat(),
                "slot_name": slot_name,
                "description": description,
                "turn": game_state.current_turn,
                "player_faction": game_state.player.faction,
                "game_phase": game_state.game_phase
            }
            
            # Generate save file path
            save_file = self.save_directory / f"{slot_name}.save"
            
            # Save to file (using pickle for complex objects, JSON for metadata)
            with open(save_file, 'wb') as f:
                pickle.dump(save_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Create human-readable metadata file
            metadata_file = self.save_directory / f"{slot_name}.meta"
            with open(metadata_file, 'w') as f:
                json.dump(save_data["metadata"], f, indent=2)
            
            self.logger.info(f"Game saved successfully to slot '{slot_name}'")
            return {
                "success": True,
                "message": f"Game saved to slot '{slot_name}'",
                "file_path": str(save_file),
                "timestamp": save_data["metadata"]["timestamp"]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to save game: {e}")
            return {
                "success": False,
                "message": f"Save failed: {str(e)}",
                "error": str(e)
            }
    
    def load_game(self, slot_name: str) -> Dict[str, Any]:
        """
        Load game state from file
        
        Args:
            slot_name: Name/identifier of the save slot to load
            
        Returns:
            Result dictionary with success status, message, and game data
        """
        try:
            save_file = self.save_directory / f"{slot_name}.save"
            
            if not save_file.exists():
                return {
                    "success": False,
                    "message": f"Save file '{slot_name}' not found"
                }
            
            # Load save data
            with open(save_file, 'rb') as f:
                save_data = pickle.load(f)
            
            # Validate save data
            validation_result = self._validate_save_data(save_data)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "message": f"Invalid save file: {validation_result['reason']}"
                }
            
            self.logger.info(f"Game loaded successfully from slot '{slot_name}'")
            return {
                "success": True,
                "message": f"Game loaded from slot '{slot_name}'",
                "save_data": save_data,
                "metadata": save_data.get("metadata", {})
            }
            
        except Exception as e:
            self.logger.error(f"Failed to load game: {e}")
            return {
                "success": False,
                "message": f"Load failed: {str(e)}",
                "error": str(e)
            }
    
    def get_save_slots(self) -> List[Dict[str, Any]]:
        """
        Get list of available save slots with metadata
        
        Returns:
            List of save slot information
        """
        save_slots = []
        
        try:
            for save_file in self.save_directory.glob("*.save"):
                slot_name = save_file.stem
                metadata_file = self.save_directory / f"{slot_name}.meta"
                
                # Load metadata
                metadata = {}
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                    except Exception as e:
                        self.logger.warning(f"Failed to load metadata for {slot_name}: {e}")
                
                # Get file stats
                file_stats = save_file.stat()
                
                save_slots.append({
                    "slot_name": slot_name,
                    "file_path": str(save_file),
                    "file_size": file_stats.st_size,
                    "modified_time": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    "metadata": metadata
                })
            
            # Sort by modification time (newest first)
            save_slots.sort(key=lambda x: x["modified_time"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to get save slots: {e}")
        
        return save_slots
    
    def delete_save(self, slot_name: str) -> Dict[str, Any]:
        """
        Delete a save file
        
        Args:
            slot_name: Name of the save slot to delete
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            save_file = self.save_directory / f"{slot_name}.save"
            metadata_file = self.save_directory / f"{slot_name}.meta"
            
            if not save_file.exists():
                return {
                    "success": False,
                    "message": f"Save file '{slot_name}' not found"
                }
            
            # Delete files
            save_file.unlink()
            if metadata_file.exists():
                metadata_file.unlink()
            
            self.logger.info(f"Save slot '{slot_name}' deleted successfully")
            return {
                "success": True,
                "message": f"Save slot '{slot_name}' deleted"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to delete save: {e}")
            return {
                "success": False,
                "message": f"Delete failed: {str(e)}",
                "error": str(e)
            }
    
    def _serialize_game_state(self, game_state: GameStateManager) -> Dict[str, Any]:
        """Serialize complete game state to dictionary"""
        return {
            # Core game state
            "current_turn": game_state.current_turn,
            "game_phase": game_state.game_phase,
            
            # Player state
            "player": {
                "faction": game_state.player.faction,
                "resources": self._serialize_resources(game_state.player.resources),
                "controlled_stations": game_state.player.controlled_stations.copy()
            },
            
            # Game statistics
            "statistics": game_state.statistics.copy(),
            
            # Metro map state
            "metro_map": self._serialize_metro_map(game_state.metro_map),
            
            # System states
            "scouting_system": self._serialize_scouting_system(game_state.scouting_system),
            "trade_system": self._serialize_trade_system(game_state.trade_system),
            "diplomacy_system": self._serialize_diplomacy_system(game_state.diplomacy_system),
            "military_manager": self._serialize_military_manager(game_state.military_manager),
            "building_system": self._serialize_building_system(game_state.building_system),
            "event_system": self._serialize_event_system(game_state.event_system),
            "victory_system": self._serialize_victory_system(game_state.victory_system),
            "ai_system": self._serialize_ai_system(game_state.ai_system)
        }
    
    def _serialize_resources(self, resources: ResourcePool) -> Dict[str, int]:
        """Serialize resource pool"""
        return {
            "food": resources.food,
            "clean_water": resources.clean_water,
            "scrap": resources.scrap,
            "medicine": resources.medicine,
            "mgr_rounds": resources.mgr_rounds
        }
    
    def _serialize_metro_map(self, metro_map: MetroMap) -> Dict[str, Any]:
        """Serialize metro map state"""
        return {
            "stations": {
                name: self._serialize_station(station)
                for name, station in metro_map.stations.items()
            },
            "tunnels": {
                tunnel_id: {
                    "station_a": tunnel.station_a,
                    "station_b": tunnel.station_b,
                    "distance": tunnel.distance,
                    "condition": tunnel.condition.value,
                    "safety_level": tunnel.safety_level,
                    "travel_cost": tunnel.travel_cost
                }
                for tunnel_id, tunnel in metro_map.tunnels.items()
            }
        }
    
    def _serialize_station(self, station: Station) -> Dict[str, Any]:
        """Serialize station state"""
        return {
            "name": station.name,
            "position": station.position,
            "controlling_faction": station.controlling_faction,
            "population": station.population,
            "morale": station.morale,
            "defensive_value": station.defensive_value,
            "resources": self._serialize_resources(station.resources),
            "infrastructure": {
                building_type.value: {
                    "level": infrastructure.level,
                    "condition": infrastructure.condition,
                    "construction_turn": infrastructure.construction_turn
                }
                for building_type, infrastructure in station.infrastructure.items()
            },
            "special_traits": station.special_traits.copy()
        }
    
    def _serialize_scouting_system(self, scouting_system) -> Dict[str, Any]:
        """Serialize scouting system state"""
        return {
            "station_intelligence": {
                station_name: {
                    "station_name": intel.station_name,
                    "level": intel.level.value,
                    "last_updated": intel.last_updated,
                    "faction": intel.faction,
                    "population": intel.population,
                    "morale": intel.morale,
                    "defensive_value": intel.defensive_value,
                    "resources": intel.resources.copy() if intel.resources else {},
                    "infrastructure": intel.infrastructure.copy() if intel.infrastructure else [],
                    "military_units": intel.military_units.copy() if intel.military_units else [],
                    "special_traits": intel.special_traits.copy() if intel.special_traits else []
                }
                for station_name, intel in scouting_system.station_intelligence.items()
            },
            "discovered_stations": list(scouting_system.discovered_stations),
            "scouting_reports": scouting_system.scouting_reports.copy()
        }
    
    def _serialize_trade_system(self, trade_system) -> Dict[str, Any]:
        """Serialize trade system state"""
        return {
            "active_caravans": {
                caravan_id: {
                    "caravan_id": caravan.caravan_id,
                    "origin": caravan.origin,
                    "destination": caravan.destination,
                    "current_position": caravan.current_position,
                    "status": caravan.status.value,
                    "estimated_arrival": caravan.estimated_arrival,
                    "cargo": caravan.cargo.copy(),
                    "security_level": caravan.security_level
                }
                for caravan_id, caravan in trade_system.active_caravans.items()
            },
            "trade_routes": {
                route_id: {
                    "route_id": route.route_id,
                    "station_a": route.station_a,
                    "station_b": route.station_b,
                    "status": route.status.value,
                    "total_trades": route.total_trades,
                    "security_level": route.security_level,
                    "established_turn": route.established_turn
                }
                for route_id, route in trade_system.trade_routes.items()
            },
            "trade_agreements": trade_system.trade_agreements.copy()
        }
    
    def _serialize_diplomacy_system(self, diplomacy_system) -> Dict[str, Any]:
        """Serialize diplomacy system state"""
        return {
            "faction_relationships": {
                faction_pair: relationship.value
                for faction_pair, relationship in diplomacy_system.faction_relationships.items()
            },
            "relationship_history": diplomacy_system.relationship_history.copy(),
            "diplomatic_agreements": diplomacy_system.diplomatic_agreements.copy()
        }
    
    def _serialize_military_manager(self, military_manager) -> Dict[str, Any]:
        """Serialize military manager state"""
        return {
            "faction": military_manager.faction,
            "units": [
                {
                    "unit_id": unit.unit_id,
                    "unit_type": unit.unit_type.value,
                    "stationed_at": unit.stationed_at,
                    "experience": unit.experience,
                    "morale": unit.morale,
                    "equipment_level": unit.equipment_level,
                    "is_active": unit.is_active,
                    "recruitment_turn": unit.recruitment_turn
                }
                for unit in military_manager.units
            ]
        }
    
    def _serialize_building_system(self, building_system) -> Dict[str, Any]:
        """Serialize building system state"""
        return {
            "construction_projects": [
                {
                    "station_name": project.station_name,
                    "building_type": project.building_type.value,
                    "start_turn": project.start_turn,
                    "completion_turn": project.completion_turn,
                    "progress": project.progress,
                    "total_cost": project.total_cost.copy()
                }
                for project in building_system.construction_projects
            ]
        }
    
    def _serialize_event_system(self, event_system) -> Dict[str, Any]:
        """Serialize event system state"""
        return {
            "active_events": event_system.active_events.copy(),
            "event_history": event_system.event_history.copy(),
            "category_modifiers": {
                category.value: modifier
                for category, modifier in event_system.category_modifiers.items()
            }
        }
    
    def _serialize_victory_system(self, victory_system) -> Dict[str, Any]:
        """Serialize victory system state"""
        return {
            "game_ended": victory_system.game_ended,
            "victory_achieved": victory_system.victory_achieved.value if victory_system.victory_achieved else None,
            "victory_turn": victory_system.victory_turn,
            "victory_score": victory_system.victory_score,
            "victory_conditions": {
                victory_type.value: {
                    "current_progress": condition.current_progress,
                    "status": condition.status.value,
                    "turn_achieved": condition.turn_achieved
                }
                for victory_type, condition in victory_system.victory_conditions.items()
            },
            "progress_history": victory_system.progress_history.copy()
        }
    
    def _serialize_ai_system(self, ai_system) -> Dict[str, Any]:
        """Serialize AI system state"""
        return {
            "ai_factions": {
                faction_name: {
                    "faction_name": ai_faction.faction_name,
                    "personality": ai_faction.personality.value,
                    "controlled_stations": ai_faction.controlled_stations.copy(),
                    "resources": ai_faction.resources.copy(),
                    "priorities": {
                        action.value: priority
                        for action, priority in ai_faction.priorities.items()
                    },
                    "action_history": ai_faction.action_history.copy(),
                    "aggression_level": ai_faction.aggression_level,
                    "expansion_desire": ai_faction.expansion_desire,
                    "diplomatic_tendency": ai_faction.diplomatic_tendency
                }
                for faction_name, ai_faction in ai_system.ai_factions.items()
            },
            "action_probability": ai_system.action_probability,
            "resource_generation_rate": ai_system.resource_generation_rate
        }
    
    def _validate_save_data(self, save_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate loaded save data"""
        try:
            # Check for required fields
            required_fields = [
                "current_turn", "game_phase", "player", "statistics",
                "metro_map", "metadata"
            ]
            
            for field in required_fields:
                if field not in save_data:
                    return {
                        "valid": False,
                        "reason": f"Missing required field: {field}"
                    }
            
            # Check save version compatibility
            metadata = save_data.get("metadata", {})
            save_version = metadata.get("save_version", "unknown")
            
            if save_version != self.save_version:
                self.logger.warning(f"Save version mismatch: {save_version} vs {self.save_version}")
                # Could implement version migration here
            
            # Validate player data
            player_data = save_data["player"]
            if not all(key in player_data for key in ["faction", "resources", "controlled_stations"]):
                return {
                    "valid": False,
                    "reason": "Invalid player data structure"
                }
            
            # Validate metro map data
            metro_map_data = save_data["metro_map"]
            if not all(key in metro_map_data for key in ["stations", "tunnels"]):
                return {
                    "valid": False,
                    "reason": "Invalid metro map data structure"
                }
            
            return {"valid": True, "reason": "Save data is valid"}
            
        except Exception as e:
            return {
                "valid": False,
                "reason": f"Validation error: {str(e)}"
            }
    
    def create_quick_save(self, game_state: GameStateManager) -> Dict[str, Any]:
        """Create a quick save with automatic naming"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slot_name = f"quicksave_{timestamp}"
        description = f"Quick save - Turn {game_state.current_turn}"
        
        return self.save_game(game_state, slot_name, description)
    
    def get_auto_save_name(self, game_state: GameStateManager) -> str:
        """Generate auto-save name based on game state"""
        return f"autosave_turn_{game_state.current_turn:03d}"
    
    def cleanup_old_saves(self, max_saves: int = None) -> Dict[str, Any]:
        """Clean up old save files, keeping only the most recent ones"""
        if max_saves is None:
            max_saves = self.max_save_slots
        
        try:
            save_slots = self.get_save_slots()
            
            if len(save_slots) <= max_saves:
                return {
                    "success": True,
                    "message": f"No cleanup needed ({len(save_slots)} saves)",
                    "deleted_count": 0
                }
            
            # Delete oldest saves
            saves_to_delete = save_slots[max_saves:]
            deleted_count = 0
            
            for save_slot in saves_to_delete:
                result = self.delete_save(save_slot["slot_name"])
                if result["success"]:
                    deleted_count += 1
            
            return {
                "success": True,
                "message": f"Cleaned up {deleted_count} old saves",
                "deleted_count": deleted_count
            }
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup saves: {e}")
            return {
                "success": False,
                "message": f"Cleanup failed: {str(e)}",
                "error": str(e)
            }