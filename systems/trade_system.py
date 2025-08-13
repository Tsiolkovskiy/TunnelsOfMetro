"""
Trade System
Handles trade routes, caravans, and economic relationships between stations
"""

import logging
import random
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
from dataclasses import dataclass
import time

from systems.metro_map import MetroMap
from data.resources import ResourcePool
from data.tunnel import TunnelState


class CaravanStatus(Enum):
    """Status of trade caravans"""
    PREPARING = "preparing"
    TRAVELING = "traveling"
    TRADING = "trading"
    RETURNING = "returning"
    COMPLETED = "completed"
    LOST = "lost"
    ATTACKED = "attacked"


class TradeRouteStatus(Enum):
    """Status of trade routes"""
    ACTIVE = "active"
    DISRUPTED = "disrupted"
    BLOCKED = "blocked"
    INACTIVE = "inactive"


@dataclass
class TradeOffer:
    """Trade offer between stations"""
    offering_station: str
    requesting_station: str
    offered_resources: Dict[str, int]
    requested_resources: Dict[str, int]
    mgr_cost: int
    expires_turn: int
    
    def is_expired(self, current_turn: int) -> bool:
        return current_turn > self.expires_turn


@dataclass
class Caravan:
    """Physical caravan unit moving between stations"""
    caravan_id: str
    origin: str
    destination: str
    current_position: str
    path: List[str]
    path_index: int
    
    cargo: Dict[str, int]
    status: CaravanStatus
    
    created_turn: int
    estimated_arrival: int
    
    # Risk factors
    escort_strength: int = 0
    stealth_level: int = 0
    
    def get_current_tunnel(self) -> Optional[Tuple[str, str]]:
        """Get current tunnel being traversed"""
        if self.path_index < len(self.path) - 1:
            return (self.path[self.path_index], self.path[self.path_index + 1])
        return None
    
    def advance_position(self) -> bool:
        """Advance caravan to next position. Returns True if destination reached."""
        if self.path_index < len(self.path) - 1:
            self.path_index += 1
            self.current_position = self.path[self.path_index]
            return self.current_position == self.destination
        return True


@dataclass
class TradeRoute:
    """Established trade route between stations"""
    route_id: str
    station_a: str
    station_b: str
    path: List[str]
    
    status: TradeRouteStatus
    established_turn: int
    last_used_turn: int
    
    # Trade statistics
    total_trades: int = 0
    total_value: int = 0
    
    # Route security
    security_level: int = 50  # 0-100
    last_incident_turn: int = 0


class TradeSystem:
    """
    Complete trade and caravan management system
    
    Features:
    - Physical caravan units that move on the map
    - Trade route establishment and management
    - Supply line visualization
    - Dynamic pricing based on supply and demand
    - Caravan security and risk management
    """
    
    def __init__(self, metro_map: MetroMap):
        """
        Initialize trade system
        
        Args:
            metro_map: MetroMap instance
        """
        self.metro_map = metro_map
        self.logger = logging.getLogger(__name__)
        
        # Trade data
        self.active_caravans: Dict[str, Caravan] = {}
        self.trade_routes: Dict[str, TradeRoute] = {}
        self.trade_offers: List[TradeOffer] = []
        
        # Trade settings
        self.base_trade_cost = 5  # Base MGR cost for trade
        self.caravan_travel_time = 2  # Turns per station
        
        # Market data
        self.market_prices: Dict[str, Dict[str, int]] = {}
        self.supply_demand: Dict[str, Dict[str, float]] = {}
        
        # Caravan counter for unique IDs
        self.caravan_counter = 0
        
        self.logger.info("Trade system initialized")
    
    def create_trade_offer(self, origin: str, target: str, offered: Dict[str, int], 
                          requested: Dict[str, int], current_turn: int) -> Dict[str, Any]:
        """
        Create a trade offer between stations
        
        Args:
            origin: Offering station
            target: Requesting station
            offered: Resources being offered
            requested: Resources being requested
            current_turn: Current game turn
            
        Returns:
            Result dictionary
        """
        # Validate stations
        origin_station = self.metro_map.get_station(origin)
        target_station = self.metro_map.get_station(target)
        
        if not origin_station or not target_station:
            return {"success": False, "message": "Invalid stations for trade"}
        
        # Check if trade route exists or can be established
        route_path = self.metro_map.find_path(origin, target, "caravan")
        if not route_path:
            return {"success": False, "message": f"No trade route available to {target}"}
        
        # Calculate MGR cost based on distance and risk
        mgr_cost = self._calculate_trade_cost(origin, target, offered, requested)
        
        # Create trade offer
        offer = TradeOffer(
            offering_station=origin,
            requesting_station=target,
            offered_resources=offered.copy(),
            requested_resources=requested.copy(),
            mgr_cost=mgr_cost,
            expires_turn=current_turn + 3  # Expires in 3 turns
        )
        
        self.trade_offers.append(offer)
        
        return {
            "success": True,
            "message": f"Trade offer created: {origin} -> {target}",
            "mgr_cost": mgr_cost,
            "offer": offer
        }
    
    def execute_trade(self, origin: str, target: str, player_resources: ResourcePool,
                     current_turn: int) -> Dict[str, Any]:
        """
        Execute a trade by sending a caravan
        
        Args:
            origin: Origin station
            target: Target station
            player_resources: Player's resource pool
            current_turn: Current game turn
            
        Returns:
            Result dictionary
        """
        # Simple trade for now - exchange MGR for food
        mgr_cost = 20
        food_gain = 10
        
        # Check resources
        if not player_resources.has_sufficient("mgr_rounds", mgr_cost):
            return {"success": False, "message": f"Insufficient MGR for trade (need {mgr_cost})"}
        
        # Check if route is available
        route_path = self.metro_map.find_path(origin, target, "caravan")
        if not route_path:
            return {"success": False, "message": f"No trade route available to {target}"}
        
        # Create caravan
        caravan_id = f"caravan_{self.caravan_counter}"
        self.caravan_counter += 1
        
        caravan = Caravan(
            caravan_id=caravan_id,
            origin=origin,
            destination=target,
            current_position=origin,
            path=route_path,
            path_index=0,
            cargo={"mgr_rounds": mgr_cost},
            status=CaravanStatus.TRAVELING,
            created_turn=current_turn,
            estimated_arrival=current_turn + len(route_path) * self.caravan_travel_time
        )
        
        self.active_caravans[caravan_id] = caravan
        
        # Consume resources
        player_resources.subtract("mgr_rounds", mgr_cost)
        
        # Establish or update trade route
        self._update_trade_route(origin, target, route_path, current_turn)
        
        return {
            "success": True,
            "message": f"Caravan dispatched to {target}. Expected return: {food_gain} food",
            "caravan_id": caravan_id,
            "estimated_arrival": caravan.estimated_arrival
        }
    
    def _calculate_trade_cost(self, origin: str, target: str, offered: Dict[str, int],
                            requested: Dict[str, int]) -> int:
        """Calculate MGR cost for trade"""
        base_cost = self.base_trade_cost
        
        # Distance factor
        path = self.metro_map.find_path(origin, target, "caravan")
        if path:
            distance_cost = len(path) * 2
        else:
            distance_cost = 10  # High cost for difficult routes
        
        # Resource value factor
        resource_values = {"food": 2, "clean_water": 3, "scrap": 1, "medicine": 5, "mgr_rounds": 1}
        
        offered_value = sum(amount * resource_values.get(resource, 1) 
                           for resource, amount in offered.items())
        requested_value = sum(amount * resource_values.get(resource, 1) 
                             for resource, amount in requested.items())
        
        value_difference = abs(offered_value - requested_value)
        
        return base_cost + distance_cost + (value_difference // 10)
    
    def _update_trade_route(self, station_a: str, station_b: str, path: List[str], current_turn: int):
        """Update or create trade route"""
        route_id = f"{min(station_a, station_b)}_{max(station_a, station_b)}"
        
        if route_id in self.trade_routes:
            # Update existing route
            route = self.trade_routes[route_id]
            route.last_used_turn = current_turn
            route.total_trades += 1
            route.status = TradeRouteStatus.ACTIVE
        else:
            # Create new route
            route = TradeRoute(
                route_id=route_id,
                station_a=station_a,
                station_b=station_b,
                path=path,
                status=TradeRouteStatus.ACTIVE,
                established_turn=current_turn,
                last_used_turn=current_turn,
                total_trades=1
            )
            self.trade_routes[route_id] = route
            
            self.logger.info(f"Established trade route: {station_a} <-> {station_b}")
    
    def process_caravans(self, current_turn: int, player_resources: ResourcePool) -> List[Dict[str, Any]]:
        """
        Process all active caravans
        
        Args:
            current_turn: Current game turn
            player_resources: Player's resource pool
            
        Returns:
            List of caravan events
        """
        events = []
        completed_caravans = []
        
        for caravan_id, caravan in self.active_caravans.items():
            if caravan.status == CaravanStatus.TRAVELING:
                # Check if caravan should advance
                if current_turn >= caravan.created_turn + (caravan.path_index + 1) * self.caravan_travel_time:
                    # Check for hazards in current tunnel
                    tunnel_info = caravan.get_current_tunnel()
                    if tunnel_info:
                        hazard_result = self._check_caravan_hazards(caravan, tunnel_info, current_turn)
                        if hazard_result:
                            events.append(hazard_result)
                            if hazard_result.get("caravan_lost"):
                                caravan.status = CaravanStatus.LOST
                                continue
                    
                    # Advance caravan
                    reached_destination = caravan.advance_position()
                    
                    if reached_destination:
                        # Caravan reached destination - execute trade
                        trade_result = self._complete_caravan_trade(caravan, player_resources)
                        events.append(trade_result)
                        caravan.status = CaravanStatus.COMPLETED
                        completed_caravans.append(caravan_id)
                    else:
                        events.append({
                            "type": "caravan_progress",
                            "caravan_id": caravan_id,
                            "current_position": caravan.current_position,
                            "message": f"Caravan {caravan_id} reached {caravan.current_position}"
                        })
        
        # Remove completed caravans
        for caravan_id in completed_caravans:
            del self.active_caravans[caravan_id]
        
        return events
    
    def _check_caravan_hazards(self, caravan: Caravan, tunnel_info: Tuple[str, str], 
                              current_turn: int) -> Optional[Dict[str, Any]]:
        """Check for hazards affecting caravan"""
        station_a, station_b = tunnel_info
        tunnel = self.metro_map.get_tunnel(station_a, station_b)
        
        if not tunnel:
            return None
        
        # Base survival chance
        survival_chance = 0.9
        
        # Tunnel state affects survival
        if tunnel.state == TunnelState.HAZARDOUS:
            survival_chance -= 0.1
        elif tunnel.state == TunnelState.INFESTED:
            survival_chance -= 0.3
        elif tunnel.state == TunnelState.ANOMALOUS:
            survival_chance -= 0.5
        elif tunnel.state == TunnelState.COLLAPSED:
            survival_chance = 0.0  # Cannot pass
        
        # Escort strength helps
        survival_chance += caravan.escort_strength * 0.1
        
        # Roll for survival
        if random.random() > survival_chance:
            return {
                "type": "caravan_lost",
                "caravan_id": caravan.caravan_id,
                "location": f"{station_a} -> {station_b}",
                "message": f"Caravan {caravan.caravan_id} lost in {tunnel.state.value} tunnel",
                "caravan_lost": True
            }
        
        # Minor incidents
        if random.random() < 0.1:  # 10% chance of minor incident
            return {
                "type": "caravan_incident",
                "caravan_id": caravan.caravan_id,
                "location": caravan.current_position,
                "message": f"Caravan {caravan.caravan_id} encountered difficulties but continued"
            }
        
        return None
    
    def _complete_caravan_trade(self, caravan: Caravan, player_resources: ResourcePool) -> Dict[str, Any]:
        """Complete caravan trade at destination"""
        # Simple trade completion - gain food for MGR
        food_gained = 10
        player_resources.add("food", food_gained)
        
        return {
            "type": "trade_completed",
            "caravan_id": caravan.caravan_id,
            "origin": caravan.origin,
            "destination": caravan.destination,
            "message": f"Trade completed: Gained {food_gained} food",
            "resources_gained": {"food": food_gained}
        }
    
    def get_active_caravans(self) -> Dict[str, Caravan]:
        """Get all active caravans"""
        return self.active_caravans.copy()
    
    def get_trade_routes(self) -> Dict[str, TradeRoute]:
        """Get all established trade routes"""
        return self.trade_routes.copy()
    
    def get_supply_lines(self, station: str) -> List[str]:
        """Get supply lines connected to a station"""
        supply_lines = []
        
        for route in self.trade_routes.values():
            if route.status == TradeRouteStatus.ACTIVE:
                if route.station_a == station:
                    supply_lines.append(route.station_b)
                elif route.station_b == station:
                    supply_lines.append(route.station_a)
        
        return supply_lines
    
    def disrupt_trade_route(self, station_a: str, station_b: str, reason: str = ""):
        """Disrupt a trade route"""
        route_id = f"{min(station_a, station_b)}_{max(station_a, station_b)}"
        
        if route_id in self.trade_routes:
            route = self.trade_routes[route_id]
            route.status = TradeRouteStatus.DISRUPTED
            
            self.logger.info(f"Trade route disrupted: {station_a} <-> {station_b} ({reason})")
    
    def get_trade_opportunities(self, origin: str) -> List[Dict[str, Any]]:
        """Get available trade opportunities from a station"""
        opportunities = []
        
        # Find stations within trade range
        reachable = self.metro_map.find_all_paths_within_range(origin, 10, "caravan")
        
        for station_name in reachable:
            if station_name != origin:
                station = self.metro_map.get_station(station_name)
                if station:
                    # Simple opportunity - stations that accept MGR for food
                    opportunity = {
                        "target": station_name,
                        "faction": station.controlling_faction,
                        "distance": len(self.metro_map.find_path(origin, station_name, "caravan") or []),
                        "offers": [
                            {
                                "give": {"mgr_rounds": 20},
                                "receive": {"food": 10},
                                "description": "Trade MGR for food"
                            }
                        ]
                    }
                    opportunities.append(opportunity)
        
        return opportunities
    
    def update_market_prices(self, current_turn: int):
        """Update market prices based on supply and demand"""
        # Simple price fluctuation
        for station_name in self.metro_map.stations:
            if station_name not in self.market_prices:
                self.market_prices[station_name] = {
                    "food": 2,
                    "clean_water": 3,
                    "scrap": 1,
                    "medicine": 5
                }
            
            # Random price fluctuations
            for resource in self.market_prices[station_name]:
                change = random.uniform(-0.1, 0.1)
                self.market_prices[station_name][resource] = max(1, 
                    int(self.market_prices[station_name][resource] * (1 + change)))
    
    def get_trade_statistics(self) -> Dict[str, Any]:
        """Get trade system statistics"""
        return {
            "active_caravans": len(self.active_caravans),
            "established_routes": len(self.trade_routes),
            "active_routes": len([r for r in self.trade_routes.values() 
                                if r.status == TradeRouteStatus.ACTIVE]),
            "total_trades": sum(r.total_trades for r in self.trade_routes.values()),
            "pending_offers": len(self.trade_offers)
        }
    
    def process_turn(self, current_turn: int, player_resources: ResourcePool) -> List[Dict[str, Any]]:
        """Process end-of-turn trade updates"""
        events = []
        
        # Process caravans
        caravan_events = self.process_caravans(current_turn, player_resources)
        events.extend(caravan_events)
        
        # Update market prices
        self.update_market_prices(current_turn)
        
        # Remove expired trade offers
        self.trade_offers = [offer for offer in self.trade_offers 
                           if not offer.is_expired(current_turn)]
        
        return events