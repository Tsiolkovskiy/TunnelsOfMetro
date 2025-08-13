"""
Metro Map System
Manages the Moscow Metro map with stations, tunnels, and pathfinding
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, deque
import heapq

from data.station import Station
from data.tunnel import Tunnel, TunnelState


class MetroMap:
    """
    Manages the complete Moscow Metro system
    
    This class handles:
    - Station and tunnel management
    - Pathfinding algorithms for movement and trade
    - Area effects and events
    - Map state updates and queries
    """
    
    def __init__(self):
        """Initialize the Metro map system"""
        self.logger = logging.getLogger(__name__)
        
        # Core data structures
        self.stations: Dict[str, Station] = {}
        self.tunnels: List[Tunnel] = []
        
        # Adjacency graph for pathfinding (station_name -> set of connected stations)
        self.adjacency: Dict[str, set[str]] = defaultdict(set)
        
        # Metro line organization
        self.metro_lines: Dict[str, List[str]] = {}  # line_name -> station_names
        
        # Spatial indexing for area effects
        self.station_positions: Dict[str, Tuple[int, int]] = {}
        
        self.logger.info("Metro map system initialized")
    
    def add_station(self, station: Station) -> bool:
        """
        Add a station to the map
        
        Args:
            station: Station object to add
            
        Returns:
            True if station was added successfully
        """
        if station.name in self.stations:
            self.logger.warning(f"Station {station.name} already exists")
            return False
        
        self.stations[station.name] = station
        self.station_positions[station.name] = station.position
        
        # Add to metro line
        if station.metro_line:
            if station.metro_line not in self.metro_lines:
                self.metro_lines[station.metro_line] = []
            self.metro_lines[station.metro_line].append(station.name)
        
        self.logger.info(f"Added station: {station.name}")
        return True
    
    def add_tunnel(self, tunnel: Tunnel) -> bool:
        """
        Add a tunnel connection to the map
        
        Args:
            tunnel: Tunnel object to add
            
        Returns:
            True if tunnel was added successfully
        """
        # Verify both stations exist
        if tunnel.station_a not in self.stations:
            self.logger.error(f"Station {tunnel.station_a} not found for tunnel")
            return False
        
        if tunnel.station_b not in self.stations:
            self.logger.error(f"Station {tunnel.station_b} not found for tunnel")
            return False
        
        # Check for duplicate tunnels
        for existing_tunnel in self.tunnels:
            if existing_tunnel.connects_stations(tunnel.station_a, tunnel.station_b):
                self.logger.warning(f"Tunnel between {tunnel.station_a} and {tunnel.station_b} already exists")
                return False
        
        # Add tunnel and update adjacency
        self.tunnels.append(tunnel)
        self.adjacency[tunnel.station_a].add(tunnel.station_b)
        self.adjacency[tunnel.station_b].add(tunnel.station_a)
        
        self.logger.info(f"Added tunnel: {tunnel.station_a} <-> {tunnel.station_b}")
        return True
    
    def get_station(self, station_name: str) -> Optional[Station]:
        """Get station by name"""
        return self.stations.get(station_name)
    
    def get_tunnel(self, station_a: str, station_b: str) -> Optional[Tunnel]:
        """
        Get tunnel between two stations
        
        Args:
            station_a: First station name
            station_b: Second station name
            
        Returns:
            Tunnel object if connection exists, None otherwise
        """
        for tunnel in self.tunnels:
            if tunnel.connects_stations(station_a, station_b):
                return tunnel
        return None
    
    def get_adjacent_stations(self, station_name: str) -> List[str]:
        """
        Get list of stations directly connected to the given station
        
        Args:
            station_name: Name of the station
            
        Returns:
            List of adjacent station names
        """
        return list(self.adjacency.get(station_name, set()))
    
    def find_path(
        self,
        origin: str,
        destination: str,
        unit_type: str = "military",
        avoid_dangerous: bool = True
    ) -> Optional[List[str]]:
        """
        Find shortest path between two stations using Dijkstra's algorithm
        
        Args:
            origin: Starting station name
            destination: Target station name
            unit_type: Type of unit for travel cost calculation
            avoid_dangerous: Whether to avoid dangerous tunnels
            
        Returns:
            List of station names forming the path, or None if no path exists
        """
        if origin not in self.stations or destination not in self.stations:
            self.logger.error(f"Invalid stations for pathfinding: {origin} -> {destination}")
            return None
        
        if origin == destination:
            return [origin]
        
        # Dijkstra's algorithm implementation
        distances = {station: float('inf') for station in self.stations}
        distances[origin] = 0
        previous = {}
        unvisited = [(0, origin)]
        visited = set()
        
        while unvisited:
            current_distance, current_station = heapq.heappop(unvisited)
            
            if current_station in visited:
                continue
            
            visited.add(current_station)
            
            if current_station == destination:
                # Reconstruct path
                path = []
                while current_station in previous:
                    path.append(current_station)
                    current_station = previous[current_station]
                path.append(origin)
                return list(reversed(path))
            
            # Check all adjacent stations
            for neighbor in self.adjacency[current_station]:
                if neighbor in visited:
                    continue
                
                tunnel = self.get_tunnel(current_station, neighbor)
                if not tunnel or not tunnel.is_passable(unit_type):
                    continue
                
                # Skip dangerous tunnels if requested
                if avoid_dangerous and tunnel.get_danger_level() > 50:
                    continue
                
                travel_cost = tunnel.calculate_travel_cost(unit_type)
                new_distance = current_distance + travel_cost
                
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current_station
                    heapq.heappush(unvisited, (new_distance, neighbor))
        
        # No path found
        self.logger.warning(f"No path found from {origin} to {destination}")
        return None
    
    def find_all_paths_within_range(
        self,
        origin: str,
        max_cost: int,
        unit_type: str = "military"
    ) -> Dict[str, int]:
        """
        Find all stations reachable within a given movement cost
        
        Args:
            origin: Starting station name
            max_cost: Maximum movement cost
            unit_type: Type of unit for travel cost calculation
            
        Returns:
            Dictionary mapping station names to their travel costs
        """
        if origin not in self.stations:
            return {}
        
        reachable = {origin: 0}
        queue = [(0, origin)]
        
        while queue:
            current_cost, current_station = heapq.heappop(queue)
            
            if current_cost > max_cost:
                continue
            
            for neighbor in self.adjacency[current_station]:
                tunnel = self.get_tunnel(current_station, neighbor)
                if not tunnel or not tunnel.is_passable(unit_type):
                    continue
                
                travel_cost = tunnel.calculate_travel_cost(unit_type)
                new_cost = current_cost + travel_cost
                
                if new_cost <= max_cost and (neighbor not in reachable or new_cost < reachable[neighbor]):
                    reachable[neighbor] = new_cost
                    heapq.heappush(queue, (new_cost, neighbor))
        
        return reachable
    
    def get_stations_by_faction(self, faction_name: str) -> List[Station]:
        """
        Get all stations controlled by a specific faction
        
        Args:
            faction_name: Name of the faction
            
        Returns:
            List of stations controlled by the faction
        """
        return [station for station in self.stations.values() 
                if station.controlling_faction == faction_name]
    
    def get_stations_on_line(self, metro_line: str) -> List[Station]:
        """
        Get all stations on a specific metro line
        
        Args:
            metro_line: Name of the metro line
            
        Returns:
            List of stations on the line
        """
        station_names = self.metro_lines.get(metro_line, [])
        return [self.stations[name] for name in station_names if name in self.stations]
    
    def apply_area_event(self, event: Dict[str, Any], affected_area: Dict[str, Any]):
        """
        Apply an event to multiple stations in an area
        
        Args:
            event: Event data to apply
            affected_area: Area definition (center, radius, or station list)
        """
        affected_stations = []
        
        if "stations" in affected_area:
            # Specific list of stations
            affected_stations = [name for name in affected_area["stations"] if name in self.stations]
        
        elif "center" in affected_area and "radius" in affected_area:
            # Circular area around a center point
            center_x, center_y = affected_area["center"]
            radius = affected_area["radius"]
            
            for station_name, (x, y) in self.station_positions.items():
                distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                if distance <= radius:
                    affected_stations.append(station_name)
        
        elif "metro_line" in affected_area:
            # Entire metro line
            affected_stations = self.metro_lines.get(affected_area["metro_line"], [])
        
        # Apply event to all affected stations
        for station_name in affected_stations:
            if station_name in self.stations:
                self.stations[station_name].apply_event(event)
                self.logger.info(f"Applied area event to station {station_name}")
    
    def update_tunnel_states(self, state_changes: List[Dict[str, Any]]):
        """
        Update multiple tunnel states
        
        Args:
            state_changes: List of tunnel state change data
        """
        for change in state_changes:
            station_a = change.get("station_a")
            station_b = change.get("station_b")
            new_state = change.get("state")
            reason = change.get("reason", "")
            
            tunnel = self.get_tunnel(station_a, station_b)
            if tunnel and new_state:
                try:
                    tunnel_state = TunnelState(new_state)
                    tunnel.update_state(tunnel_state, reason)
                except ValueError:
                    self.logger.error(f"Invalid tunnel state: {new_state}")
    
    def process_turn(self, current_turn: int):
        """
        Process end-of-turn updates for all map elements
        
        Args:
            current_turn: Current game turn number
        """
        # Process all stations
        for station in self.stations.values():
            station.process_turn()
        
        # Process all tunnels
        for tunnel in self.tunnels:
            tunnel.process_turn(current_turn)
        
        self.logger.debug(f"Processed turn {current_turn} for map")
    
    def get_map_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive map statistics
        
        Returns:
            Dictionary containing map statistics
        """
        faction_counts = defaultdict(int)
        tunnel_states = defaultdict(int)
        total_population = 0
        
        for station in self.stations.values():
            faction_counts[station.controlling_faction] += 1
            total_population += station.population
        
        for tunnel in self.tunnels:
            tunnel_states[tunnel.state.value] += 1
        
        return {
            "total_stations": len(self.stations),
            "total_tunnels": len(self.tunnels),
            "total_population": total_population,
            "metro_lines": len(self.metro_lines),
            "faction_control": dict(faction_counts),
            "tunnel_states": dict(tunnel_states),
            "average_population": total_population // len(self.stations) if self.stations else 0
        }
    
    def validate_map_integrity(self) -> List[str]:
        """
        Validate map integrity and return list of issues
        
        Returns:
            List of validation error messages
        """
        issues = []
        
        # Check for isolated stations
        for station_name in self.stations:
            if not self.adjacency[station_name]:
                issues.append(f"Station {station_name} has no tunnel connections")
        
        # Check for invalid tunnel references
        for tunnel in self.tunnels:
            if tunnel.station_a not in self.stations:
                issues.append(f"Tunnel references non-existent station: {tunnel.station_a}")
            if tunnel.station_b not in self.stations:
                issues.append(f"Tunnel references non-existent station: {tunnel.station_b}")
        
        # Check for disconnected components
        if self.stations:
            visited = set()
            start_station = next(iter(self.stations))
            self._dfs_visit(start_station, visited)
            
            if len(visited) != len(self.stations):
                unconnected = set(self.stations.keys()) - visited
                issues.append(f"Disconnected stations: {list(unconnected)}")
        
        return issues
    
    def _dfs_visit(self, station: str, visited: set[str]):
        """Depth-first search helper for connectivity checking"""
        visited.add(station)
        for neighbor in self.adjacency[station]:
            if neighbor not in visited:
                self._dfs_visit(neighbor, visited)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert map to dictionary for serialization"""
        return {
            "stations": {name: station.get_info() for name, station in self.stations.items()},
            "tunnels": [tunnel.to_dict() for tunnel in self.tunnels],
            "metro_lines": self.metro_lines.copy()
        }
    
    def get_info(self) -> Dict[str, Any]:
        """Get comprehensive map information"""
        return {
            "statistics": self.get_map_statistics(),
            "validation_issues": self.validate_map_integrity(),
            "metro_lines": list(self.metro_lines.keys())
        }
    
    def __str__(self) -> str:
        """String representation"""
        stats = self.get_map_statistics()
        return f"MetroMap({stats['total_stations']} stations, {stats['total_tunnels']} tunnels)"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return f"MetroMap(stations={len(self.stations)}, tunnels={len(self.tunnels)}, lines={len(self.metro_lines)})"