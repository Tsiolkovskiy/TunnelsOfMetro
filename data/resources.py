"""
Resource Management System
Handles all resource types and transactions in the Metro universe
"""

import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass


@dataclass
class ResourceTransaction:
    """Represents a resource transaction between entities"""
    resource_type: str
    amount: int
    source: str
    destination: str
    cost: int = 0
    timestamp: Optional[str] = None


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
        
        # Initialize all resource types to zero
        self._resources = {
            "food": 0,
            "clean_water": 0,
            "scrap": 0,
            "medicine": 0,
            "mgr_rounds": 0
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