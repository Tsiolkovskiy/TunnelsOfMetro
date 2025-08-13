"""
Diplomacy System
Handles diplomatic relationships, negotiations, and alliance management
"""

import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass

from systems.metro_map import MetroMap


class RelationshipStatus(Enum):
    """Diplomatic relationship statuses"""
    ALLIED = "allied"
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    UNFRIENDLY = "unfriendly"
    HOSTILE = "hostile"
    AT_WAR = "at_war"


class DiplomaticAction(Enum):
    """Types of diplomatic actions"""
    IMPROVE_RELATIONS = "improve_relations"
    DECLARE_WAR = "declare_war"
    OFFER_PEACE = "offer_peace"
    FORM_ALLIANCE = "form_alliance"
    BREAK_ALLIANCE = "break_alliance"
    TRADE_AGREEMENT = "trade_agreement"
    NON_AGGRESSION_PACT = "non_aggression_pact"
    DEMAND_TRIBUTE = "demand_tribute"
    OFFER_TRIBUTE = "offer_tribute"


class DiplomaticModifier(Enum):
    """Factors that modify diplomatic relationships"""
    IDEOLOGICAL_ALIGNMENT = "ideological_alignment"
    BORDER_DISPUTES = "border_disputes"
    TRADE_RELATIONS = "trade_relations"
    RECENT_AGGRESSION = "recent_aggression"
    MUTUAL_ENEMIES = "mutual_enemies"
    CULTURAL_EXCHANGE = "cultural_exchange"
    RESOURCE_COMPETITION = "resource_competition"


@dataclass
class DiplomaticRelationship:
    """Represents relationship between two factions"""
    faction_a: str
    faction_b: str
    
    # Relationship value (-100 to +100)
    relationship_value: int
    
    # Status derived from relationship value
    status: RelationshipStatus = None
    
    # Active agreements
    trade_agreement: bool = False
    non_aggression_pact: bool = False
    military_alliance: bool = False
    
    # Relationship modifiers
    modifiers: Dict[DiplomaticModifier, int] = None
    
    # History tracking
    last_interaction_turn: int = 0
    relationship_trend: int = 0  # Positive = improving, negative = deteriorating
    
    def __post_init__(self):
        if self.modifiers is None:
            self.modifiers = {}
        self.status = self._calculate_status()
    
    def _calculate_status(self) -> RelationshipStatus:
        """Calculate relationship status from value"""
        if self.relationship_value >= 80:
            return RelationshipStatus.ALLIED
        elif self.relationship_value >= 40:
            return RelationshipStatus.FRIENDLY
        elif self.relationship_value >= -20:
            return RelationshipStatus.NEUTRAL
        elif self.relationship_value >= -60:
            return RelationshipStatus.UNFRIENDLY
        elif self.relationship_value >= -80:
            return RelationshipStatus.HOSTILE
        else:
            return RelationshipStatus.AT_WAR
    
    def modify_relationship(self, change: int, reason: str = ""):
        """Modify relationship value"""
        old_value = self.relationship_value
        self.relationship_value = max(-100, min(100, self.relationship_value + change))
        self.status = self._calculate_status()
        self.relationship_trend = self.relationship_value - old_value
        
        return self.relationship_value != old_value


@dataclass
class DiplomaticProposal:
    """Represents a diplomatic proposal between factions"""
    proposer: str
    target: str
    action: DiplomaticAction
    
    # Proposal terms
    mgr_cost: int
    resource_offer: Dict[str, int]
    conditions: List[str]
    
    # Proposal status
    expires_turn: int
    response_required: bool = True
    
    def is_expired(self, current_turn: int) -> bool:
        return current_turn > self.expires_turn


class DiplomacySystem:
    """
    Complete diplomacy and relationship management system
    
    Features:
    - Dynamic relationship tracking
    - Faction-specific diplomatic options
    - Alliance and treaty management
    - Diplomatic modifiers and consequences
    - AI diplomatic behavior simulation
    """
    
    def __init__(self, metro_map: MetroMap):
        """
        Initialize diplomacy system
        
        Args:
            metro_map: MetroMap instance
        """
        self.metro_map = metro_map
        self.logger = logging.getLogger(__name__)
        
        # Diplomatic relationships
        self.relationships: Dict[Tuple[str, str], DiplomaticRelationship] = {}
        
        # Active proposals
        self.active_proposals: List[DiplomaticProposal] = []
        
        # Faction ideologies and characteristics
        self.faction_ideologies = {
            "Rangers": {"alignment": "pragmatic", "openness": 70, "aggression": 30},
            "Polis": {"alignment": "intellectual", "openness": 90, "aggression": 20},
            "Fourth Reich": {"alignment": "fascist", "openness": 20, "aggression": 90},
            "Red Line": {"alignment": "communist", "openness": 40, "aggression": 70},
            "Hanza": {"alignment": "capitalist", "openness": 80, "aggression": 40},
            "Invisible Watchers": {"alignment": "secretive", "openness": 10, "aggression": 60},
            "Independent": {"alignment": "neutral", "openness": 60, "aggression": 30}
        }
        
        # Initialize default relationships
        self._initialize_relationships()
        
        self.logger.info("Diplomacy system initialized")
    
    def _initialize_relationships(self):
        """Initialize default faction relationships based on lore"""
        default_relationships = [
            # Allied relationships
            ("Rangers", "Polis", 60),
            ("Polis", "Hanza", 50),
            
            # Hostile relationships
            ("Rangers", "Fourth Reich", -80),
            ("Rangers", "Red Line", -70),
            ("Fourth Reich", "Red Line", -90),
            ("Polis", "Invisible Watchers", -60),
            
            # Neutral relationships
            ("Rangers", "Hanza", 10),
            ("Rangers", "Independent", 20),
            ("Polis", "Independent", 30),
            ("Hanza", "Independent", 40),
            ("Fourth Reich", "Independent", -30),
            ("Red Line", "Independent", 0),
            ("Invisible Watchers", "Independent", -10),
            
            # Complex relationships
            ("Hanza", "Fourth Reich", 20),  # Trade despite ideology
            ("Hanza", "Red Line", 10),      # Reluctant trade
            ("Fourth Reich", "Invisible Watchers", 0),  # Unknown manipulation
            ("Red Line", "Invisible Watchers", 0),      # Unknown manipulation
            ("Hanza", "Invisible Watchers", -20)        # Economic competition
        ]
        
        for faction_a, faction_b, value in default_relationships:
            self._create_relationship(faction_a, faction_b, value)
    
    def _create_relationship(self, faction_a: str, faction_b: str, initial_value: int):
        """Create a diplomatic relationship"""
        # Ensure consistent ordering
        if faction_a > faction_b:
            faction_a, faction_b = faction_b, faction_a
        
        key = (faction_a, faction_b)
        
        relationship = DiplomaticRelationship(
            faction_a=faction_a,
            faction_b=faction_b,
            relationship_value=initial_value
        )
        
        # Add ideological modifiers
        self._apply_ideological_modifiers(relationship)
        
        self.relationships[key] = relationship
    
    def _apply_ideological_modifiers(self, relationship: DiplomaticRelationship):
        """Apply ideological compatibility modifiers"""
        faction_a_ideology = self.faction_ideologies.get(relationship.faction_a, {})
        faction_b_ideology = self.faction_ideologies.get(relationship.faction_b, {})
        
        a_alignment = faction_a_ideology.get("alignment", "neutral")
        b_alignment = faction_b_ideology.get("alignment", "neutral")
        
        # Ideological compatibility matrix
        compatibility = {
            ("fascist", "communist"): -30,
            ("fascist", "capitalist"): 10,
            ("communist", "capitalist"): -20,
            ("intellectual", "fascist"): -25,
            ("intellectual", "communist"): -10,
            ("pragmatic", "secretive"): -15,
            ("neutral", "fascist"): -10
        }
        
        modifier = compatibility.get((a_alignment, b_alignment), 0)
        if modifier == 0:
            modifier = compatibility.get((b_alignment, a_alignment), 0)
        
        if modifier != 0:
            relationship.modifiers[DiplomaticModifier.IDEOLOGICAL_ALIGNMENT] = modifier
            relationship.relationship_value += modifier
            relationship.status = relationship._calculate_status()
    
    def get_relationship(self, faction_a: str, faction_b: str) -> Optional[DiplomaticRelationship]:
        """Get relationship between two factions"""
        if faction_a == faction_b:
            return None
        
        # Ensure consistent ordering
        if faction_a > faction_b:
            faction_a, faction_b = faction_b, faction_a
        
        key = (faction_a, faction_b)
        return self.relationships.get(key)
    
    def get_relationship_value(self, faction_a: str, faction_b: str) -> int:
        """Get relationship value between two factions"""
        relationship = self.get_relationship(faction_a, faction_b)
        return relationship.relationship_value if relationship else 0
    
    def can_perform_action(self, actor: str, target: str, action: DiplomaticAction) -> Tuple[bool, str]:
        """Check if a diplomatic action is valid"""
        if actor == target:
            return False, "Cannot perform diplomatic actions with yourself"
        
        relationship = self.get_relationship(actor, target)
        if not relationship:
            return False, "No diplomatic relationship exists"
        
        # Action-specific validation
        if action == DiplomaticAction.DECLARE_WAR:
            if relationship.status == RelationshipStatus.AT_WAR:
                return False, "Already at war"
            if relationship.military_alliance:
                return False, "Cannot declare war on military ally"
        
        elif action == DiplomaticAction.FORM_ALLIANCE:
            if relationship.military_alliance:
                return False, "Military alliance already exists"
            if relationship.status in [RelationshipStatus.HOSTILE, RelationshipStatus.AT_WAR]:
                return False, "Cannot form alliance with hostile faction"
        
        elif action == DiplomaticAction.OFFER_PEACE:
            if relationship.status != RelationshipStatus.AT_WAR:
                return False, "Not currently at war"
        
        elif action == DiplomaticAction.TRADE_AGREEMENT:
            if relationship.trade_agreement:
                return False, "Trade agreement already exists"
            if relationship.status == RelationshipStatus.AT_WAR:
                return False, "Cannot trade with faction at war"
        
        return True, "Action is valid"
    
    def execute_diplomatic_action(self, actor: str, target: str, action: DiplomaticAction,
                                 current_turn: int, mgr_cost: int = 0,
                                 resource_offer: Dict[str, int] = None) -> Dict[str, Any]:
        """
        Execute a diplomatic action
        
        Args:
            actor: Acting faction
            target: Target faction
            action: Diplomatic action to perform
            current_turn: Current game turn
            mgr_cost: MGR cost for the action
            resource_offer: Resources offered (if any)
            
        Returns:
            Result dictionary
        """
        can_perform, reason = self.can_perform_action(actor, target, action)
        if not can_perform:
            return {"success": False, "message": reason}
        
        relationship = self.get_relationship(actor, target)
        if not relationship:
            return {"success": False, "message": "No diplomatic relationship exists"}
        
        # Calculate success chance
        success_chance = self._calculate_action_success_chance(actor, target, action, mgr_cost)
        
        # Execute action
        if random.random() <= success_chance:
            result = self._apply_diplomatic_action(relationship, action, current_turn, mgr_cost, resource_offer)
            result["success"] = True
        else:
            result = {
                "success": False,
                "message": f"Diplomatic action failed - {target} rejected the proposal",
                "relationship_change": -5  # Failed diplomacy hurts relations
            }
            relationship.modify_relationship(-5, f"Failed {action.value}")
        
        relationship.last_interaction_turn = current_turn
        return result
    
    def _calculate_action_success_chance(self, actor: str, target: str, 
                                       action: DiplomaticAction, mgr_cost: int) -> float:
        """Calculate success chance for diplomatic action"""
        relationship = self.get_relationship(actor, target)
        if not relationship:
            return 0.0
        
        # Base success chance from relationship value
        base_chance = 0.5 + (relationship.relationship_value / 200.0)  # -0.5 to 1.0
        
        # Action-specific modifiers
        action_modifiers = {
            DiplomaticAction.IMPROVE_RELATIONS: 0.8,
            DiplomaticAction.OFFER_PEACE: 0.6,
            DiplomaticAction.TRADE_AGREEMENT: 0.7,
            DiplomaticAction.NON_AGGRESSION_PACT: 0.7,
            DiplomaticAction.FORM_ALLIANCE: 0.4,
            DiplomaticAction.DEMAND_TRIBUTE: 0.2,
            DiplomaticAction.DECLARE_WAR: 1.0  # Always succeeds
        }
        
        modifier = action_modifiers.get(action, 0.5)
        
        # MGR investment improves chances
        mgr_bonus = min(0.3, mgr_cost / 100.0)
        
        # Faction personality affects diplomacy
        target_ideology = self.faction_ideologies.get(target, {})
        openness_bonus = (target_ideology.get("openness", 50) - 50) / 200.0
        
        final_chance = base_chance * modifier + mgr_bonus + openness_bonus
        return max(0.1, min(0.95, final_chance))
    
    def _apply_diplomatic_action(self, relationship: DiplomaticRelationship, 
                               action: DiplomaticAction, current_turn: int,
                               mgr_cost: int, resource_offer: Dict[str, int] = None) -> Dict[str, Any]:
        """Apply the effects of a successful diplomatic action"""
        result = {"message": "", "relationship_change": 0, "agreements": []}
        
        if action == DiplomaticAction.IMPROVE_RELATIONS:
            improvement = 10 + (mgr_cost // 5)
            relationship.modify_relationship(improvement, "Diplomatic outreach")
            result["message"] = f"Relations improved with {relationship.faction_b}"
            result["relationship_change"] = improvement
        
        elif action == DiplomaticAction.DECLARE_WAR:
            relationship.modify_relationship(-50, "War declared")
            relationship.military_alliance = False
            relationship.trade_agreement = False
            relationship.non_aggression_pact = False
            result["message"] = f"War declared against {relationship.faction_b}"
            result["relationship_change"] = -50
        
        elif action == DiplomaticAction.OFFER_PEACE:
            improvement = 30
            relationship.modify_relationship(improvement, "Peace treaty")
            result["message"] = f"Peace treaty signed with {relationship.faction_b}"
            result["relationship_change"] = improvement
        
        elif action == DiplomaticAction.FORM_ALLIANCE:
            relationship.military_alliance = True
            relationship.modify_relationship(20, "Military alliance formed")
            result["message"] = f"Military alliance formed with {relationship.faction_b}"
            result["relationship_change"] = 20
            result["agreements"].append("Military Alliance")
        
        elif action == DiplomaticAction.TRADE_AGREEMENT:
            relationship.trade_agreement = True
            relationship.modify_relationship(15, "Trade agreement signed")
            result["message"] = f"Trade agreement signed with {relationship.faction_b}"
            result["relationship_change"] = 15
            result["agreements"].append("Trade Agreement")
        
        elif action == DiplomaticAction.NON_AGGRESSION_PACT:
            relationship.non_aggression_pact = True
            relationship.modify_relationship(10, "Non-aggression pact signed")
            result["message"] = f"Non-aggression pact signed with {relationship.faction_b}"
            result["relationship_change"] = 10
            result["agreements"].append("Non-Aggression Pact")
        
        elif action == DiplomaticAction.DEMAND_TRIBUTE:
            # Demanding tribute hurts relations but may provide resources
            relationship.modify_relationship(-15, "Tribute demanded")
            result["message"] = f"Tribute demanded from {relationship.faction_b}"
            result["relationship_change"] = -15
            result["tribute_received"] = resource_offer or {"mgr_rounds": 10}
        
        return result
    
    def get_diplomatic_options(self, actor: str, target: str) -> List[Dict[str, Any]]:
        """Get available diplomatic options for a faction pair"""
        relationship = self.get_relationship(actor, target)
        if not relationship:
            return []
        
        options = []
        
        # Always available: improve relations
        options.append({
            "action": DiplomaticAction.IMPROVE_RELATIONS,
            "name": "Improve Relations",
            "description": "Send diplomatic envoys to improve relations",
            "mgr_cost": 10,
            "success_chance": self._calculate_action_success_chance(actor, target, DiplomaticAction.IMPROVE_RELATIONS, 10)
        })
        
        # Status-specific options
        if relationship.status == RelationshipStatus.AT_WAR:
            options.append({
                "action": DiplomaticAction.OFFER_PEACE,
                "name": "Offer Peace",
                "description": "Propose end to hostilities",
                "mgr_cost": 25,
                "success_chance": self._calculate_action_success_chance(actor, target, DiplomaticAction.OFFER_PEACE, 25)
            })
        
        elif relationship.status in [RelationshipStatus.FRIENDLY, RelationshipStatus.ALLIED]:
            if not relationship.trade_agreement:
                options.append({
                    "action": DiplomaticAction.TRADE_AGREEMENT,
                    "name": "Trade Agreement",
                    "description": "Establish formal trade relations",
                    "mgr_cost": 15,
                    "success_chance": self._calculate_action_success_chance(actor, target, DiplomaticAction.TRADE_AGREEMENT, 15)
                })
            
            if not relationship.military_alliance and relationship.status == RelationshipStatus.ALLIED:
                options.append({
                    "action": DiplomaticAction.FORM_ALLIANCE,
                    "name": "Military Alliance",
                    "description": "Form military alliance for mutual defense",
                    "mgr_cost": 30,
                    "success_chance": self._calculate_action_success_chance(actor, target, DiplomaticAction.FORM_ALLIANCE, 30)
                })
        
        elif relationship.status == RelationshipStatus.NEUTRAL:
            if not relationship.non_aggression_pact:
                options.append({
                    "action": DiplomaticAction.NON_AGGRESSION_PACT,
                    "name": "Non-Aggression Pact",
                    "description": "Agree not to attack each other",
                    "mgr_cost": 12,
                    "success_chance": self._calculate_action_success_chance(actor, target, DiplomaticAction.NON_AGGRESSION_PACT, 12)
                })
        
        # War declaration (if not already at war and not allied)
        if relationship.status != RelationshipStatus.AT_WAR and not relationship.military_alliance:
            options.append({
                "action": DiplomaticAction.DECLARE_WAR,
                "name": "Declare War",
                "description": "Formally declare hostilities",
                "mgr_cost": 0,
                "success_chance": 1.0,
                "warning": True
            })
        
        return options
    
    def get_faction_relationships(self, faction: str) -> Dict[str, Dict[str, Any]]:
        """Get all relationships for a faction"""
        faction_relationships = {}
        
        for (faction_a, faction_b), relationship in self.relationships.items():
            other_faction = None
            if faction_a == faction:
                other_faction = faction_b
            elif faction_b == faction:
                other_faction = faction_a
            
            if other_faction:
                faction_relationships[other_faction] = {
                    "status": relationship.status.value,
                    "value": relationship.relationship_value,
                    "trend": relationship.relationship_trend,
                    "trade_agreement": relationship.trade_agreement,
                    "non_aggression_pact": relationship.non_aggression_pact,
                    "military_alliance": relationship.military_alliance,
                    "last_interaction": relationship.last_interaction_turn
                }
        
        return faction_relationships
    
    def process_turn(self, current_turn: int):
        """Process end-of-turn diplomacy updates"""
        # Natural relationship decay/improvement over time
        for relationship in self.relationships.values():
            # Relationships slowly drift toward neutral if no interaction
            turns_since_interaction = current_turn - relationship.last_interaction_turn
            
            if turns_since_interaction > 5:
                # Slow drift toward neutral
                if relationship.relationship_value > 0:
                    relationship.modify_relationship(-1, "Natural drift")
                elif relationship.relationship_value < 0:
                    relationship.modify_relationship(1, "Natural drift")
        
        # Remove expired proposals
        self.active_proposals = [p for p in self.active_proposals if not p.is_expired(current_turn)]
    
    def get_diplomacy_summary(self) -> Dict[str, Any]:
        """Get summary of diplomatic situation"""
        status_counts = {}
        for relationship in self.relationships.values():
            status = relationship.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_relationships": len(self.relationships),
            "status_breakdown": status_counts,
            "active_proposals": len(self.active_proposals),
            "active_alliances": len([r for r in self.relationships.values() if r.military_alliance]),
            "active_trade_agreements": len([r for r in self.relationships.values() if r.trade_agreement])
        }