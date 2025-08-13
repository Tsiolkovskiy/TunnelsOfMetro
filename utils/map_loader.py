"""
Map Loader Utility
Loads and initializes the Metro map from data files
"""

import logging
from typing import Optional

from systems.metro_map import MetroMap
from data.station import Station
from data.tunnel import Tunnel, TunnelState
from data.map_data import MetroMapData
from data.infrastructure import Infrastructure, BuildingType


class MapLoader:
    """
    Utility class for loading and initializing the Metro map
    """
    
    def __init__(self):
        """Initialize the map loader"""
        self.logger = logging.getLogger(__name__)
    
    def load_default_map(self) -> MetroMap:
        """
        Load the default Moscow Metro map with authentic stations and connections
        
        Returns:
            Fully initialized MetroMap instance
        """
        self.logger.info("Loading default Moscow Metro map...")
        
        metro_map = MetroMap()
        
        # Load stations
        self._load_stations(metro_map)
        
        # Load tunnel connections
        self._load_tunnels(metro_map)
        
        # Add initial infrastructure to key stations
        self._add_initial_infrastructure(metro_map)
        
        # Validate the loaded map
        issues = metro_map.validate_map_integrity()
        if issues:
            self.logger.warning(f"Map validation issues: {issues}")
        else:
            self.logger.info("Map validation passed")
        
        stats = metro_map.get_map_statistics()
        self.logger.info(f"Map loaded successfully: {stats}")
        
        return metro_map
    
    def _load_stations(self, metro_map: MetroMap):
        """Load all stations into the map"""
        station_data = MetroMapData.get_station_data()
        
        for data in station_data:
            station = Station(
                name=data["name"],
                position=data["position"],
                metro_line=data["metro_line"],
                faction=data["faction"],
                population=data["population"],
                morale=data["morale"]
            )
            
            # Add special traits
            if "special_traits" in data:
                station.special_traits = data["special_traits"]
            
            # Set initial resources based on faction and traits
            self._set_initial_resources(station)
            
            metro_map.add_station(station)
            
        self.logger.info(f"Loaded {len(station_data)} stations")
    
    def _load_tunnels(self, metro_map: MetroMap):
        """Load all tunnel connections into the map"""
        tunnel_data = MetroMapData.get_tunnel_connections()
        
        for data in tunnel_data:
            state = TunnelState(data.get("state", "clear"))
            hazard_level = data.get("hazard_level", 0)
            metro_line = data.get("metro_line", "")
            
            tunnel = Tunnel(
                station_a=data["station_a"],
                station_b=data["station_b"],
                state=state,
                hazard_level=hazard_level,
                metro_line=metro_line
            )
            
            metro_map.add_tunnel(tunnel)
        
        self.logger.info(f"Loaded {len(tunnel_data)} tunnel connections")
    
    def _set_initial_resources(self, station: Station):
        """Set initial resources for a station based on its characteristics"""
        # Base resources for all stations
        base_resources = {
            "food": 20,
            "clean_water": 10,
            "scrap": 15,
            "medicine": 5,
            "mgr_rounds": 2
        }
        
        # Faction-specific bonuses
        faction_bonuses = {
            "Rangers": {"mgr_rounds": 8, "medicine": 5},
            "Polis": {"mgr_rounds": 10, "medicine": 10, "clean_water": 15},
            "Fourth Reich": {"mgr_rounds": 5, "scrap": 10},
            "Red Line": {"food": 15, "scrap": 10},
            "Hanza": {"mgr_rounds": 15, "food": 10, "clean_water": 5},
            "Invisible Watchers": {"mgr_rounds": 20, "medicine": 15},
            "Independent": {"food": 5, "scrap": 5}
        }
        
        # Apply base resources
        for resource, amount in base_resources.items():
            station.resources.set(resource, amount)
        
        # Apply faction bonuses
        faction = station.controlling_faction
        if faction in faction_bonuses:
            for resource, bonus in faction_bonuses[faction].items():
                current = station.resources.get(resource)
                station.resources.set(resource, current + bonus)
        
        # Special trait bonuses
        trait_bonuses = {
            "mushroom_cultivation": {"food": 20},
            "great_library": {"mgr_rounds": 10},
            "trade_center": {"mgr_rounds": 15, "food": 10},
            "major_hub": {"clean_water": 10, "scrap": 10},
            "military_discipline": {"mgr_rounds": 5},
            "secret_facility": {"mgr_rounds": 25, "medicine": 20}
        }
        
        for trait in station.special_traits:
            if trait in trait_bonuses:
                for resource, bonus in trait_bonuses[trait].items():
                    current = station.resources.get(resource)
                    station.resources.set(resource, current + bonus)
    
    def _add_initial_infrastructure(self, metro_map: MetroMap):
        """Add initial infrastructure to key stations"""
        infrastructure_assignments = {
            # Rangers stations
            "VDNKh": [BuildingType.MUSHROOM_FARM, BuildingType.BARRACKS],
            "Park Pobedy": [BuildingType.BARRACKS, BuildingType.SCRAP_WORKSHOP],
            
            # Polis stations
            "Polis": [BuildingType.LIBRARY, BuildingType.MED_BAY, BuildingType.WATER_FILTER],
            "Kiyevskaya": [BuildingType.MED_BAY],
            "Teatralnaya": [BuildingType.LIBRARY],
            
            # Fourth Reich stations
            "Tverskaya": [BuildingType.BARRACKS, BuildingType.FORTIFICATIONS],
            "Okhotny Ryad": [BuildingType.BARRACKS],
            
            # Red Line stations
            "Preobrazhenskaya Ploshchad": [BuildingType.MUSHROOM_FARM, BuildingType.BARRACKS],
            "Park Kultury": [BuildingType.MUSHROOM_FARM],
            "Sokolniki": [BuildingType.BARRACKS],
            
            # Hanza stations
            "Kurskaya": [BuildingType.MARKET, BuildingType.WATER_FILTER],
            "Komsomolskaya": [BuildingType.MARKET, BuildingType.SCRAP_WORKSHOP],
            
            # Invisible Watchers stations
            "Lubyanka": [BuildingType.MED_BAY, BuildingType.FORTIFICATIONS],
            "Taganskaya": [BuildingType.FORTIFICATIONS],
            
            # Independent stations
            "Mayakovskaya": [BuildingType.MUSHROOM_FARM]
        }
        
        for station_name, buildings in infrastructure_assignments.items():
            station = metro_map.get_station(station_name)
            if station:
                for building_type in buildings:
                    # Major faction stations get level 2 buildings
                    level = 2 if station.controlling_faction in ["Rangers", "Polis", "Fourth Reich", "Red Line", "Hanza"] else 1
                    station.add_infrastructure(building_type, level)
                    
                self.logger.debug(f"Added infrastructure to {station_name}: {[b.value for b in buildings]}")
        
        self.logger.info("Added initial infrastructure to key stations")
    
    def save_map(self, metro_map: MetroMap, filename: str) -> bool:
        """
        Save map to file
        
        Args:
            metro_map: MetroMap instance to save
            filename: Output filename
            
        Returns:
            True if save was successful
        """
        try:
            import json
            from pathlib import Path
            
            # Create saves directory if it doesn't exist
            saves_dir = Path("saves")
            saves_dir.mkdir(exist_ok=True)
            
            # Convert map to dictionary
            map_data = metro_map.to_dict()
            
            # Save to file
            save_path = saves_dir / filename
            with open(save_path, 'w') as f:
                json.dump(map_data, f, indent=2)
            
            self.logger.info(f"Map saved to {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save map: {e}")
            return False
    
    def load_map(self, filename: str) -> Optional[MetroMap]:
        """
        Load map from file
        
        Args:
            filename: Input filename
            
        Returns:
            Loaded MetroMap instance or None if failed
        """
        try:
            import json
            from pathlib import Path
            
            save_path = Path("saves") / filename
            if not save_path.exists():
                self.logger.error(f"Save file not found: {save_path}")
                return None
            
            with open(save_path, 'r') as f:
                map_data = json.load(f)
            
            # Reconstruct map from data
            metro_map = self._reconstruct_map(map_data)
            
            self.logger.info(f"Map loaded from {save_path}")
            return metro_map
            
        except Exception as e:
            self.logger.error(f"Failed to load map: {e}")
            return None
    
    def _reconstruct_map(self, map_data: dict) -> MetroMap:
        """Reconstruct MetroMap from saved data"""
        metro_map = MetroMap()
        
        # Reconstruct stations
        for station_name, station_data in map_data["stations"].items():
            station = Station(
                name=station_data["name"],
                position=tuple(station_data["position"]),
                metro_line=station_data["metro_line"],
                faction=station_data["faction"],
                population=station_data["population"],
                morale=station_data["morale"]
            )
            
            # Restore resources
            station.resources.from_dict(station_data["resources"])
            
            # Restore special traits
            station.special_traits = station_data.get("special_traits", [])
            
            # Restore infrastructure
            for building_type_str, building_data in station_data.get("infrastructure", {}).items():
                building_type = BuildingType(building_type_str)
                infrastructure = Infrastructure.from_dict(building_data)
                station.infrastructure[building_type] = infrastructure
            
            metro_map.add_station(station)
        
        # Reconstruct tunnels
        for tunnel_data in map_data["tunnels"]:
            tunnel = Tunnel.from_dict(tunnel_data)
            metro_map.add_tunnel(tunnel)
        
        # Restore metro lines
        metro_map.metro_lines = map_data.get("metro_lines", {})
        
        return metro_map