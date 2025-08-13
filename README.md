# Metro Universe Strategy Game

A turn-based grand strategy survival game set in the post-apocalyptic Moscow Metro system, inspired by the Metro 2033 universe.

## Installation

1. Ensure you have Python 3.8+ installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Game

```bash
python main.py
```

## Controls

- **ESC**: Exit game
- **Mouse Click**: Select stations
- **S**: Scout selected station
- **T**: Trade with selected station
- **A**: Attack selected station
- **D**: Diplomacy with selected station

## Project Structure

```
metro_strategy_game/
├── main.py              # Main entry point
├── core/                # Core game engine and configuration
├── systems/             # Game systems (map, factions, resources, etc.)
├── data/                # Data models and game state
├── ui/                  # User interface components
├── utils/               # Utility functions and helpers
└── logs/                # Game logs (auto-generated)
```

## Development

This game is built using:
- **Python 3.8+**
- **Pygame** for graphics and input handling
- **Modular architecture** for maintainable code

## Features

- Interactive Moscow Metro map
- Multiple faction gameplay with unique mechanics
- Resource management (food, water, scrap, medicine, MGRs)
- Turn-based strategy with diplomatic, military, and economic options
- Dynamic events and political intrigue
- Multiple victory conditions