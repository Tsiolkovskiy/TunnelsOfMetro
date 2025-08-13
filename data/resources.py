"""
Resource Management System
Handles all resource types and transactions in the Metro universe
"""

import logging
import random
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum


class ResourceType(Enum):
    """Enumeration of all resource types"""
    FOOD = "food"
    CLEAN_WATER = "clean_water"
    SCRAP = "scrap"
    MEDICINE = "medicine"
    MGR_ROUNDS = "mgr_rounds"


class ResourceRarity(Enum):
    """Resource rarity levels affecting availability and value"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    LEGENDARY = "legendary"


@dataclass
class ResourceTransaction:
    """Represents a resource transaction between entities"""
    resource_type: str
    amount: int
    source: str
    destination: str
    cost: int = 0
    timestamp: Optional[str] = None
    transaction_id: Optional[str] = None


@dataclass
class ResourceMarketData:
    """Market data for resource trading"""
    resource_type: str
    base_price: int
    current_price: int
    supply: int
    demand: int
    volatility: float
    rarity: ResourceRarity


class ResourcePool:
    """
    Manages a collection of resources for a faction or station
    
    Handles the five main resource types:
    - Food: Sustenance for population
    - Clean Water: Essential for health and morale
    - Scrap: Raw materials for construction and repairs
    - Medicine: Medical supplies for health and crisis response
    - MGR Rounds: Military-Grade Rounds (premium currency)
    """
    
    def __init__(self, initial_resources: Optional[Dict[str, int]] = None):
        """
        Initialize resource pool
        
        Args:
            initial_resources: Starting resource amounts
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize all resource types with default starting amounts
        self._resources = {
            "food": 50,
            "clean_water": 30,
            "scrap": 40,
            "medicine": 15,
            "mgr_rounds": 25
        }
        
        # Set initial values if provided
        if initial_resources:
            for resource, amount in initial_resources.items():
                if resource in self._resources:
                    self._resources[resource] = max(0, amount)
                else:
                    self.logger.warning(f"Unknown resource type: {resource}")
    
    def get(self, resource_type: str) -> int:
        """
        Get current amount of a resource
        
        Args:
            resource_type: Type of resource to query
            
        Returns:
            Current amount of the resource
        """
        return self._resources.get(resource_type, 0)
    
    def set(self, resource_type: str, amount: int) -> bool:
        """
        Set resource amount directly
        
        Args:
            resource_type: Type of resource
            amount: New amount (cannot be negative)
            
        Returns:
            True if successful
        """
        if resource_type not in self._resources:
            self.logger.error(f"Unknown resource type: {resource_type}")
            return False
        
        if amount < 0:
            self.logger.error(f"Cannot set negative resource amount: {amount}")
            return False
        
        old_amount = self._resources[resource_type]
        self._resources[resource_type] = amount
        
        if old_amount != amount:
            self.logger.debug(f"Resource {resource_type}: {old_amount} -> {amount}")
        
        return True
    
    def add(self, resource_type: str, amount: int) -> bool:
        """
        Add resources to the pool
        
        Args:
            resource_type: Type of resource to add
            amount: Amount to add (can be negative for subtraction)
            
        Returns:
            True if successful
        """
        if resource_type not in self._resources:
            self.logger.error(f"Unknown resource type: {resource_type}")
            return False
        
        new_amount = self._resources[resource_type] + amount
        
        if new_amount < 0:
            self.logger.warning(f"Insufficient {resource_type}: have {self._resources[resource_type]}, need {abs(amount)}")
            return False
        
        self._resources[resource_type] = new_amount
        
        if amount != 0:
            self.logger.debug(f"Added {amount} {resource_type} (total: {new_amount})")
        
        return True
    
    def subtract(self, resource_type: str, amount: int) -> bool:
        """
        Subtract resources from the pool
        
        Args:
            resource_type: Type of resource to subtract
            amount: Amount to subtract (must be positive)
            
        Returns:
            True if successful (enough resources available)
        """
        if amount < 0:
            self.logger.error("Subtract amount must be positive")
            return False
        
        return self.add(resource_type, -amount)
    
    def has_sufficient(self, resource_type: str, amount: int) -> bool:
        """
        Check if pool has sufficient resources
        
        Args:
            resource_type: Type of resource to check
            amount: Required amount
            
        Returns:
            True if sufficient resources are available
        """
        return self.get(resource_type) >= amount
    
    def has_sufficient_multiple(self, requirements: Dict[str, int]) -> bool:
        """
        Check if pool has sufficient resources for multiple requirements
        
        Args:
            requirements: Dictionary of resource requirements
            
        Returns:
            True if all requirements can be met
        """
        for resource_type, amount in requirements.items():
            if not self.has_sufficient(resource_type, amount):
                return False
        return True
    
    def has_resources(self, requirements: Dict[str, int]) -> bool:
        """
        Alias for has_sufficient_multiple for backward compatibility
        
        Args:
            requirements: Dictionary of resource requirements
            
        Returns:
            True if all requirements can be met
        """
        return self.has_sufficient_multiple(requirements)
    
    def consume_multiple(self, requirements: Dict[str, int]) -> bool:
        """
        Consume multiple resources atomically
        
        Args:
            requirements: Dictionary of resource requirements
            
        Returns:
            True if all resources were consumed successfully
        """
        # First check if we have sufficient resources
        if not self.has_sufficient_multiple(requirements):
            missing = []
            for resource_type, amount in requirements.items():
                if not self.has_sufficient(resource_type, amount):
                    have = self.get(resource_type)
                    missing.append(f"{resource_type}: need {amount}, have {have}")
            
            self.logger.warning(f"Insufficient resources: {', '.join(missing)}")
            return False
        
        # Consume all resources
        for resource_type, amount in requirements.items():
            self.subtract(resource_type, amount)
        
        self.logger.info(f"Consumed resources: {requirements}")
        return True
    
    def transfer_to(self, other_pool: 'ResourcePool', resource_type: str, amount: int) -> bool:
        """
        Transfer resources to another pool
        
        Args:
            other_pool: Destination resource pool
            resource_type: Type of resource to transfer
            amount: Amount to transfer
            
        Returns:
            True if transfer was successful
        """
        if not self.has_sufficient(resource_type, amount):
            self.logger.warning(f"Cannot transfer {amount} {resource_type} - insufficient resources")
            return False
        
        # Perform the transfer
        if self.subtract(resource_type, amount) and other_pool.add(resource_type, amount):
            self.logger.info(f"Transferred {amount} {resource_type}")
            return True
        else:
            # Rollback if something went wrong
            self.add(resource_type, amount)
            self.logger.error(f"Transfer failed for {amount} {resource_type}")
            return False
    
    def get_total_value(self, prices: Optional[Dict[str, int]] = None) -> int:
        """
        Calculate total value of all resources
        
        Args:
            prices: Optional price dictionary (defaults to MGR values)
            
        Returns:
            Total value in MGR equivalent
        """
        if prices is None:
            # Default MGR exchange rates
            prices = {
                "food": 2,
                "clean_water": 3,
                "scrap": 1,
                "medicine": 5,
                "mgr_rounds": 1
            }
        
        total_value = 0
        for resource_type, amount in self._resources.items():
            price = prices.get(resource_type, 0)
            total_value += amount * price
        
        return total_value
    
    def is_empty(self) -> bool:
        """Check if all resources are zero"""
        return all(amount == 0 for amount in self._resources.values())
    
    def get_critical_resources(self, thresholds: Optional[Dict[str, int]] = None) -> List[str]:
        """
        Get list of resources below critical thresholds
        
        Args:
            thresholds: Critical thresholds for each resource
            
        Returns:
            List of resource types below critical levels
        """
        if thresholds is None:
            thresholds = {
                "food": 20,
                "clean_water": 10,
                "scrap": 15,
                "medicine": 5,
                "mgr_rounds": 10
            }
        
        critical = []
        for resource_type, threshold in thresholds.items():
            if self.get(resource_type) < threshold:
                critical.append(resource_type)
        
        return critical
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary representation"""
        return self._resources.copy()
    
    def from_dict(self, data: Dict[str, int]):
        """Load from dictionary representation"""
        for resource_type, amount in data.items():
            if resource_type in self._resources:
                self._resources[resource_type] = max(0, amount)
    
    def __str__(self) -> str:
        """String representation of resource pool"""
        return f"Resources({', '.join(f'{k}:{v}' for k, v in self._resources.items())})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return f"ResourcePool({self._resources})"
    
    # Property accessors for common resources
    @property
    def food(self) -> int:
        return self._resources["food"]
    
    @property
    def clean_water(self) -> int:
        return self._resources["clean_water"]
    
    @property
    def scrap(self) -> int:
        return self._resources["scrap"]
    
    @property
    def medicine(self) -> int:
        return self._resources["medicine"]
    
    @property
    def mgr_rounds(self) -> int:
        return self._resources["mgr_rounds"]


class MGRScarcitySystem:
    """
    Military-Grade Rounds (MGR) scarcity and value system
    
    Features:
    - Dynamic MGR pricing based on scarcity
    - Regional availability variations
    - Black market mechanics
    - Quality degradation over time
    """
    
    def __init__(self):
        """Initialize MGR scarcity system"""
        self.logger = logging.getLogger(__name__)
        
        # Global MGR market state
        self.global_supply = 1000  # Total MGR in circulation
        self.base_price = 10  # Base price in resource units
        self.scarcity_multiplier = 1.0  # Price multiplier due to scarcity
        
        # Regional variations
        self.regional_availability: Dict[str, float] = {}  # Station -> availability multiplier
        
        # Black market
        self.black_market_active = False
        self.black_market_premium = 2.5  # 250% markup
        
        # Quality system
        self.quality_levels = {
            "pristine": {"multiplier": 1.5, "rarity": 0.05},
            "good": {"multiplier": 1.2, "rarity": 0.15},
            "standard": {"multiplier": 1.0, "rarity": 0.60},
            "worn": {"multiplier": 0.8, "rarity": 0.15},
            "damaged": {"multiplier": 0.5, "rarity": 0.05}
        }
        
        self.logger.info("MGR scarcity system initialized")
    
    def calculate_mgr_price(self, station: str, quantity: int = 1) -> int:
        """
        Calculate MGR price at a specific station
        
        Args:
            station: Station name
            quantity: Quantity being purchased
            
        Returns:
            Total price for the MGR
        """
        # Base price with scarcity multiplier
        unit_price = self.base_price * self.scarcity_multiplier
        
        # Regional availability affects price
        availability = self.regional_availability.get(station, 1.0)
        regional_multiplier = 2.0 - availability  # Lower availability = higher price
        
        # Quantity affects price (bulk discount/premium)
        if quantity > 10:
            quantity_multiplier = 0.9  # 10% bulk discount
        elif quantity > 50:
            quantity_multiplier = 0.8  # 20% bulk discount
        else:
            quantity_multiplier = 1.0
        
        # Black market premium
        market_multiplier = self.black_market_premium if self.black_market_active else 1.0
        
        final_price = unit_price * regional_multiplier * quantity_multiplier * market_multiplier * quantity
        
        return int(final_price)
    
    def consume_mgr_from_market(self, quantity: int):
        """Remove MGR from global supply, affecting scarcity"""
        self.global_supply = max(0, self.global_supply - quantity)
        
        # Update scarcity multiplier based on supply
        if self.global_supply < 200:
            self.scarcity_multiplier = 3.0  # Extreme scarcity
        elif self.global_supply < 500:
            self.scarcity_multiplier = 2.0  # High scarcity
        elif self.global_supply < 800:
            self.scarcity_multiplier = 1.5  # Moderate scarcity
        else:
            self.scarcity_multiplier = 1.0  # Normal availability
    
    def add_mgr_to_market(self, quantity: int):
        """Add MGR to global supply"""
        self.global_supply += quantity
        
        # Cap maximum supply
        self.global_supply = min(self.global_supply, 2000)
    
    def set_regional_availability(self, station: str, availability: float):
        """Set MGR availability for a specific station"""
        self.regional_availability[station] = max(0.1, min(2.0, availability))
    
    def activate_black_market(self):
        """Activate black market trading"""
        self.black_market_active = True
        self.logger.info("Black market activated - MGR prices increased")
    
    def deactivate_black_market(self):
        """Deactivate black market trading"""
        self.black_market_active = False
        self.logger.info("Black market deactivated - MGR prices normalized")
    
    def get_mgr_quality(self) -> Tuple[str, float]:
        """
        Get random MGR quality based on rarity
        
        Returns:
            Tuple of (quality_name, value_multiplier)
        """
        rand = random.random()
        cumulative = 0.0
        
        for quality, data in self.quality_levels.items():
            cumulative += data["rarity"]
            if rand <= cumulative:
                return quality, data["multiplier"]
        
        return "standard", 1.0
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get current MGR market status"""
        return {
            "global_supply": self.global_supply,
            "base_price": self.base_price,
            "scarcity_multiplier": self.scarcity_multiplier,
            "black_market_active": self.black_market_active,
            "scarcity_level": self._get_scarcity_level()
        }
    
    def _get_scarcity_level(self) -> str:
        """Get human-readable scarcity level"""
        if self.global_supply < 200:
            return "extreme"
        elif self.global_supply < 500:
            return "high"
        elif self.global_supply < 800:
            return "moderate"
        else:
            return "normal"


class ResourceGenerationSystem:
    """
    System for generating and consuming resources over time
    
    Features:
    - Turn-based resource generation
    - Population-based consumption
    - Infrastructure bonuses
    - Random events affecting production
    """
    
    def __init__(self):
        """Initialize resource generation system"""
        self.logger = logging.getLogger(__name__)
        
        # Base generation rates per population
        self.base_generation_rates = {
            "food": 0.8,  # Food per person per turn
            "clean_water": 0.6,
            "scrap": 0.4,
            "medicine": 0.1,
            "mgr_rounds": 0.02
        }
        
        # Base consumption rates per population
        self.base_consumption_rates = {
            "food": 1.0,  # Food consumed per person per turn
            "clean_water": 0.8,
            "medicine": 0.05
        }
        
        # Infrastructure bonuses
        self.infrastructure_bonuses = {
            "mushroom_farm": {"food": 2.0},
            "water_filter": {"clean_water": 1.5},
            "scrap_workshop": {"scrap": 1.8},
            "med_bay": {"medicine": 1.2},
            "market": {"mgr_rounds": 0.5}
        }
        
        self.logger.info("Resource generation system initialized")
    
    def calculate_generation(self, population: int, infrastructure: List[str], 
                           efficiency: float = 1.0) -> Dict[str, int]:
        """
        Calculate resource generation for a station
        
        Args:
            population: Station population
            infrastructure: List of infrastructure buildings
            efficiency: Efficiency multiplier (0.0 to 2.0)
            
        Returns:
            Dictionary of generated resources
        """
        generation = {}
        
        for resource, base_rate in self.base_generation_rates.items():
            # Base generation
            base_amount = population * base_rate
            
            # Infrastructure bonuses
            infrastructure_bonus = 1.0
            for building in infrastructure:
                if building in self.infrastructure_bonuses:
                    building_bonus = self.infrastructure_bonuses[building].get(resource, 0)
                    infrastructure_bonus += building_bonus
            
            # Apply efficiency and calculate final amount
            final_amount = int(base_amount * infrastructure_bonus * efficiency)
            generation[resource] = max(0, final_amount)
        
        return generation
    
    def calculate_consumption(self, population: int, morale: float = 0.5) -> Dict[str, int]:
        """
        Calculate resource consumption for a station
        
        Args:
            population: Station population
            morale: Station morale (affects consumption)
            
        Returns:
            Dictionary of consumed resources
        """
        consumption = {}
        
        # Morale affects consumption (low morale = higher consumption)
        morale_multiplier = 1.5 - morale  # 0.5 to 1.5 range
        
        for resource, base_rate in self.base_consumption_rates.items():
            base_amount = population * base_rate * morale_multiplier
            consumption[resource] = int(base_amount)
        
        return consumption
    
    def apply_random_event(self, generation: Dict[str, int], event_type: str) -> Dict[str, int]:
        """
        Apply random event effects to resource generation
        
        Args:
            generation: Base generation amounts
            event_type: Type of random event
            
        Returns:
            Modified generation amounts
        """
        event_effects = {
            "good_harvest": {"food": 1.5},
            "water_contamination": {"clean_water": 0.3},
            "scrap_find": {"scrap": 2.0},
            "medical_shortage": {"medicine": 0.5},
            "ammunition_cache": {"mgr_rounds": 3.0},
            "equipment_failure": {"scrap": 0.7, "clean_water": 0.8}
        }
        
        if event_type in event_effects:
            effects = event_effects[event_type]
            modified_generation = generation.copy()
            
            for resource, multiplier in effects.items():
                if resource in modified_generation:
                    modified_generation[resource] = int(modified_generation[resource] * multiplier)
            
            self.logger.info(f"Applied event {event_type} to resource generation")
            return modified_generation
        
        return generation


class ResourceMarket:
    """
    Global resource trading market with dynamic pricing
    
    Features:
    - Supply and demand mechanics
    - Price volatility
    - Regional price variations
    - Trade route effects
    """
    
    def __init__(self):
        """Initialize resource market"""
        self.logger = logging.getLogger(__name__)
        
        # Market data for each resource
        self.market_data: Dict[str, ResourceMarketData] = {}
        
        # Initialize market data
        self._initialize_market_data()
        
        # Trade history
        self.trade_history: List[ResourceTransaction] = []
        
        self.logger.info("Resource market initialized")
    
    def _initialize_market_data(self):
        """Initialize market data for all resources"""
        initial_data = {
            "food": ResourceMarketData("food", 2, 2, 1000, 800, 0.1, ResourceRarity.COMMON),
            "clean_water": ResourceMarketData("clean_water", 3, 3, 600, 700, 0.15, ResourceRarity.UNCOMMON),
            "scrap": ResourceMarketData("scrap", 1, 1, 1500, 1200, 0.05, ResourceRarity.COMMON),
            "medicine": ResourceMarketData("medicine", 5, 5, 200, 300, 0.25, ResourceRarity.RARE),
            "mgr_rounds": ResourceMarketData("mgr_rounds", 10, 10, 100, 150, 0.4, ResourceRarity.LEGENDARY)
        }
        
        self.market_data = initial_data
    
    def get_current_price(self, resource_type: str, quantity: int = 1) -> int:
        """
        Get current market price for a resource
        
        Args:
            resource_type: Type of resource
            quantity: Quantity being traded
            
        Returns:
            Total price for the quantity
        """
        if resource_type not in self.market_data:
            return 0
        
        market = self.market_data[resource_type]
        
        # Supply and demand affects price
        supply_demand_ratio = market.supply / max(1, market.demand)
        price_modifier = 2.0 - supply_demand_ratio  # Higher demand = higher price
        
        # Quantity affects price (large orders affect market)
        if quantity > market.supply * 0.1:  # Large order
            quantity_modifier = 1.2
        else:
            quantity_modifier = 1.0
        
        final_price = market.current_price * price_modifier * quantity_modifier * quantity
        
        return int(final_price)
    
    def execute_trade(self, resource_type: str, quantity: int, buyer: str, seller: str) -> bool:
        """
        Execute a trade transaction
        
        Args:
            resource_type: Type of resource
            quantity: Quantity to trade
            buyer: Buyer identifier
            seller: Seller identifier
            
        Returns:
            True if trade was successful
        """
        if resource_type not in self.market_data:
            return False
        
        market = self.market_data[resource_type]
        
        # Check if sufficient supply exists
        if quantity > market.supply:
            self.logger.warning(f"Insufficient supply for {quantity} {resource_type}")
            return False
        
        # Calculate price
        price = self.get_current_price(resource_type, quantity)
        
        # Update market data
        market.supply -= quantity
        market.demand = max(0, market.demand - quantity)
        
        # Update price based on new supply/demand
        self._update_market_price(resource_type)
        
        # Record transaction
        transaction = ResourceTransaction(
            resource_type=resource_type,
            amount=quantity,
            source=seller,
            destination=buyer,
            cost=price,
            transaction_id=f"trade_{len(self.trade_history)}"
        )
        
        self.trade_history.append(transaction)
        
        self.logger.info(f"Trade executed: {quantity} {resource_type} from {seller} to {buyer} for {price}")
        return True
    
    def _update_market_price(self, resource_type: str):
        """Update market price based on supply and demand"""
        if resource_type not in self.market_data:
            return
        
        market = self.market_data[resource_type]
        
        # Calculate new price based on supply/demand ratio
        supply_demand_ratio = market.supply / max(1, market.demand)
        
        if supply_demand_ratio < 0.5:  # High demand, low supply
            price_change = market.base_price * 0.1
        elif supply_demand_ratio > 2.0:  # Low demand, high supply
            price_change = -market.base_price * 0.1
        else:
            price_change = 0
        
        # Apply volatility
        volatility_change = random.uniform(-market.volatility, market.volatility) * market.base_price
        
        # Update current price
        new_price = market.current_price + price_change + volatility_change
        market.current_price = max(1, int(new_price))  # Minimum price of 1
    
    def add_supply(self, resource_type: str, quantity: int):
        """Add supply to the market"""
        if resource_type in self.market_data:
            self.market_data[resource_type].supply += quantity
    
    def add_demand(self, resource_type: str, quantity: int):
        """Add demand to the market"""
        if resource_type in self.market_data:
            self.market_data[resource_type].demand += quantity
    
    def get_market_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all market data"""
        summary = {}
        
        for resource_type, market in self.market_data.items():
            summary[resource_type] = {
                "current_price": market.current_price,
                "base_price": market.base_price,
                "supply": market.supply,
                "demand": market.demand,
                "rarity": market.rarity.value,
                "price_trend": "up" if market.current_price > market.base_price else "down"
            }
        
        return summary