# Metro Universe Strategy Game

A turn-based strategy game set in the post-apocalyptic Moscow Metro system, inspired by Dmitry Glukhovsky's Metro series.

## Overview

Lead the Rangers faction through the dangerous tunnels of the Moscow Metro, managing resources, building alliances, and fighting for survival in a world devastated by nuclear war. Navigate complex faction politics, manage scarce resources, and make critical decisions that will determine the fate of humanity's underground civilization.

## Features

### Core Gameplay
- **Turn-based Strategy**: Plan your moves carefully in a challenging turn-based environment
- **Resource Management**: Manage five critical resources - Food, Clean Water, Scrap, Medicine, and MGR Rounds
- **Faction Politics**: Interact with major Metro factions including Red Line, Fourth Reich, Hanza, and Polis
- **Multiple Victory Paths**: Achieve victory through Political Unity, Military Conquest, Economic Dominance, Survival, or Technological Advancement

### Game Systems
- **Dynamic Events**: Random events that challenge your decision-making and adaptability
- **Military Management**: Recruit and manage different unit types with unique capabilities
- **Station Development**: Build infrastructure to improve resource production and station capabilities
- **Diplomacy System**: Form alliances, improve relations, or declare war on other factions
- **Trade Networks**: Establish trade routes and manage caravans for economic growth
- **Scouting System**: Explore the Metro and gather intelligence on other factions

### Technical Features
- **Performance Optimized**: Smooth 30 FPS gameplay with advanced rendering optimizations
- **Audio & Visual Effects**: Immersive sound effects and particle systems for enhanced feedback
- **Save/Load System**: Multiple save slots with comprehensive game state persistence
- **Settings Management**: Customizable graphics, audio, and gameplay options
- **AI Opponents**: Intelligent AI factions with unique personalities and strategies

## Installation

### Requirements
- Python 3.8 or higher
- Pygame 2.0 or higher
- NumPy (optional, for enhanced audio effects)

### Setup
1. Clone or download the game files
2. Install required dependencies:
   ```bash
   pip install pygame numpy
   ```
3. Run the game:
   ```bash
   python main.py
   ```

## Controls

### Basic Controls
- **Mouse**: Click to select stations and interact with UI elements
- **Right-click**: Open action menu for selected station
- **SPACE**: End turn
- **ESC**: Exit game

### Keyboard Shortcuts
- **S**: Scout action
- **T**: Trade action
- **A**: Attack action
- **D**: Diplomacy action
- **R**: Recruit units
- **B**: Build infrastructure
- **F**: Fortify station

### System Controls
- **F3**: Toggle performance overlay
- **F4**: Generate performance report
- **F5**: Quick save
- **F9**: Quick load (when implemented)
- **H**: Toggle HUD visibility
- **M**: Toggle message feed
- **L**: Toggle map legend

## Gameplay Guide

### Getting Started
1. **Learn the Interface**: Familiarize yourself with the HUD showing resources, turn counter, and faction information
2. **Explore the Map**: Click on stations to see their status and available actions
3. **Manage Resources**: Keep an eye on your Food, Water, Scrap, Medicine, and MGR supplies
4. **Plan Your Strategy**: Decide whether to focus on military expansion, diplomatic unity, or economic growth

### Resource Management
- **Food**: Essential for population survival and military unit maintenance
- **Clean Water**: Required for health and morale, affects population growth
- **Scrap**: Used for construction, repairs, and equipment manufacturing
- **Medicine**: Critical for health crises and maintaining high morale
- **MGR Rounds**: Premium currency for advanced equipment and emergency situations

### Faction Interactions
Each faction has unique characteristics:
- **Red Line**: Communist faction with strong military and commissariat system
- **Fourth Reich**: Fascist faction with superior military discipline but population control
- **Hanza**: Capitalist traders with extensive trade networks and toll systems
- **Polis**: Democratic faction with efficient governance and research capabilities
- **Rangers**: Elite military faction (player) with superior training and diplomatic neutrality

### Victory Conditions
- **Political Victory**: Unite all major factions through diplomacy and alliance
- **Military Victory**: Conquer the majority of Metro stations through force
- **Economic Victory**: Control the Metro's economy through trade dominance
- **Survival Victory**: Outlast all challenges for 100 turns while maintaining stability
- **Technological Victory**: Lead the Metro into a new age through knowledge and research

### Tips for Success
1. **Balance Resources**: Don't focus on just one resource - maintain a balanced economy
2. **Build Infrastructure**: Invest in buildings that provide long-term resource generation
3. **Maintain Relationships**: Even if pursuing military victory, some allies are valuable
4. **Scout Regularly**: Information is power - know what your neighbors are doing
5. **Plan for Events**: Keep emergency reserves for unexpected crises
6. **Adapt Your Strategy**: Be flexible and adjust your approach based on circumstances

## Advanced Features

### Faction Mechanics
Each faction has unique special abilities:
- **Red Line Commissariat**: Deploy political officers to boost morale
- **Fourth Reich Purity Doctrine**: Population control for military bonuses
- **Hanza Toll System**: Collect fees from trade routes
- **Polis Council Democracy**: Democratic efficiency bonuses
- **Rangers Elite Training**: Superior scouting and survival capabilities

### MGR Scarcity System
Military-Grade Rounds are the premium currency with dynamic pricing:
- **Global Supply**: Limited MGR supply affects pricing across the Metro
- **Regional Availability**: Different stations have different MGR access
- **Quality Levels**: MGR comes in different quality grades affecting value
- **Black Market**: Emergency MGR trading at premium prices during scarcity

### AI Personalities
AI factions have distinct personalities affecting their behavior:
- **Aggressive**: Focuses on military expansion and conquest
- **Defensive**: Prioritizes fortification and protection
- **Diplomatic**: Seeks alliances and peaceful solutions
- **Economic**: Focuses on trade and resource accumulation
- **Expansionist**: Constantly seeks to grow territory
- **Isolationist**: Prefers minimal external contact

## Technical Information

### Performance
- Target: 30 FPS on modest hardware
- Optimized rendering with batching and culling
- Configurable graphics quality settings
- Performance monitoring and automatic optimization

### Save System
- Multiple save slots with descriptive metadata
- Complete game state serialization
- Auto-save functionality (configurable frequency)
- Quick save/load for convenience

### Audio System
- Category-based volume control (Master, Music, SFX, UI)
- Positional audio support
- Dynamic sound effects for all game actions
- Atmospheric background music

## Troubleshooting

### Common Issues
1. **Game won't start**: Ensure Python 3.8+ and Pygame are installed
2. **Poor performance**: Lower graphics quality in settings or press F3 to monitor FPS
3. **No sound**: Check audio settings and ensure audio drivers are working
4. **Save/Load issues**: Ensure write permissions in the game directory

### Performance Optimization
- Lower graphics quality if experiencing frame drops
- Disable particle effects for better performance
- Reduce UI scale if interface elements are too large
- Use windowed mode instead of fullscreen if having display issues

### Debug Features
- Press F3 to show performance overlay
- Press F4 to log detailed performance report
- Check console output for error messages and debug information

## Development

### Architecture
The game is built with a modular architecture:
- **Core**: Game engine, configuration, and main loop
- **Data**: Game entities (stations, factions, resources, units)
- **Systems**: Game logic (diplomacy, combat, trade, AI, etc.)
- **UI**: User interface components and rendering
- **Utils**: Utilities for performance, optimization, and file management

### Extending the Game
The modular design makes it easy to add new features:
- New factions can be added by extending the Faction class
- Additional victory conditions can be implemented in the VictorySystem
- New events can be added to the EventSystem
- Custom AI personalities can be created in the AISystem

## Credits

### Inspiration
- **Dmitry Glukhovsky**: Creator of the Metro universe
- **4A Games**: Developers of the Metro video game series
- **Classic Strategy Games**: Civilization, Europa Universalis, Crusader Kings

### Development
- Built with Python and Pygame
- Uses modular architecture for maintainability
- Comprehensive testing suite for reliability
- Performance optimization for smooth gameplay

## License

This is a fan-made game inspired by the Metro universe. All rights to the Metro intellectual property belong to Dmitry Glukhovsky and associated rights holders.

## Version History

### v1.0.0 - Initial Release
- Complete turn-based strategy gameplay
- All major factions implemented with unique mechanics
- Five victory conditions available
- Comprehensive resource management system
- Dynamic event system with player choices
- AI opponents with distinct personalities
- Save/load functionality
- Performance optimization and audio/visual polish
- Comprehensive testing and bug fixes

---

**Survive the Metro. Unite the Factions. Determine Humanity's Future.**