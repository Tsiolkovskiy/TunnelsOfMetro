# Metro Universe Strategy Game - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Game Interface](#game-interface)
3. [Resource Management](#resource-management)
4. [Faction System](#faction-system)
5. [Military Operations](#military-operations)
6. [Diplomacy](#diplomacy)
7. [Station Development](#station-development)
8. [Victory Conditions](#victory-conditions)
9. [Advanced Strategies](#advanced-strategies)
10. [Troubleshooting](#troubleshooting)

## Getting Started

### First Launch
1. Run `python launch.py` to start the game
2. The game will initialize and show the main map
3. You start as the Rangers faction with control of several stations
4. Your initial resources and units will be displayed in the HUD

### Understanding the Map
- **Green Stations**: Your controlled stations
- **Red Stations**: Hostile faction stations
- **Blue Stations**: Neutral or allied faction stations
- **Gray Tunnels**: Clear passages
- **Yellow Tunnels**: Hazardous but passable
- **Red Tunnels**: Dangerous or blocked passages

### Basic Controls
- **Left Click**: Select stations and UI elements
- **Right Click**: Open action menu for selected station
- **Mouse Wheel**: Zoom in/out (if implemented)
- **SPACE**: End your turn
- **ESC**: Exit game

## Game Interface

### HUD Elements
- **Top Left**: Resource display (Food, Water, Scrap, Medicine)
- **Top Right**: MGR Rounds counter and turn information
- **Bottom**: Message feed showing recent events and actions
- **Right Side**: Station information panel (when station selected)

### Action Interface
When you select a station, available actions appear:
- **Scout (S)**: Gather intelligence on adjacent stations
- **Trade (T)**: Establish trade routes or send caravans
- **Attack (A)**: Launch military assault on enemy stations
- **Diplomacy (D)**: Improve relations with other factions
- **Recruit (R)**: Train new military units
- **Build (B)**: Construct infrastructure buildings
- **Fortify (F)**: Improve station defenses

### Message System
- **Green Messages**: Successful actions and positive events
- **Red Messages**: Failed actions and negative events
- **Yellow Messages**: Warnings and important information
- **Blue Messages**: General information and turn updates

## Resource Management

### The Five Resources

#### Food
- **Purpose**: Feeds your population and military units
- **Sources**: Mushroom farms, trade, scavenging
- **Consumption**: 1 unit per person per turn
- **Critical Level**: Below 20 units
- **Tips**: Build mushroom farms early, maintain food reserves

#### Clean Water
- **Purpose**: Essential for health and morale
- **Sources**: Water filters, trade, natural sources
- **Consumption**: 0.8 units per person per turn
- **Critical Level**: Below 10 units
- **Tips**: Water contamination events are common, have backups

#### Scrap
- **Purpose**: Construction material and equipment repairs
- **Sources**: Scrap workshops, salvage operations, trade
- **Consumption**: Used for building and unit equipment
- **Critical Level**: Below 15 units
- **Tips**: Essential for infrastructure development

#### Medicine
- **Purpose**: Treats illness and maintains high morale
- **Sources**: Medical bays, trade, rare finds
- **Consumption**: 0.05 units per person per turn
- **Critical Level**: Below 5 units
- **Tips**: Stockpile for medical emergencies and events

#### MGR Rounds (Military-Grade Rounds)
- **Purpose**: Premium currency for advanced equipment and emergencies
- **Sources**: Trade, military victories, rare events
- **Consumption**: Used for high-end military equipment and crisis resolution
- **Critical Level**: Below 10 units
- **Tips**: MGR is scarce - use wisely for critical situations

### Resource Tips
1. **Balance is Key**: Don't focus on just one resource
2. **Plan for Growth**: Resource needs increase with population
3. **Emergency Reserves**: Keep 20% extra for unexpected events
4. **Trade Wisely**: Use abundant resources to get scarce ones
5. **Infrastructure Investment**: Buildings provide long-term benefits

## Faction System

### Major Factions

#### Red Line (Communist)
- **Government**: Stalinist Communist
- **Strengths**: Strong military, high morale through commissars
- **Weaknesses**: Higher food consumption, political rigidity
- **Special**: Commissariat system - deploy political officers
- **Relations**: Hostile to Fourth Reich, neutral to others initially

#### Fourth Reich (Fascist)
- **Government**: Nazi Fascist
- **Strengths**: Superior military discipline and equipment
- **Weaknesses**: Population control reduces growth
- **Special**: Purity Doctrine - population control for military bonuses
- **Relations**: Hostile to Red Line and Polis, neutral to Hanza

#### Hanza (Capitalist)
- **Government**: Merchant Oligarchy
- **Strengths**: Excellent trade networks, high MGR generation
- **Weaknesses**: Weaker military, corruption issues
- **Special**: Toll System - collect fees from trade routes
- **Relations**: Generally neutral, prefers trade to war

#### Polis (Democratic)
- **Government**: Democratic Republic
- **Strengths**: Efficient governance, good research capabilities
- **Weaknesses**: Slower decision-making, less military focus
- **Special**: Council Democracy - democratic efficiency bonuses
- **Relations**: Hostile to Fourth Reich, friendly to Rangers

#### Rangers (Player)
- **Government**: Military Republic
- **Strengths**: Elite training, diplomatic neutrality, balanced approach
- **Weaknesses**: Smaller starting territory, limited initial resources
- **Special**: Elite Training - superior scouting and survival skills
- **Relations**: Neutral mediator, can ally with most factions

### Faction Relationships
- **Allied**: +20% trade efficiency, military support available
- **Friendly**: +10% trade efficiency, diplomatic cooperation
- **Neutral**: Standard interactions, no bonuses or penalties
- **Unfriendly**: -10% trade efficiency, increased tension
- **Hostile**: No trade possible, military conflict likely

## Military Operations

### Unit Types

#### Militia
- **Cost**: Low (5 Food, 3 Scrap)
- **Strength**: Basic
- **Special**: Cheap to maintain, good for garrison duty
- **Best Use**: Station defense, early game expansion

#### Conscripts
- **Cost**: Medium (8 Food, 5 Scrap, 2 Medicine)
- **Strength**: Moderate
- **Special**: Balanced unit, reliable in most situations
- **Best Use**: Main battle force, offensive operations

#### Scouts
- **Cost**: Medium (10 Food, 8 Scrap)
- **Strength**: Low combat, high mobility
- **Special**: Enhanced scouting range, stealth capabilities
- **Best Use**: Intelligence gathering, reconnaissance

#### Stormtroopers
- **Cost**: High (20 Food, 15 Scrap, 8 Medicine, 5 MGR)
- **Strength**: Very High
- **Special**: Elite combat effectiveness, special equipment
- **Best Use**: Critical battles, breakthrough operations

### Combat System
- **Attacker Advantage**: Attacking units get initiative
- **Defender Bonus**: Defending units get fortification bonuses
- **Numbers Matter**: More units provide significant advantages
- **Quality Counts**: Elite units can overcome numerical disadvantages
- **Equipment**: MGR-equipped units have combat bonuses
- **Morale**: High morale units fight more effectively

### Military Strategy
1. **Combined Arms**: Use different unit types together
2. **Intelligence**: Scout before attacking
3. **Logistics**: Ensure supply lines for distant operations
4. **Timing**: Coordinate attacks with diplomatic situations
5. **Reserves**: Keep some units for defense and emergencies

## Diplomacy

### Diplomatic Actions

#### Improve Relations
- **Cost**: 15 MGR or equivalent resources
- **Effect**: Increases relationship level over time
- **Success Rate**: Based on current relations and faction compatibility
- **Tips**: Easier with compatible ideologies

#### Trade Agreement
- **Cost**: Negotiation time and resources
- **Effect**: Establishes regular resource exchange
- **Benefits**: Steady resource income, improved relations
- **Tips**: Offer resources they need, ask for what you lack

#### Military Alliance
- **Cost**: High diplomatic investment
- **Effect**: Mutual defense pact, shared military operations
- **Benefits**: Military support, coordinated attacks
- **Requirements**: Friendly or Allied relationship level

#### Non-Aggression Pact
- **Cost**: Moderate diplomatic investment
- **Effect**: Prevents direct military conflict
- **Benefits**: Secure borders, focus on other threats
- **Duration**: Usually 10-20 turns

### Diplomatic Strategy
1. **Know Your Neighbors**: Understand faction ideologies and goals
2. **Build Gradually**: Improve relations step by step
3. **Mutual Benefit**: Ensure agreements benefit both parties
4. **Honor Agreements**: Breaking deals damages reputation
5. **Strategic Timing**: Use diplomacy to prevent multi-front wars

## Station Development

### Infrastructure Buildings

#### Mushroom Farm
- **Cost**: 15 Scrap, 5 Clean Water
- **Effect**: +2 Food production per turn
- **Upgrade**: Higher levels increase production
- **Priority**: High - essential for food security

#### Water Filter
- **Cost**: 25 Scrap, 2 MGR
- **Effect**: +1.5 Clean Water production per turn
- **Upgrade**: Improved efficiency and capacity
- **Priority**: High - water is critical for health

#### Scrap Workshop
- **Cost**: 20 Scrap, 10 Food
- **Effect**: +1.8 Scrap production per turn
- **Upgrade**: Better tools and efficiency
- **Priority**: Medium - needed for construction

#### Medical Bay
- **Cost**: 35 Scrap, 15 Clean Water, 3 MGR
- **Effect**: +1.2 Medicine production per turn, health bonuses
- **Upgrade**: Advanced medical equipment
- **Priority**: Medium - important for crises

#### Barracks
- **Cost**: 50 Scrap, 20 Food, 8 MGR
- **Effect**: Enables unit recruitment, training bonuses
- **Upgrade**: Better equipment and training facilities
- **Priority**: High for military strategy

#### Fortifications
- **Cost**: 75 Scrap, 12 MGR
- **Effect**: +defensive value, combat bonuses for defenders
- **Upgrade**: Stronger defenses, artillery positions
- **Priority**: High for border stations

#### Market
- **Cost**: 40 Scrap, 25 Food, 15 MGR
- **Effect**: +0.5 MGR production per turn, trade bonuses
- **Upgrade**: Larger trading capacity
- **Priority**: Medium - good for economic strategy

### Development Strategy
1. **Basic Needs First**: Food and water production
2. **Security Second**: Fortifications for border stations
3. **Economic Growth**: Markets and workshops for expansion
4. **Military Capability**: Barracks for unit production
5. **Specialization**: Focus stations on specific roles

## Victory Conditions

### Political Victory - Metro Unification
- **Goal**: Unite all major factions under a single banner
- **Requirements**: 
  - 4+ allied factions
  - Control 12+ stations (80% of Metro)
  - 8+ diplomatic agreements
  - 75+ reputation across Metro
  - Maintain unity for 5 turns
- **Strategy**: Focus on diplomacy, avoid military conflicts, build trust
- **Timeline**: 60-80 turns typically

### Military Victory - Metro Conquest
- **Goal**: Conquer and control the majority of Metro stations
- **Requirements**:
  - Control 11+ stations (70% of Metro)
  - 500+ military strength
  - 15+ battles won
  - 3+ enemy factions defeated
  - 6+ fortified stations
- **Strategy**: Build strong military, strategic conquests, secure supply lines
- **Timeline**: 50-70 turns typically

### Economic Victory - Economic Dominance
- **Goal**: Control the Metro's economy through trade networks
- **Requirements**:
  - 1000+ MGR reserves
  - 10+ trade routes
  - 5+ market stations
  - 200+ resource production capacity
  - 12+ trade agreements
  - 80%+ economic influence
- **Strategy**: Focus on trade, build markets, establish trade networks
- **Timeline**: 70-90 turns typically

### Survival Victory - Metro Survival
- **Goal**: Survive the harsh Metro environment and outlast all threats
- **Requirements**:
  - Survive 100 turns
  - Maintain 1000+ population
  - 80%+ resource security
  - Survive 10+ major crises
  - 50+ infrastructure level
  - 75%+ faction stability
- **Strategy**: Balanced development, crisis preparation, steady growth
- **Timeline**: Exactly 100 turns

### Technological Victory - Technological Renaissance
- **Goal**: Lead the Metro into a new age through knowledge
- **Requirements**:
  - 4+ libraries built
  - 8+ research projects completed
  - 100+ knowledge preserved
  - 6+ technology shared with factions
  - 3+ anomaly research completed
  - Re-establish surface contact
- **Strategy**: Focus on research, build libraries, share knowledge
- **Timeline**: 80-100 turns typically

## Advanced Strategies

### Early Game (Turns 1-20)
1. **Secure Resources**: Build mushroom farms and water filters
2. **Explore Safely**: Scout adjacent stations, avoid conflicts
3. **Build Relations**: Establish contact with all factions
4. **Develop Core**: Focus on 2-3 key stations initially
5. **Plan Strategy**: Decide on victory condition focus

### Mid Game (Turns 21-60)
1. **Expand Carefully**: Take strategic stations, avoid overextension
2. **Specialize Stations**: Develop stations for specific purposes
3. **Form Alliances**: Secure at least one major ally
4. **Build Military**: Prepare for inevitable conflicts
5. **Economic Growth**: Establish trade networks and markets

### Late Game (Turns 61-100)
1. **Victory Push**: Focus all efforts on chosen victory condition
2. **Crisis Management**: Handle major events and challenges
3. **Final Conflicts**: Resolve remaining hostile relationships
4. **Resource Security**: Ensure sustainable resource production
5. **Endgame Preparation**: Prepare for victory condition requirements

### Faction-Specific Strategies

#### Playing Against Red Line
- **Strengths**: Strong military, high morale
- **Weaknesses**: Food consumption, political rigidity
- **Counter**: Economic pressure, avoid direct military confrontation
- **Diplomacy**: Difficult but possible with shared enemies

#### Playing Against Fourth Reich
- **Strengths**: Military discipline, equipment quality
- **Weaknesses**: Population control, international isolation
- **Counter**: Coalition building, exploit population issues
- **Diplomacy**: Very difficult, usually requires military solution

#### Playing Against Hanza
- **Strengths**: Economic power, trade networks
- **Weaknesses**: Military weakness, corruption
- **Counter**: Military pressure, disrupt trade routes
- **Diplomacy**: Easiest faction to negotiate with

#### Playing Against Polis
- **Strengths**: Efficiency, research capability
- **Weaknesses**: Slow decisions, military weakness
- **Counter**: Quick decisive actions, military pressure
- **Diplomacy**: Natural ally, shared democratic values

## Troubleshooting

### Performance Issues
- **Low FPS**: Press F3 to check performance, lower graphics settings
- **Stuttering**: Disable particle effects, reduce UI scale
- **Memory Issues**: Restart game periodically during long sessions

### Gameplay Issues
- **Can't End Turn**: Check for pending events or required actions
- **Actions Unavailable**: Verify resource requirements and station control
- **Save/Load Problems**: Ensure write permissions in game directory

### Common Mistakes
1. **Overexpansion**: Taking too many stations without proper development
2. **Resource Neglect**: Focusing on one resource while others become critical
3. **Military Weakness**: Not building enough military for defense
4. **Diplomatic Isolation**: Making enemies of all factions
5. **Event Unpreparedness**: Not keeping emergency reserves for crises

### Getting Help
- Check the console output for error messages
- Review the logs/launcher.log file for detailed information
- Ensure all game files are present and unmodified
- Verify Python and Pygame versions meet requirements

---

**Remember**: The Metro is unforgiving, but with careful planning, strategic thinking, and adaptability, you can lead humanity to a brighter future in the underground world.