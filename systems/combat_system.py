"""
Combat System
Handles military actions, battles, and territory control changes
"""

import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass

from systems.metro_map import MetroMap
from data.station import Station
from data.resources import ResourcePool
from data.military_unit import MilitaryManager


class CombatResult(Enum):
    """Results of combat encounters"""
    DECISIVE_VICTORY = "decisive_victory"
    VICTORY = "victory"
    PYRRHIC_VICTORY = "pyrrhic_victory"
    DEFEAT = "defeat"
    CRUSHING_DEFEAT = "crushing_defeat"
    STALEMATE = "stalemate"


class AttackType(Enum):
    """Types of military attacks"""
    ASSAULT = "assault"
    SIEGE = "siege"
    RAID = "raid"
    INFILTRATION = "infiltration"


@dataclass
class CombatForce:
    """Represents a military force in combat"""
    faction: str
    station: str
    
    # Military strength components
    manpower: int
    equipment_quality: int  # 1-10 scale
    morale: int  # 0-100
    leadership: int  # 0-10 scale
    
    # Special modifiers
    defensive_bonus: int = 0
    terrain_bonus: int = 0
    supply_bonus: int = 0
    
    def get_total_strength(self) -> int:
        """Calculate total military strength"""
        base_strength = self.manpower * (self.equipment_quality / 10.0)
        morale_modifier = 0.5 + (self.morale / 100.0) * 0.5  # 0.5 to 1.0
        leadership_modifier = 1.0 + (self.leadership / 20.0)  # 1.0 to 1.5
        
        total_strength = base_strength * morale_modifier * leadership_modifier
        total_strength += self.defensive_bonus + self.terrain_bonus + self.supply_bonus
        
        return int(total_strength)


@dataclass
class BattleReport:
    """Detailed battle report"""
    attacker: str
    defender: str
    attack_type: AttackType
    
    attacker_strength: int
    defender_strength: int
    
    result: CombatResult
    
    attacker_casualties: int
    defender_casualties: int
    
    territory_changed: bool
    resources_captured: Dict[str, int]
    
    battle_description: str
    turn_number: int
    
    # Additional fields for unit tracking
    attacker_station: str = ""
    defender_station: str = ""


class CombatSystem:
    """
    Complete combat and military system
    
    Features:
    - Relationship-based attack validation
    - Resource cost requirements
    - Probability-based combat resolution
    - Territory capture mechanics
    - Detailed battle reports
    - Faction-specific combat bonuses
    """
    
    def __init__(self, metro_map: MetroMap):
        """
        Initialize combat system
        
        Args:
            metro_map: MetroMap instance
        """
        self.metro_map = metro_map
        self.logger = logging.getLogger(__name__)
        
        # Combat settings
        self.base_attack_cost = 50  # Base MGR cost for attacks
        self.casualty_rates = {
            CombatResult.DECISIVE_VICTORY: (0.05, 0.30),  # (attacker, defender)
            CombatResult.VICTORY: (0.10, 0.25),
            CombatResult.PYRRHIC_VICTORY: (0.20, 0.20),
            CombatResult.DEFEAT: (0.25, 0.10),
            CombatResult.CRUSHING_DEFEAT: (0.30, 0.05),
            CombatResult.STALEMATE: (0.15, 0.15)
        }
        
        # Reference to diplomacy system (will be set by game state)
        self.diplomacy_system = None
        
        # Reference to military managers (will be set by game state)
        self.military_managers: Dict[str, MilitaryManager] = {}
        
        # Battle history
        self.battle_history: List[BattleReport] = []
        
        self.logger.info("Combat system initialized")
    
    def register_military_manager(self, faction: str, military_manager: MilitaryManager):
        """Register a military manager for a faction"""
        self.military_managers[faction] = military_manager
        self.logger.info(f"Registered military manager for faction: {faction}")
    
    def can_attack(self, attacker_faction: str, target_station: str) -> Tuple[bool, str]:
        """
        Check if an attack is valid
        
        Args:
            attacker_faction: Attacking faction
            target_station: Target station name
            
        Returns:
            Tuple of (can_attack, reason)
        """
        target = self.metro_map.get_station(target_station)
        if not target:
            return False, f"Target station {target_station} not found"
        
        defender_faction = target.controlling_faction
        
        # Cannot attack own stations
        if attacker_faction == defender_faction:
            return False, "Cannot attack your own stations"
        
        # Check faction relationships
        relationship = self._get_faction_relationship(attacker_faction, defender_faction)
        if relationship >= 0:
            return False, f"Cannot attack {defender_faction} - not at war"
        
        return True, "Attack is valid"
    
    def execute_attack(self, origin_station: str, target_station: str, 
                      attacker_faction: str, player_resources: ResourcePool,
                      current_turn: int, attack_type: AttackType = AttackType.ASSAULT) -> Dict[str, Any]:
        """
        Execute an attack on a target station
        
        Args:
            origin_station: Attacking station
            target_station: Target station
            attacker_faction: Attacking faction
            player_resources: Player's resource pool
            current_turn: Current game turn
            attack_type: Type of attack
            
        Returns:
            Result dictionary with battle outcome
        """
        # Validate attack
        can_attack, reason = self.can_attack(attacker_faction, target_station)
        if not can_attack:
            return {"success": False, "message": reason}
        
        # Check resource costs
        attack_cost = self._calculate_attack_cost(origin_station, target_station, attack_type)
        if not player_resources.has_sufficient("mgr_rounds", attack_cost):
            return {"success": False, "message": f"Insufficient MGR for attack (need {attack_cost})"}
        
        # Consume resources
        player_resources.subtract("mgr_rounds", attack_cost)
        
        # Create combat forces
        attacker_force = self._create_combat_force(origin_station, attacker_faction, False)
        defender_force = self._create_combat_force(target_station, None, True)
        
        # Resolve combat
        battle_report = self._resolve_combat(attacker_force, defender_force, attack_type, current_turn)
        
        # Store station names for casualty application
        battle_report.attacker_station = origin_station
        battle_report.defender_station = target_station
        
        # Apply battle results
        result = self._apply_battle_results(battle_report, player_resources)
        
        # Store battle in history
        self.battle_history.append(battle_report)
        
        return result
    
    def _get_faction_relationship(self, faction_a: str, faction_b: str) -> int:
        """Get relationship between two factions"""
        if self.diplomacy_system:
            return self.diplomacy_system.get_relationship_value(faction_a, faction_b)
        
        # Fallback to simplified relationships if diplomacy system not available
        hostile_pairs = [
            ("Rangers", "Fourth Reich"),
            ("Rangers", "Red Line"),
            ("Fourth Reich", "Red Line"),
            ("Polis", "Invisible Watchers")
        ]
        
        if ((faction_a, faction_b) in hostile_pairs or 
            (faction_b, faction_a) in hostile_pairs):
            return -70
        
        return 0  # Neutral by default
    
    def _calculate_attack_cost(self, origin: str, target: str, attack_type: AttackType) -> int:
        """Calculate MGR cost for attack"""
        base_cost = self.base_attack_cost
        
        # Distance factor
        path = self.metro_map.find_path(origin, target, "military")
        if path:
            distance_cost = len(path) * 5
        else:
            distance_cost = 25  # High cost for difficult approaches
        
        # Attack type modifiers
        type_modifiers = {
            AttackType.ASSAULT: 1.0,
            AttackType.SIEGE: 1.5,
            AttackType.RAID: 0.7,
            AttackType.INFILTRATION: 0.8
        }
        
        modifier = type_modifiers.get(attack_type, 1.0)
        
        return int((base_cost + distance_cost) * modifier)
    
    def _create_combat_force(self, station_name: str, faction: str = None, is_defender: bool = False) -> CombatForce:
        """Create combat force for a station using actual military units"""
        station = self.metro_map.get_station(station_name)
        if not station:
            # Return minimal force if station not found
            return CombatForce(
                faction=faction or "Unknown",
                station=station_name,
                manpower=10,
                equipment_quality=1,
                morale=50,
                leadership=1
            )
        
        faction = faction or station.controlling_faction
        
        # Get military units at this station
        military_manager = self.military_managers.get(faction)
        if military_manager:
            units = military_manager.get_units_at_station(station_name)
            
            if units:
                # Calculate force from actual military units
                total_strength = sum(unit.calculate_combat_strength() for unit in units)
                avg_morale = sum(unit.morale for unit in units) / len(units)
                avg_equipment = sum(unit.equipment_level for unit in units) / len(units)
                
                # Convert unit strength to manpower equivalent
                manpower = max(10, int(total_strength / 2))  # Rough conversion
                equipment_quality = min(10, int(avg_equipment * 2))
                morale = int(avg_morale)
                
                # Leadership bonus from elite units
                leadership = self._get_faction_leadership(faction)
                for unit in units:
                    if unit.has_ability("leadership"):
                        leadership += 2
                    elif unit.has_ability("elite_training"):
                        leadership += 1
                
                leadership = min(10, leadership)
            else:
                # No military units - use militia/population
                manpower = max(5, station.population // 20)  # Reduced from civilian population
                equipment_quality = max(1, self._get_faction_equipment_quality(faction) - 2)
                morale = max(30, station.morale - 20)  # Lower morale for untrained civilians
                leadership = max(1, self._get_faction_leadership(faction) - 2)
        else:
            # Fallback to old system if no military manager
            manpower = max(10, station.population // 10)
            equipment_quality = self._get_faction_equipment_quality(faction)
            morale = station.morale
            leadership = self._get_faction_leadership(faction)
        
        # Add infrastructure bonuses
        from data.infrastructure import BuildingType
        if BuildingType.BARRACKS in station.infrastructure:
            barracks = station.infrastructure[BuildingType.BARRACKS]
            manpower += barracks.efficiency_level * 3
            equipment_quality += barracks.efficiency_level
        
        force = CombatForce(
            faction=faction,
            station=station_name,
            manpower=manpower,
            equipment_quality=min(10, equipment_quality),
            morale=max(10, min(100, morale)),
            leadership=min(10, leadership)
        )
        
        # Defensive bonuses
        if is_defender:
            force.defensive_bonus = station.defensive_value
            
            # Fortification bonuses
            if BuildingType.FORTIFICATIONS in station.infrastructure:
                fortifications = station.infrastructure[BuildingType.FORTIFICATIONS]
                force.defensive_bonus += fortifications.efficiency_level * 10
            
            # Defensive unit bonuses
            if military_manager:
                units = military_manager.get_units_at_station(station_name)
                for unit in units:
                    if unit.has_ability("fortification"):
                        force.defensive_bonus += 5
        
        return force
    
    def _get_faction_equipment_quality(self, faction: str) -> int:
        """Get base equipment quality for faction"""
        faction_equipment = {
            "Rangers": 8,
            "Fourth Reich": 7,
            "Red Line": 5,
            "Polis": 9,
            "Hanza": 6,
            "Invisible Watchers": 8,
            "Independent": 4
        }
        return faction_equipment.get(faction, 5)
    
    def _get_faction_leadership(self, faction: str) -> int:
        """Get leadership quality for faction"""
        faction_leadership = {
            "Rangers": 8,
            "Fourth Reich": 7,
            "Red Line": 6,
            "Polis": 7,
            "Hanza": 5,
            "Invisible Watchers": 9,
            "Independent": 3
        }
        return faction_leadership.get(faction, 5)
    
    def _resolve_combat(self, attacker: CombatForce, defender: CombatForce, 
                       attack_type: AttackType, current_turn: int) -> BattleReport:
        """Resolve combat between two forces"""
        attacker_strength = attacker.get_total_strength()
        defender_strength = defender.get_total_strength()
        
        # Calculate strength ratio
        total_strength = attacker_strength + defender_strength
        if total_strength == 0:
            strength_ratio = 0.5
        else:
            strength_ratio = attacker_strength / total_strength
        
        # Add randomness
        random_factor = random.uniform(-0.2, 0.2)
        final_ratio = max(0.0, min(1.0, strength_ratio + random_factor))
        
        # Determine result
        result = self._determine_combat_result(final_ratio, attack_type)
        
        # Calculate casualties
        attacker_casualties, defender_casualties = self._calculate_casualties(
            attacker, defender, result
        )
        
        # Determine if territory changes hands
        territory_changed = result in [CombatResult.DECISIVE_VICTORY, CombatResult.VICTORY]
        
        # Resources captured
        resources_captured = {}
        if territory_changed:
            defender_station = self.metro_map.get_station(defender.station)
            if defender_station:
                # Capture portion of station resources
                capture_rate = 0.3 if result == CombatResult.DECISIVE_VICTORY else 0.2
                resources_captured = {
                    "food": int(defender_station.resources.food * capture_rate),
                    "clean_water": int(defender_station.resources.clean_water * capture_rate),
                    "scrap": int(defender_station.resources.scrap * capture_rate),
                    "medicine": int(defender_station.resources.medicine * capture_rate),
                    "mgr_rounds": int(defender_station.resources.mgr_rounds * capture_rate)
                }
        
        # Create battle description
        description = self._create_battle_description(
            attacker, defender, result, attacker_casualties, defender_casualties
        )
        
        return BattleReport(
            attacker=attacker.faction,
            defender=defender.faction,
            attack_type=attack_type,
            attacker_strength=attacker_strength,
            defender_strength=defender_strength,
            result=result,
            attacker_casualties=attacker_casualties,
            defender_casualties=defender_casualties,
            territory_changed=territory_changed,
            resources_captured=resources_captured,
            battle_description=description,
            turn_number=current_turn
        )
    
    def _determine_combat_result(self, strength_ratio: float, attack_type: AttackType) -> CombatResult:
        """Determine combat result based on strength ratio"""
        # Attack type modifiers
        if attack_type == AttackType.RAID:
            # Raids are less likely to achieve decisive results
            strength_ratio = 0.3 + strength_ratio * 0.4
        elif attack_type == AttackType.SIEGE:
            # Sieges favor the attacker slightly
            strength_ratio += 0.1
        
        if strength_ratio >= 0.8:
            return CombatResult.DECISIVE_VICTORY
        elif strength_ratio >= 0.65:
            return CombatResult.VICTORY
        elif strength_ratio >= 0.55:
            return CombatResult.PYRRHIC_VICTORY
        elif strength_ratio >= 0.45:
            return CombatResult.STALEMATE
        elif strength_ratio >= 0.3:
            return CombatResult.DEFEAT
        else:
            return CombatResult.CRUSHING_DEFEAT
    
    def _calculate_casualties(self, attacker: CombatForce, defender: CombatForce, 
                            result: CombatResult) -> Tuple[int, int]:
        """Calculate casualties for both sides"""
        casualty_rates = self.casualty_rates[result]
        
        attacker_casualties = int(attacker.manpower * casualty_rates[0])
        defender_casualties = int(defender.manpower * casualty_rates[1])
        
        return attacker_casualties, defender_casualties
    
    def _create_battle_description(self, attacker: CombatForce, defender: CombatForce,
                                 result: CombatResult, att_casualties: int, def_casualties: int) -> str:
        """Create descriptive battle report"""
        descriptions = {
            CombatResult.DECISIVE_VICTORY: f"{attacker.faction} forces overwhelmed {defender.faction} defenders at {defender.station}",
            CombatResult.VICTORY: f"{attacker.faction} successfully captured {defender.station} from {defender.faction}",
            CombatResult.PYRRHIC_VICTORY: f"{attacker.faction} took {defender.station} but at heavy cost",
            CombatResult.DEFEAT: f"{defender.faction} repelled {attacker.faction} attack on {defender.station}",
            CombatResult.CRUSHING_DEFEAT: f"{attacker.faction} forces were routed at {defender.station}",
            CombatResult.STALEMATE: f"Fierce fighting at {defender.station} ended in stalemate"
        }
        
        base_description = descriptions.get(result, "Battle occurred")
        casualty_info = f"Casualties: {attacker.faction} {att_casualties}, {defender.faction} {def_casualties}"
        
        return f"{base_description}. {casualty_info}"
    
    def _apply_battle_results(self, battle_report: BattleReport, player_resources: ResourcePool) -> Dict[str, Any]:
        """Apply battle results to game state"""
        result_messages = []
        
        # Territory change
        if battle_report.territory_changed:
            target_station = self.metro_map.get_station(battle_report.defender)
            if target_station:
                # Change faction control
                old_faction = target_station.controlling_faction
                target_station.change_faction_control(battle_report.attacker, peaceful=False)
                
                result_messages.append(f"Captured {target_station.name} from {old_faction}")
                
                # Add captured resources to player
                for resource, amount in battle_report.resources_captured.items():
                    if amount > 0:
                        player_resources.add(resource, amount)
                        # Remove from station
                        target_station.resources.subtract(resource, amount)
                
                if battle_report.resources_captured:
                    captured_summary = ", ".join(f"{amount} {resource}" 
                                                for resource, amount in battle_report.resources_captured.items() 
                                                if amount > 0)
                    result_messages.append(f"Captured resources: {captured_summary}")
        
        # Create result message
        success = battle_report.result in [CombatResult.DECISIVE_VICTORY, CombatResult.VICTORY, CombatResult.PYRRHIC_VICTORY]
        
        main_message = battle_report.battle_description
        if result_messages:
            main_message += ". " + ". ".join(result_messages)
        
        # Apply casualties to military units
        self._apply_unit_casualties(battle_report)
        
        return {
            "success": success,
            "message": main_message,
            "battle_report": battle_report,
            "territory_changed": battle_report.territory_changed,
            "resources_captured": battle_report.resources_captured
        }
    
    def _apply_unit_casualties(self, battle_report: BattleReport):
        """Apply casualties to actual military units"""
        # Apply casualties to attacker units
        attacker_manager = self.military_managers.get(battle_report.attacker)
        if attacker_manager and battle_report.attacker_casualties > 0:
            attacker_station = battle_report.attacker_station or battle_report.attacker
            self._damage_units_at_station(
                attacker_manager, 
                attacker_station,
                battle_report.attacker_casualties
            )
        
        # Apply casualties to defender units  
        defender_manager = self.military_managers.get(battle_report.defender)
        if defender_manager and battle_report.defender_casualties > 0:
            defender_station = battle_report.defender_station or battle_report.defender
            self._damage_units_at_station(
                defender_manager,
                defender_station,
                battle_report.defender_casualties
            )
    
    def _damage_units_at_station(self, military_manager: MilitaryManager, station: str, total_damage: int):
        """Apply damage to units at a station"""
        units = military_manager.get_units_at_station(station)
        if not units:
            return
        
        # Distribute damage among units
        damage_per_unit = total_damage // len(units)
        remaining_damage = total_damage % len(units)
        
        for i, unit in enumerate(units):
            unit_damage = damage_per_unit
            if i < remaining_damage:
                unit_damage += 1
            
            # Convert casualties to damage (rough conversion)
            health_damage = min(100, unit_damage * 10)  # Scale damage appropriately
            
            destroyed = unit.take_damage(health_damage)
            if destroyed:
                self.logger.info(f"{unit.unit_type.value} unit destroyed at {station}")
            else:
                # Reduce morale for surviving units
                unit.modify_morale(-10)
                self.logger.debug(f"{unit.unit_type.value} unit damaged at {station}: {unit.health}% health")
        
        # Remove destroyed units
        military_manager.remove_destroyed_units()
    
    def use_mgr_in_combat(self, force: CombatForce, mgr_amount: int) -> CombatForce:
        """Use MGR rounds to boost combat effectiveness"""
        if mgr_amount <= 0:
            return force
        
        # MGR provides temporary bonuses
        mgr_bonus = min(mgr_amount // 5, 20)  # 1 bonus per 5 MGR, max 20
        
        # Apply bonuses
        force.equipment_quality = min(10, force.equipment_quality + mgr_bonus // 4)
        force.morale = min(100, force.morale + mgr_bonus // 2)
        force.leadership = min(10, force.leadership + mgr_bonus // 10)
        
        self.logger.info(f"Used {mgr_amount} MGR for combat bonuses: +{mgr_bonus // 4} equipment, +{mgr_bonus // 2} morale")
        
        return force
    
    def get_combat_modifiers_for_units(self, units: List) -> Dict[str, int]:
        """Get combat modifiers from unit special abilities"""
        modifiers = {
            "assault_bonus": 0,
            "defensive_bonus": 0,
            "morale_bonus": 0,
            "equipment_bonus": 0
        }
        
        for unit in units:
            # Unit-specific bonuses
            if unit.has_ability("assault"):
                modifiers["assault_bonus"] += 5
            if unit.has_ability("heavy_weapons"):
                modifiers["equipment_bonus"] += 2
            if unit.has_ability("elite_training"):
                modifiers["morale_bonus"] += 10
            if unit.has_ability("tunnel_warfare"):
                modifiers["assault_bonus"] += 3
                modifiers["defensive_bonus"] += 3
            if unit.has_ability("leadership"):
                modifiers["morale_bonus"] += 5
        
        return modifiers
    
    def get_battle_history(self, limit: int = 10) -> List[BattleReport]:
        """Get recent battle history"""
        return self.battle_history[-limit:]
    
    def get_faction_military_strength(self, faction: str) -> Dict[str, Any]:
        """Get military strength assessment for a faction"""
        faction_stations = [station for station in self.metro_map.stations.values() 
                          if station.controlling_faction == faction]
        
        total_manpower = 0
        total_defensive_value = 0
        military_stations = 0
        
        for station in faction_stations:
            force = self._create_combat_force(station.name, faction, True)
            total_manpower += force.manpower
            total_defensive_value += force.defensive_bonus
            
            from data.infrastructure import BuildingType
            if BuildingType.BARRACKS in station.infrastructure or BuildingType.FORTIFICATIONS in station.infrastructure:
                military_stations += 1
        
        return {
            "faction": faction,
            "total_stations": len(faction_stations),
            "military_stations": military_stations,
            "total_manpower": total_manpower,
            "average_defensive_value": total_defensive_value // max(1, len(faction_stations)),
            "equipment_quality": self._get_faction_equipment_quality(faction),
            "leadership_quality": self._get_faction_leadership(faction)
        }
    
    def get_attack_preview(self, origin: str, target: str, attacker_faction: str) -> Dict[str, Any]:
        """Get preview of potential attack outcome"""
        can_attack, reason = self.can_attack(attacker_faction, target)
        if not can_attack:
            return {"valid": False, "reason": reason}
        
        # Create forces for preview
        attacker_force = self._create_combat_force(origin, attacker_faction, False)
        defender_force = self._create_combat_force(target, None, True)
        
        attacker_strength = attacker_force.get_total_strength()
        defender_strength = defender_force.get_total_strength()
        
        # Calculate rough odds
        total_strength = attacker_strength + defender_strength
        if total_strength == 0:
            success_chance = 50
        else:
            success_chance = int((attacker_strength / total_strength) * 100)
        
        # Estimate costs
        attack_cost = self._calculate_attack_cost(origin, target, AttackType.ASSAULT)
        estimated_casualties = int(attacker_force.manpower * 0.15)  # Rough estimate
        
        return {
            "valid": True,
            "attacker_strength": attacker_strength,
            "defender_strength": defender_strength,
            "success_chance": success_chance,
            "attack_cost": attack_cost,
            "estimated_casualties": estimated_casualties,
            "defender_faction": self.metro_map.get_station(target).controlling_faction
        }