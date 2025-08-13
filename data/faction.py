"""
Faction System with Government Types and Unique Mechanics
Represents different Metro factions with their ideologies and special abilities
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

from data.resources import ResourcePool


class GovernmentType(Enum):
    """Types of government systems"""
    COMMUNIST = "communist"
    FASCIST = "fascist"
    OLIGARCHY = "oligarchy"
    REPUBLIC = "republic"
    THEOCRACY = "theocracy"
    ANARCHIST = "anarchist"
    MILITARY = "military"


class Ideology(Enum):
    """Political ideologies"""
    STALINIST = "stalinist"
    NAZI = "nazi"
    CAPITALIST = "capitalist"
    DEMOCRATIC = "democratic"
    ORTHODOX = "orthodox"
    LIBERTARIAN = "libertarian"
    MILITARIST = "militarist"


@dataclass
class FactionBonus:
    """Represents a faction-specific bonus or penalty"""
    name: str
    description: str
    resource_modifiers: Dict[str, float]  # Resource production/consumption modifiers
    combat_modifier: float = 0.0
    diplomacy_modifier: float = 0.0
    trade_modifier: float = 0.0
    population_modifier: float = 0.0


class FactionMechanic:
    """Base class for faction-specific mechanics"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.active = True
    
    def apply_effect(self, faction: 'Faction', game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the mechanic's effect (override in subclasses)"""
        return {"success": True, "message": f"{self.name} applied"}
    
    def can_activate(self, faction: 'Faction', game_state: Dict[str, Any]) -> bool:
        """Check if mechanic can be activated"""
        return self.active


class CommissariatMechanic(FactionMechanic):
    """Red Line's Commissariat system - political officers boost morale but consume resources"""
    
    def __init__(self):
        super().__init__(
            "Commissariat",
            "Political officers boost station morale but require additional food"
        )
        self.commissars_deployed = 0
        self.max_commissars = 5
    
    def apply_effect(self, faction: 'Faction', game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy commissars to boost morale"""
        controlled_stations = game_state.get("controlled_stations", [])
        
        if self.commissars_deployed >= self.max_commissars:
            return {"success": False, "message": "Maximum commissars already deployed"}
        
        if not faction.resources.has_resources({"food": 10}):
            return {"success": False, "message": "Insufficient food for commissar deployment"}
        
        # Deploy commissar
        faction.resources.subtract("food", 10)
        self.commissars_deployed += 1
        
        # Boost morale at all controlled stations
        morale_boost = 15
        stations_affected = min(len(controlled_stations), self.commissars_deployed)
        
        return {
            "success": True,
            "message": f"Commissar deployed. +{morale_boost} morale at {stations_affected} stations",
            "effects": {
                "morale_boost": morale_boost,
                "stations_affected": stations_affected,
                "food_cost": 10
            }
        }


class PurityDoctrineMechanic(FactionMechanic):
    """Fourth Reich's Purity Doctrine - population control and military bonuses"""
    
    def __init__(self):
        super().__init__(
            "Purity Doctrine",
            "Strict population control provides military bonuses but reduces growth"
        )
        self.purity_level = 0.5  # 0.0 to 1.0
    
    def apply_effect(self, faction: 'Faction', game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply purity doctrine effects"""
        # Military bonus based on purity level
        military_bonus = int(self.purity_level * 30)
        
        # Population growth penalty
        growth_penalty = int(self.purity_level * 20)
        
        return {
            "success": True,
            "message": f"Purity Doctrine: +{military_bonus}% military strength, -{growth_penalty}% population growth",
            "effects": {
                "military_bonus": military_bonus,
                "population_penalty": growth_penalty,
                "purity_level": self.purity_level
            }
        }
    
    def increase_purity(self, amount: float = 0.1):
        """Increase purity level"""
        self.purity_level = min(1.0, self.purity_level + amount)
    
    def decrease_purity(self, amount: float = 0.1):
        """Decrease purity level"""
        self.purity_level = max(0.0, self.purity_level - amount)


class TollSystemMechanic(FactionMechanic):
    """Hanza's Toll System - collect MGR from trade routes"""
    
    def __init__(self):
        super().__init__(
            "Toll System",
            "Collect tolls from trade routes passing through Hanza territory"
        )
        self.toll_rate = 0.15  # 15% of trade value
        self.total_collected = 0
    
    def apply_effect(self, faction: 'Faction', game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Collect tolls from active trade routes"""
        active_trades = game_state.get("active_trades", [])
        controlled_stations = game_state.get("controlled_stations", [])
        
        toll_collected = 0
        trades_affected = 0
        
        for trade in active_trades:
            # Check if trade route passes through Hanza territory
            origin = trade.get("origin")
            destination = trade.get("destination")
            
            if origin in controlled_stations or destination in controlled_stations:
                trade_value = trade.get("value", 0)
                toll = int(trade_value * self.toll_rate)
                
                if toll > 0:
                    faction.resources.add("mgr_rounds", toll)
                    toll_collected += toll
                    trades_affected += 1
        
        self.total_collected += toll_collected
        
        return {
            "success": True,
            "message": f"Collected {toll_collected} MGR in tolls from {trades_affected} trades",
            "effects": {
                "mgr_collected": toll_collected,
                "trades_affected": trades_affected,
                "total_collected": self.total_collected
            }
        }


class CouncilDemocracyMechanic(FactionMechanic):
    """Polis's Council Democracy - democratic decisions boost efficiency"""
    
    def __init__(self):
        super().__init__(
            "Council Democracy",
            "Democratic decision-making improves efficiency but slows major changes"
        )
        self.council_approval = 0.7  # 0.0 to 1.0
        self.pending_decisions = []
    
    def apply_effect(self, faction: 'Faction', game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply democratic efficiency bonuses"""
        # Efficiency bonus based on council approval
        efficiency_bonus = int(self.council_approval * 25)
        
        # Process pending decisions
        decisions_processed = len(self.pending_decisions)
        self.pending_decisions.clear()
        
        return {
            "success": True,
            "message": f"Council Democracy: +{efficiency_bonus}% efficiency, {decisions_processed} decisions processed",
            "effects": {
                "efficiency_bonus": efficiency_bonus,
                "council_approval": self.council_approval,
                "decisions_processed": decisions_processed
            }
        }
    
    def add_decision(self, decision: str):
        """Add a decision to the council queue"""
        self.pending_decisions.append(decision)
    
    def vote_on_decision(self, approve: bool):
        """Vote on a pending decision"""
        if approve:
            self.council_approval = min(1.0, self.council_approval + 0.05)
        else:
            self.council_approval = max(0.0, self.council_approval - 0.1)


class Faction:
    """
    Represents a Metro faction with government, ideology, and unique mechanics
    
    Features:
    - Government type and ideology system
    - Faction-specific bonuses and penalties
    - Unique mechanics for each major faction
    - Resource management and population control
    - Diplomatic relationships and trade preferences
    """
    
    def __init__(self, name: str, government: GovernmentType, ideology: Ideology):
        """
        Initialize faction
        
        Args:
            name: Faction name
            government: Government type
            ideology: Political ideology
        """
        self.name = name
        self.government = government
        self.ideology = ideology
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Resources and population
        self.resources = ResourcePool()
        self.total_population = 0
        self.controlled_stations: List[str] = []
        
        # Faction characteristics
        self.stability = 0.7  # 0.0 to 1.0
        self.militarism = 0.5  # 0.0 to 1.0
        self.expansionism = 0.5  # 0.0 to 1.0
        self.isolationism = 0.3  # 0.0 to 1.0
        
        # Bonuses and mechanics
        self.bonuses: List[FactionBonus] = []
        self.mechanics: List[FactionMechanic] = []
        
        # Initialize faction-specific features
        self._initialize_faction_features()
        
        self.logger.info(f"Faction {name} initialized with {government.value} government and {ideology.value} ideology")
    
    def _initialize_faction_features(self):
        """Initialize faction-specific bonuses and mechanics"""
        # Red Line (Stalinist Communist)
        if self.name == "Red Line":
            self.bonuses.append(FactionBonus(
                name="Revolutionary Fervor",
                description="Higher morale and military recruitment",
                resource_modifiers={"food": -0.1},  # 10% more food consumption
                combat_modifier=0.15,  # 15% combat bonus
                population_modifier=0.1  # 10% population growth
            ))
            self.mechanics.append(CommissariatMechanic())
            self.militarism = 0.8
            self.expansionism = 0.7
        
        # Fourth Reich (Nazi Fascist)
        elif self.name == "Fourth Reich":
            self.bonuses.append(FactionBonus(
                name="Military Discipline",
                description="Superior military organization and equipment",
                resource_modifiers={"scrap": 0.2},  # 20% more scrap production
                combat_modifier=0.25,  # 25% combat bonus
                population_modifier=-0.15  # 15% population growth penalty
            ))
            self.mechanics.append(PurityDoctrineMechanic())
            self.militarism = 0.9
            self.expansionism = 0.8
            self.isolationism = 0.6
        
        # Hanza (Capitalist Oligarchy)
        elif self.name == "Hanza":
            self.bonuses.append(FactionBonus(
                name="Trade Network",
                description="Enhanced trade capabilities and MGR generation",
                resource_modifiers={"mgr_rounds": 0.3},  # 30% more MGR
                trade_modifier=0.25,  # 25% trade bonus
                diplomacy_modifier=0.1  # 10% diplomacy bonus
            ))
            self.mechanics.append(TollSystemMechanic())
            self.militarism = 0.3
            self.expansionism = 0.4
        
        # Polis (Democratic Republic)
        elif self.name == "Polis":
            self.bonuses.append(FactionBonus(
                name="Democratic Efficiency",
                description="Better resource management and research",
                resource_modifiers={"medicine": 0.2, "clean_water": 0.15},
                diplomacy_modifier=0.2,  # 20% diplomacy bonus
                population_modifier=0.05  # 5% population growth
            ))
            self.mechanics.append(CouncilDemocracyMechanic())
            self.militarism = 0.2
            self.expansionism = 0.3
            self.isolationism = 0.1
        
        # Rangers (Military Republic)
        elif self.name == "Rangers":
            self.bonuses.append(FactionBonus(
                name="Elite Training",
                description="Superior scouting and survival skills",
                resource_modifiers={"medicine": 0.1, "food": 0.1},
                combat_modifier=0.1,  # 10% combat bonus
                diplomacy_modifier=0.15  # 15% diplomacy bonus (neutral mediators)
            ))
            self.militarism = 0.6
            self.expansionism = 0.2
            self.isolationism = 0.2
    
    def process_turn(self, turn_number: int, game_state: Dict[str, Any]):
        """Process faction turn and apply mechanics"""
        # Apply faction bonuses to resource generation
        self._apply_resource_bonuses()
        
        # Process faction mechanics
        for mechanic in self.mechanics:
            if mechanic.can_activate(self, game_state):
                result = mechanic.apply_effect(self, game_state)
                if result["success"]:
                    self.logger.debug(f"Applied {mechanic.name}: {result['message']}")
        
        # Update faction stability based on conditions
        self._update_stability(game_state)
    
    def _apply_resource_bonuses(self):
        """Apply faction bonuses to resource generation"""
        for bonus in self.bonuses:
            for resource, modifier in bonus.resource_modifiers.items():
                if modifier > 0:
                    # Positive modifier = bonus production
                    current_amount = getattr(self.resources, resource, 0)
                    bonus_amount = int(current_amount * modifier)
                    self.resources.add(resource, bonus_amount)
    
    def _update_stability(self, game_state: Dict[str, Any]):
        """Update faction stability based on current conditions"""
        # Base stability change
        stability_change = 0.0
        
        # Population happiness affects stability
        total_morale = game_state.get("total_morale", 50)
        if total_morale > 70:
            stability_change += 0.02
        elif total_morale < 30:
            stability_change -= 0.03
        
        # Resource scarcity affects stability
        critical_resources = ["food", "clean_water", "medicine"]
        for resource in critical_resources:
            amount = getattr(self.resources, resource, 0)
            if amount < 10:  # Critical shortage
                stability_change -= 0.01
        
        # Military losses affect stability
        recent_losses = game_state.get("recent_military_losses", 0)
        if recent_losses > 0:
            stability_change -= recent_losses * 0.005
        
        # Apply stability change
        self.stability = max(0.0, min(1.0, self.stability + stability_change))
    
    def get_combat_modifier(self) -> float:
        """Get total combat modifier from bonuses"""
        total_modifier = 0.0
        for bonus in self.bonuses:
            total_modifier += bonus.combat_modifier
        
        # Stability affects combat effectiveness
        stability_modifier = (self.stability - 0.5) * 0.2
        
        return total_modifier + stability_modifier
    
    def get_diplomacy_modifier(self) -> float:
        """Get total diplomacy modifier from bonuses"""
        total_modifier = 0.0
        for bonus in self.bonuses:
            total_modifier += bonus.diplomacy_modifier
        
        # Stability affects diplomatic effectiveness
        stability_modifier = (self.stability - 0.5) * 0.1
        
        return total_modifier + stability_modifier
    
    def get_trade_modifier(self) -> float:
        """Get total trade modifier from bonuses"""
        total_modifier = 0.0
        for bonus in self.bonuses:
            total_modifier += bonus.trade_modifier
        
        return total_modifier
    
    def activate_mechanic(self, mechanic_name: str, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Manually activate a faction mechanic"""
        for mechanic in self.mechanics:
            if mechanic.name == mechanic_name:
                if mechanic.can_activate(self, game_state):
                    return mechanic.apply_effect(self, game_state)
                else:
                    return {"success": False, "message": f"{mechanic_name} cannot be activated"}
        
        return {"success": False, "message": f"Mechanic {mechanic_name} not found"}
    
    def get_faction_info(self) -> Dict[str, Any]:
        """Get comprehensive faction information"""
        return {
            "name": self.name,
            "government": self.government.value,
            "ideology": self.ideology.value,
            "stability": self.stability,
            "militarism": self.militarism,
            "expansionism": self.expansionism,
            "isolationism": self.isolationism,
            "total_population": self.total_population,
            "controlled_stations": len(self.controlled_stations),
            "resources": {
                "food": self.resources.food,
                "clean_water": self.resources.clean_water,
                "scrap": self.resources.scrap,
                "medicine": self.resources.medicine,
                "mgr_rounds": self.resources.mgr_rounds
            },
            "bonuses": [
                {
                    "name": bonus.name,
                    "description": bonus.description,
                    "combat_modifier": bonus.combat_modifier,
                    "diplomacy_modifier": bonus.diplomacy_modifier,
                    "trade_modifier": bonus.trade_modifier
                }
                for bonus in self.bonuses
            ],
            "mechanics": [
                {
                    "name": mechanic.name,
                    "description": mechanic.description,
                    "active": mechanic.active
                }
                for mechanic in self.mechanics
            ]
        }
    
    def get_government_effects(self) -> Dict[str, Any]:
        """Get effects of the faction's government type"""
        government_effects = {
            GovernmentType.COMMUNIST: {
                "resource_sharing": True,
                "military_bonus": 0.1,
                "population_control": 0.8,
                "stability_requirement": 0.6
            },
            GovernmentType.FASCIST: {
                "military_bonus": 0.2,
                "population_control": 0.9,
                "expansion_bonus": 0.15,
                "stability_requirement": 0.7
            },
            GovernmentType.OLIGARCHY: {
                "trade_bonus": 0.2,
                "mgr_bonus": 0.25,
                "corruption_penalty": 0.1,
                "stability_requirement": 0.5
            },
            GovernmentType.REPUBLIC: {
                "diplomacy_bonus": 0.15,
                "research_bonus": 0.1,
                "efficiency_bonus": 0.1,
                "stability_requirement": 0.4
            },
            GovernmentType.MILITARY: {
                "military_bonus": 0.15,
                "discipline_bonus": 0.1,
                "expansion_bonus": 0.1,
                "stability_requirement": 0.6
            }
        }
        
        return government_effects.get(self.government, {})


class FactionManager:
    """Manages all factions in the game"""
    
    def __init__(self):
        """Initialize faction manager"""
        self.factions: Dict[str, Faction] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize major Metro factions
        self._initialize_factions()
    
    def _initialize_factions(self):
        """Initialize all major Metro factions"""
        faction_configs = [
            ("Red Line", GovernmentType.COMMUNIST, Ideology.STALINIST),
            ("Fourth Reich", GovernmentType.FASCIST, Ideology.NAZI),
            ("Hanza", GovernmentType.OLIGARCHY, Ideology.CAPITALIST),
            ("Polis", GovernmentType.REPUBLIC, Ideology.DEMOCRATIC),
            ("Rangers", GovernmentType.MILITARY, Ideology.MILITARIST)
        ]
        
        for name, government, ideology in faction_configs:
            faction = Faction(name, government, ideology)
            self.factions[name] = faction
        
        self.logger.info(f"Initialized {len(self.factions)} factions")
    
    def get_faction(self, name: str) -> Optional[Faction]:
        """Get faction by name"""
        return self.factions.get(name)
    
    def process_all_factions_turn(self, turn_number: int, game_state: Dict[str, Any]):
        """Process turn for all factions"""
        for faction in self.factions.values():
            faction.process_turn(turn_number, game_state)
    
    def get_all_factions_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information for all factions"""
        return {
            name: faction.get_faction_info()
            for name, faction in self.factions.items()
        }