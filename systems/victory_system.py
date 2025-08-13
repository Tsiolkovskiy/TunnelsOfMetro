"""
Victory Condition System
Tracks multiple victory paths and determines game end conditions
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field

from data.station import Station
from systems.metro_map import MetroMap


class VictoryType(Enum):
    """Types of victory conditions"""
    POLITICAL = "political"
    MILITARY = "military"
    ECONOMIC = "economic"
    SURVIVAL = "survival"
    TECHNOLOGICAL = "technological"


class VictoryStatus(Enum):
    """Status of victory condition progress"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    NEAR_COMPLETION = "near_completion"
    ACHIEVED = "achieved"
    FAILED = "failed"


@dataclass
class VictoryCondition:
    """Represents a specific victory condition"""
    victory_type: VictoryType
    name: str
    description: str
    requirements: Dict[str, Any]
    progress_thresholds: Dict[str, float] = field(default_factory=dict)
    current_progress: float = 0.0
    status: VictoryStatus = VictoryStatus.NOT_STARTED
    turn_achieved: Optional[int] = None
    
    def get_progress_percentage(self) -> float:
        """Get progress as percentage (0-100)"""
        return min(100.0, self.current_progress * 100.0)


@dataclass
class VictoryResult:
    """Result of a victory condition check"""
    victory_type: VictoryType
    achieved: bool
    progress: float
    status: VictoryStatus
    description: str
    turn_achieved: Optional[int] = None


class VictorySystem:
    """
    Complete victory condition tracking system
    
    Features:
    - Multiple victory paths (political, military, economic, survival, technological)
    - Progress tracking for each victory condition
    - Victory detection and game end mechanics
    - Dynamic victory requirements based on game state
    - Victory condition interactions and conflicts
    """
    
    def __init__(self, metro_map: MetroMap):
        """
        Initialize victory system
        
        Args:
            metro_map: MetroMap instance
        """
        self.metro_map = metro_map
        self.logger = logging.getLogger(__name__)
        
        # Victory conditions
        self.victory_conditions: Dict[VictoryType, VictoryCondition] = {}
        
        # Victory tracking
        self.game_ended = False
        self.victory_achieved: Optional[VictoryType] = None
        self.victory_turn: Optional[int] = None
        self.victory_score = 0
        
        # Progress history
        self.progress_history: List[Dict[str, Any]] = []
        
        # Initialize victory conditions
        self._initialize_victory_conditions()
        
        self.logger.info("Victory system initialized with {} victory paths".format(len(self.victory_conditions)))
    
    def _initialize_victory_conditions(self):
        """Initialize all victory conditions"""
        
        # Political Victory - Unite the Metro through diplomacy
        self.victory_conditions[VictoryType.POLITICAL] = VictoryCondition(
            victory_type=VictoryType.POLITICAL,
            name="Metro Unification",
            description="Unite all major factions under a single banner through diplomacy and alliance",
            requirements={
                "allied_factions": 4,  # Must have 4+ allied factions
                "controlled_stations": 12,  # Control 80% of stations
                "diplomatic_agreements": 8,  # Multiple diplomatic successes
                "reputation": 75,  # High reputation across Metro
                "turns_maintained": 5  # Maintain unity for 5 turns
            },
            progress_thresholds={
                "early": 0.25,  # 25% progress
                "mid": 0.50,    # 50% progress
                "late": 0.75    # 75% progress
            }
        )
        
        # Military Victory - Conquer the Metro through force
        self.victory_conditions[VictoryType.MILITARY] = VictoryCondition(
            victory_type=VictoryType.MILITARY,
            name="Metro Conquest",
            description="Conquer and control the majority of Metro stations through military might",
            requirements={
                "controlled_stations": 11,  # Control 70%+ of stations
                "military_strength": 500,   # Strong military force
                "battles_won": 15,         # Proven military success
                "enemy_factions_defeated": 3,  # Eliminate major threats
                "fortified_stations": 6    # Secure key positions
            },
            progress_thresholds={
                "early": 0.30,
                "mid": 0.60,
                "late": 0.85
            }
        )
        
        # Economic Victory - Control Metro's economy and trade
        self.victory_conditions[VictoryType.ECONOMIC] = VictoryCondition(
            victory_type=VictoryType.ECONOMIC,
            name="Economic Dominance",
            description="Control the Metro's economy through trade networks and resource monopolies",
            requirements={
                "mgr_reserves": 1000,      # Massive MGR stockpile
                "trade_routes": 10,        # Extensive trade network
                "market_stations": 5,      # Control key markets
                "resource_production": 200, # High production capacity
                "trade_agreements": 12,    # Dominant trade position
                "economic_influence": 80   # Economic control percentage
            },
            progress_thresholds={
                "early": 0.20,
                "mid": 0.45,
                "late": 0.70
            }
        )
        
        # Survival Victory - Outlast all challenges and threats
        self.victory_conditions[VictoryType.SURVIVAL] = VictoryCondition(
            victory_type=VictoryType.SURVIVAL,
            name="Metro Survival",
            description="Survive the harsh Metro environment and outlast all major threats",
            requirements={
                "turns_survived": 100,     # Survive 100 turns
                "population_maintained": 1000,  # Keep population stable
                "resource_security": 80,   # Maintain resource security
                "crisis_survived": 10,     # Survive major crises
                "infrastructure_level": 50, # Developed infrastructure
                "faction_stability": 75    # Stable faction relations
            },
            progress_thresholds={
                "early": 0.25,
                "mid": 0.50,
                "late": 0.75
            }
        )
        
        # Technological Victory - Advance Metro civilization through knowledge
        self.victory_conditions[VictoryType.TECHNOLOGICAL] = VictoryCondition(
            victory_type=VictoryType.TECHNOLOGICAL,
            name="Technological Renaissance",
            description="Lead the Metro into a new age through technological advancement and knowledge",
            requirements={
                "libraries_built": 4,      # Centers of learning
                "research_projects": 8,    # Scientific advancement
                "knowledge_preserved": 100, # Preserve pre-war knowledge
                "technology_shared": 6,    # Share tech with factions
                "anomaly_research": 3,     # Study Metro anomalies
                "surface_contact": True    # Re-establish surface contact
            },
            progress_thresholds={
                "early": 0.15,
                "mid": 0.40,
                "late": 0.65
            }
        )
    
    def check_victory_conditions(self, current_turn: int, game_state: Dict[str, Any]) -> List[VictoryResult]:
        """
        Check all victory conditions and update progress
        
        Args:
            current_turn: Current game turn
            game_state: Current game state information
            
        Returns:
            List of victory results
        """
        results = []
        
        for victory_type, condition in self.victory_conditions.items():
            result = self._check_single_victory_condition(condition, current_turn, game_state)
            results.append(result)
            
            # Update condition progress and status
            condition.current_progress = result.progress
            condition.status = result.status
            
            if result.achieved and not self.game_ended:
                condition.turn_achieved = current_turn
                self._achieve_victory(victory_type, current_turn, game_state)
        
        # Store progress history
        self._record_progress_history(current_turn, results)
        
        return results
    
    def _check_single_victory_condition(self, condition: VictoryCondition, current_turn: int, game_state: Dict[str, Any]) -> VictoryResult:
        """Check a single victory condition"""
        progress = 0.0
        status = VictoryStatus.NOT_STARTED
        achieved = False
        
        if condition.victory_type == VictoryType.POLITICAL:
            progress = self._calculate_political_progress(condition, game_state)
        elif condition.victory_type == VictoryType.MILITARY:
            progress = self._calculate_military_progress(condition, game_state)
        elif condition.victory_type == VictoryType.ECONOMIC:
            progress = self._calculate_economic_progress(condition, game_state)
        elif condition.victory_type == VictoryType.SURVIVAL:
            progress = self._calculate_survival_progress(condition, current_turn, game_state)
        elif condition.victory_type == VictoryType.TECHNOLOGICAL:
            progress = self._calculate_technological_progress(condition, game_state)
        
        # Determine status based on progress
        if progress >= 1.0:
            status = VictoryStatus.ACHIEVED
            achieved = True
        elif progress >= condition.progress_thresholds.get("late", 0.75):
            status = VictoryStatus.NEAR_COMPLETION
        elif progress >= condition.progress_thresholds.get("early", 0.25):
            status = VictoryStatus.IN_PROGRESS
        else:
            status = VictoryStatus.NOT_STARTED
        
        return VictoryResult(
            victory_type=condition.victory_type,
            achieved=achieved,
            progress=progress,
            status=status,
            description=condition.description,
            turn_achieved=condition.turn_achieved
        )
    
    def _calculate_political_progress(self, condition: VictoryCondition, game_state: Dict[str, Any]) -> float:
        """Calculate progress toward political victory"""
        requirements = condition.requirements
        progress_components = []
        
        # Allied factions progress
        stats = game_state.get("statistics", {})
        diplomatic_agreements = stats.get("diplomatic_agreements", 0)
        allied_factions = min(diplomatic_agreements / requirements["allied_factions"], 1.0)
        progress_components.append(allied_factions * 0.3)  # 30% weight
        
        # Controlled stations progress
        controlled_stations = len(game_state.get("controlled_stations", []))
        station_control = min(controlled_stations / requirements["controlled_stations"], 1.0)
        progress_components.append(station_control * 0.25)  # 25% weight
        
        # Diplomatic success progress
        diplomatic_success = min(diplomatic_agreements / requirements["diplomatic_agreements"], 1.0)
        progress_components.append(diplomatic_success * 0.25)  # 25% weight
        
        # Reputation progress (simulated)
        reputation = min(stats.get("diplomatic_agreements", 0) * 10, requirements["reputation"])
        reputation_progress = reputation / requirements["reputation"]
        progress_components.append(reputation_progress * 0.2)  # 20% weight
        
        return sum(progress_components)
    
    def _calculate_military_progress(self, condition: VictoryCondition, game_state: Dict[str, Any]) -> float:
        """Calculate progress toward military victory"""
        requirements = condition.requirements
        progress_components = []
        
        # Controlled stations progress
        controlled_stations = len(game_state.get("controlled_stations", []))
        station_control = min(controlled_stations / requirements["controlled_stations"], 1.0)
        progress_components.append(station_control * 0.35)  # 35% weight
        
        # Military strength progress
        stats = game_state.get("statistics", {})
        military_strength = stats.get("total_military_strength", 0)
        strength_progress = min(military_strength / requirements["military_strength"], 1.0)
        progress_components.append(strength_progress * 0.25)  # 25% weight
        
        # Battles won progress
        battles_won = stats.get("battles_won", 0)
        battle_progress = min(battles_won / requirements["battles_won"], 1.0)
        progress_components.append(battle_progress * 0.25)  # 25% weight
        
        # Fortified stations progress (simulated)
        fortified_stations = min(controlled_stations // 2, requirements["fortified_stations"])
        fortification_progress = fortified_stations / requirements["fortified_stations"]
        progress_components.append(fortification_progress * 0.15)  # 15% weight
        
        return sum(progress_components)
    
    def _calculate_economic_progress(self, condition: VictoryCondition, game_state: Dict[str, Any]) -> float:
        """Calculate progress toward economic victory"""
        requirements = condition.requirements
        progress_components = []
        
        # MGR reserves progress
        player_resources = game_state.get("player_resources")
        if player_resources:
            mgr_reserves = getattr(player_resources, "mgr_rounds", 0)
            mgr_progress = min(mgr_reserves / requirements["mgr_reserves"], 1.0)
            progress_components.append(mgr_progress * 0.3)  # 30% weight
        
        # Trade routes progress
        stats = game_state.get("statistics", {})
        trades_completed = stats.get("trades_completed", 0)
        trade_progress = min(trades_completed / requirements["trade_routes"], 1.0)
        progress_components.append(trade_progress * 0.25)  # 25% weight
        
        # Resource production progress
        production_summary = game_state.get("production_summary", {})
        total_production = production_summary.get("total_production", {})
        production_value = sum(total_production.values()) if total_production else 0
        production_progress = min(production_value / requirements["resource_production"], 1.0)
        progress_components.append(production_progress * 0.25)  # 25% weight
        
        # Economic influence (simulated)
        controlled_stations = len(game_state.get("controlled_stations", []))
        economic_influence = min(controlled_stations * 5, requirements["economic_influence"])
        influence_progress = economic_influence / requirements["economic_influence"]
        progress_components.append(influence_progress * 0.2)  # 20% weight
        
        return sum(progress_components)
    
    def _calculate_survival_progress(self, condition: VictoryCondition, current_turn: int, game_state: Dict[str, Any]) -> float:
        """Calculate progress toward survival victory"""
        requirements = condition.requirements
        progress_components = []
        
        # Turns survived progress
        turns_progress = min(current_turn / requirements["turns_survived"], 1.0)
        progress_components.append(turns_progress * 0.4)  # 40% weight
        
        # Population maintained progress
        stats = game_state.get("statistics", {})
        total_population = stats.get("total_population", 0)
        population_progress = min(total_population / requirements["population_maintained"], 1.0)
        progress_components.append(population_progress * 0.25)  # 25% weight
        
        # Resource security progress (simulated based on production)
        production_summary = game_state.get("production_summary", {})
        net_production = production_summary.get("net_production", {})
        resource_security = 0
        if net_production:
            positive_resources = sum(1 for amount in net_production.values() if amount > 0)
            resource_security = min(positive_resources * 20, requirements["resource_security"])
        security_progress = resource_security / requirements["resource_security"]
        progress_components.append(security_progress * 0.2)  # 20% weight
        
        # Infrastructure level progress
        controlled_stations = len(game_state.get("controlled_stations", []))
        infrastructure_level = min(controlled_stations * 3, requirements["infrastructure_level"])
        infrastructure_progress = infrastructure_level / requirements["infrastructure_level"]
        progress_components.append(infrastructure_progress * 0.15)  # 15% weight
        
        return sum(progress_components)
    
    def _calculate_technological_progress(self, condition: VictoryCondition, game_state: Dict[str, Any]) -> float:
        """Calculate progress toward technological victory"""
        requirements = condition.requirements
        progress_components = []
        
        # Libraries built progress (simulated)
        controlled_stations = len(game_state.get("controlled_stations", []))
        libraries_built = min(controlled_stations // 3, requirements["libraries_built"])
        library_progress = libraries_built / requirements["libraries_built"]
        progress_components.append(library_progress * 0.3)  # 30% weight
        
        # Research projects progress (simulated based on turns and libraries)
        research_projects = min(libraries_built * 2, requirements["research_projects"])
        research_progress = research_projects / requirements["research_projects"]
        progress_components.append(research_progress * 0.25)  # 25% weight
        
        # Knowledge preserved progress (simulated)
        stats = game_state.get("statistics", {})
        knowledge_preserved = min(stats.get("diplomatic_agreements", 0) * 10, requirements["knowledge_preserved"])
        knowledge_progress = knowledge_preserved / requirements["knowledge_preserved"]
        progress_components.append(knowledge_progress * 0.2)  # 20% weight
        
        # Technology shared progress (simulated)
        technology_shared = min(stats.get("diplomatic_agreements", 0), requirements["technology_shared"])
        tech_share_progress = technology_shared / requirements["technology_shared"]
        progress_components.append(tech_share_progress * 0.15)  # 15% weight
        
        # Anomaly research progress (simulated)
        anomaly_research = min(controlled_stations // 5, requirements["anomaly_research"])
        anomaly_progress = anomaly_research / requirements["anomaly_research"]
        progress_components.append(anomaly_progress * 0.1)  # 10% weight
        
        return sum(progress_components)
    
    def _achieve_victory(self, victory_type: VictoryType, current_turn: int, game_state: Dict[str, Any]):
        """Handle victory achievement"""
        if self.game_ended:
            return  # Only allow one victory
        
        self.game_ended = True
        self.victory_achieved = victory_type
        self.victory_turn = current_turn
        self.victory_score = self._calculate_victory_score(victory_type, current_turn, game_state)
        
        self.logger.info(f"Victory achieved: {victory_type.value} on turn {current_turn} with score {self.victory_score}")
    
    def _calculate_victory_score(self, victory_type: VictoryType, current_turn: int, game_state: Dict[str, Any]) -> int:
        """Calculate final victory score"""
        base_score = 1000
        
        # Turn bonus (earlier victory = higher score)
        turn_bonus = max(0, 200 - current_turn * 2)
        
        # Victory type bonuses
        type_bonuses = {
            VictoryType.POLITICAL: 150,    # Diplomatic achievement
            VictoryType.MILITARY: 100,     # Military conquest
            VictoryType.ECONOMIC: 125,     # Economic dominance
            VictoryType.SURVIVAL: 200,     # Ultimate challenge
            VictoryType.TECHNOLOGICAL: 175 # Knowledge advancement
        }
        
        type_bonus = type_bonuses.get(victory_type, 0)
        
        # Performance bonuses
        stats = game_state.get("statistics", {})
        performance_bonus = 0
        performance_bonus += stats.get("stations_controlled", 0) * 10
        performance_bonus += stats.get("total_population", 0) // 10
        performance_bonus += stats.get("battles_won", 0) * 15
        performance_bonus += stats.get("trades_completed", 0) * 5
        performance_bonus += stats.get("diplomatic_agreements", 0) * 20
        
        total_score = base_score + turn_bonus + type_bonus + performance_bonus
        return max(0, total_score)
    
    def _record_progress_history(self, current_turn: int, results: List[VictoryResult]):
        """Record victory progress history"""
        history_entry = {
            "turn": current_turn,
            "progress": {result.victory_type.value: result.progress for result in results},
            "statuses": {result.victory_type.value: result.status.value for result in results}
        }
        
        self.progress_history.append(history_entry)
        
        # Keep only last 20 turns of history
        if len(self.progress_history) > 20:
            self.progress_history.pop(0)
    
    def get_victory_status(self) -> Dict[str, Any]:
        """Get current victory status"""
        return {
            "game_ended": self.game_ended,
            "victory_achieved": self.victory_achieved.value if self.victory_achieved else None,
            "victory_turn": self.victory_turn,
            "victory_score": self.victory_score,
            "conditions": {
                victory_type.value: {
                    "name": condition.name,
                    "description": condition.description,
                    "progress": condition.get_progress_percentage(),
                    "status": condition.status.value,
                    "turn_achieved": condition.turn_achieved
                }
                for victory_type, condition in self.victory_conditions.items()
            }
        }
    
    def get_victory_progress_summary(self) -> Dict[str, Any]:
        """Get summary of victory progress"""
        summary = {}
        
        for victory_type, condition in self.victory_conditions.items():
            summary[victory_type.value] = {
                "name": condition.name,
                "progress": condition.get_progress_percentage(),
                "status": condition.status.value,
                "description": condition.description
            }
        
        return summary
    
    def get_closest_victory(self) -> Optional[Tuple[VictoryType, float]]:
        """Get the victory condition closest to completion"""
        if self.game_ended:
            return None
        
        closest_victory = None
        highest_progress = 0.0
        
        for victory_type, condition in self.victory_conditions.items():
            if condition.current_progress > highest_progress:
                highest_progress = condition.current_progress
                closest_victory = victory_type
        
        return (closest_victory, highest_progress) if closest_victory else None
    
    def get_progress_history(self, turns: int = 10) -> List[Dict[str, Any]]:
        """Get victory progress history"""
        return self.progress_history[-turns:] if self.progress_history else []
    
    def is_game_ended(self) -> bool:
        """Check if game has ended due to victory"""
        return self.game_ended
    
    def reset_victory_conditions(self):
        """Reset all victory conditions (for new game)"""
        self.game_ended = False
        self.victory_achieved = None
        self.victory_turn = None
        self.victory_score = 0
        self.progress_history.clear()
        
        for condition in self.victory_conditions.values():
            condition.current_progress = 0.0
            condition.status = VictoryStatus.NOT_STARTED
            condition.turn_achieved = None
        
        self.logger.info("Victory conditions reset for new game")