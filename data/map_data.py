"""
Metro Map Data
Contains the authentic Moscow Metro station data and connections
"""

from typing import Dict, List, Tuple, Any

from data.station import Station
from data.tunnel import Tunnel, TunnelState


class MetroMapData:
    """
    Contains authentic Moscow Metro data for game initialization
    Based on the Metro 2033 universe lore and real Moscow Metro system
    """
    
    @staticmethod
    def get_station_data() -> List[Dict[str, Any]]:
        """
        Get station data for map initialization
        
        Returns:
            List of station configuration dictionaries
        """
        return [
            {
                "name": "VDNKh",
                "position": (100, 100),
                "metro_line": "Kaluzhsko-Rizhskaya",
                "faction": "Rangers",
                "population": 150,
                "morale": 70,
                "special_traits": ["mushroom_cultivation", "exhibition_halls"]
            },
            {
                "name": "Polis",
                "position": (300, 200),
                "metro_line": "Sokolnicheskaya",
                "faction": "Polis",
                "population": 200,
                "morale": 80,
                "special_traits": ["great_library", "brahmin_council"]
            },
            {
                "name": "Tverskaya",
                "position": (400, 150),
                "metro_line": "Zamoskvoretskaya",
                "faction": "Fourth Reich",
                "population": 120,
                "morale": 60,
                "special_traits": ["military_discipline", "propaganda_center"]
            },
            {
                "name": "Preobrazhenskaya Ploshchad",
                "position": (500, 100),
                "metro_line": "Sokolnicheskaya",
                "faction": "Red Line",
                "population": 140,
                "morale": 65,
                "special_traits": ["communist_ideology", "workers_council"]
            },
            {
                "name": "Kurskaya",
                "position": (300, 300),
                "metro_line": "Arbatsko-Pokrovskaya",
                "faction": "Hanza",
                "population": 180,
                "morale": 75,
                "special_traits": ["major_hub", "trade_center"]
            },
            {
                "name": "Mayakovskaya",
                "position": (200, 150),
                "metro_line": "Zamoskvoretskaya",
                "faction": "Independent",
                "population": 100,
                "morale": 50,
                "special_traits": ["artistic_heritage", "neutral_ground"]
            },
            {
                "name": "Komsomolskaya",
                "position": (400, 250),
                "metro_line": "Koltsevaya",
                "faction": "Hanza",
                "population": 160,
                "morale": 70,
                "special_traits": ["ring_line_control", "transport_hub"]
            },
            {
                "name": "Park Kultury",
                "position": (200, 300),
                "metro_line": "Sokolnicheskaya",
                "faction": "Red Line",
                "population": 130,
                "morale": 60,
                "special_traits": ["cultural_center", "red_propaganda"]
            },
            {
                "name": "Kiyevskaya",
                "position": (100, 250),
                "metro_line": "Arbatsko-Pokrovskaya",
                "faction": "Polis",
                "population": 110,
                "morale": 65,
                "special_traits": ["diplomatic_outpost", "polis_influence"]
            },
            {
                "name": "Okhotny Ryad",
                "position": (350, 100),
                "metro_line": "Sokolnicheskaya",
                "faction": "Fourth Reich",
                "population": 100,
                "morale": 55,
                "special_traits": ["hunting_grounds", "reich_outpost"]
            },
            {
                "name": "Sokolniki",
                "position": (550, 200),
                "metro_line": "Sokolnicheskaya",
                "faction": "Red Line",
                "population": 90,
                "morale": 55,
                "special_traits": ["frontier_post", "red_military"]
            },
            {
                "name": "Lubyanka",
                "position": (450, 300),
                "metro_line": "Sokolnicheskaya",
                "faction": "Invisible Watchers",
                "population": 80,
                "morale": 40,
                "special_traits": ["secret_facility", "surveillance_center"]
            },
            {
                "name": "Teatralnaya",
                "position": (250, 250),
                "metro_line": "Zamoskvoretskaya",
                "faction": "Polis",
                "population": 120,
                "morale": 70,
                "special_traits": ["cultural_exchange", "theater_district"]
            },
            {
                "name": "Park Pobedy",
                "position": (150, 350),
                "metro_line": "Arbatsko-Pokrovskaya",
                "faction": "Rangers",
                "population": 110,
                "morale": 65,
                "special_traits": ["victory_memorial", "ranger_outpost"]
            },
            {
                "name": "Taganskaya",
                "position": (500, 350),
                "metro_line": "Tagansko-Krasnopresnenskaya",
                "faction": "Invisible Watchers",
                "population": 70,
                "morale": 35,
                "special_traits": ["hidden_bunker", "watcher_stronghold"]
            }
        ]
    
    @staticmethod
    def get_tunnel_connections() -> List[Dict[str, Any]]:
        """
        Get tunnel connection data for map initialization
        
        Returns:
            List of tunnel configuration dictionaries
        """
        return [
            # Main line connections
            {"station_a": "VDNKh", "station_b": "Mayakovskaya", "state": "clear", "metro_line": "Kaluzhsko-Rizhskaya"},
            {"station_a": "Mayakovskaya", "station_b": "Polis", "state": "clear", "metro_line": "Sokolnicheskaya"},
            {"station_a": "Polis", "station_b": "Kurskaya", "state": "clear", "metro_line": "Arbatsko-Pokrovskaya"},
            {"station_a": "Polis", "station_b": "Komsomolskaya", "state": "clear", "metro_line": "Koltsevaya"},
            {"station_a": "Polis", "station_b": "Park Kultury", "state": "clear", "metro_line": "Sokolnicheskaya"},
            {"station_a": "Polis", "station_b": "Teatralnaya", "state": "clear", "metro_line": "Zamoskvoretskaya"},
            {"station_a": "Polis", "station_b": "Kiyevskaya", "state": "clear", "metro_line": "Arbatsko-Pokrovskaya"},
            
            # Fourth Reich territory
            {"station_a": "Tverskaya", "station_b": "Okhotny Ryad", "state": "clear", "metro_line": "Sokolnicheskaya"},
            {"station_a": "Tverskaya", "station_b": "Komsomolskaya", "state": "clear", "metro_line": "Zamoskvoretskaya"},
            
            # Red Line territory
            {"station_a": "Preobrazhenskaya Ploshchad", "station_b": "Sokolniki", "state": "clear", "metro_line": "Sokolnicheskaya"},
            
            # Hanza Ring Line control
            {"station_a": "Kurskaya", "station_b": "Lubyanka", "state": "clear", "metro_line": "Koltsevaya"},
            {"station_a": "Kurskaya", "station_b": "Taganskaya", "state": "clear", "metro_line": "Tagansko-Krasnopresnenskaya"},
            {"station_a": "Komsomolskaya", "station_b": "Lubyanka", "state": "clear", "metro_line": "Koltsevaya"},
            
            # Additional connections
            {"station_a": "Park Kultury", "station_b": "Park Pobedy", "state": "clear", "metro_line": "Arbatsko-Pokrovskaya"},
            {"station_a": "Okhotny Ryad", "station_b": "Tverskaya", "state": "clear", "metro_line": "Sokolnicheskaya"},
            {"station_a": "Sokolniki", "station_b": "Preobrazhenskaya Ploshchad", "state": "clear", "metro_line": "Sokolnicheskaya"},
            {"station_a": "Teatralnaya", "station_b": "Polis", "state": "clear", "metro_line": "Zamoskvoretskaya"},
            {"station_a": "Park Pobedy", "station_b": "Kiyevskaya", "state": "clear", "metro_line": "Arbatsko-Pokrovskaya"},
            {"station_a": "Taganskaya", "station_b": "Lubyanka", "state": "clear", "metro_line": "Tagansko-Krasnopresnenskaya"},
            
            # Some hazardous/dangerous connections
            {"station_a": "Lubyanka", "station_b": "Teatralnaya", "state": "hazardous", "hazard_level": 30, "metro_line": "Sokolnicheskaya"},
            {"station_a": "Taganskaya", "station_b": "Park Pobedy", "state": "infested", "hazard_level": 50, "metro_line": "Arbatsko-Pokrovskaya"}
        ]
    
    @staticmethod
    def get_faction_relationships() -> Dict[str, Dict[str, int]]:
        """
        Get initial faction relationship matrix
        
        Returns:
            Dictionary mapping faction pairs to relationship values (-1 to 1)
        """
        return {
            "Rangers": {
                "Polis": 1,           # Allied
                "Fourth Reich": -1,   # At war
                "Red Line": -1,       # At war
                "Hanza": 0,          # Neutral
                "Invisible Watchers": 0,  # Neutral
                "Independent": 0      # Neutral
            },
            "Polis": {
                "Rangers": 1,         # Allied
                "Fourth Reich": 0,    # Neutral (diplomatic)
                "Red Line": 0,        # Neutral (diplomatic)
                "Hanza": 1,          # Allied (trade partners)
                "Invisible Watchers": -1,  # Suspicious
                "Independent": 0      # Neutral
            },
            "Fourth Reich": {
                "Rangers": -1,        # At war
                "Polis": 0,          # Neutral
                "Red Line": -1,       # Ideological enemies
                "Hanza": 0,          # Neutral (trade)
                "Invisible Watchers": 0,  # Unknown
                "Independent": -1     # Hostile to most
            },
            "Red Line": {
                "Rangers": -1,        # At war
                "Polis": 0,          # Neutral
                "Fourth Reich": -1,   # Ideological enemies
                "Hanza": 0,          # Neutral (reluctant trade)
                "Invisible Watchers": 0,  # Unknown
                "Independent": 0      # Neutral
            },
            "Hanza": {
                "Rangers": 0,         # Neutral
                "Polis": 1,          # Allied
                "Fourth Reich": 0,    # Neutral (trade)
                "Red Line": 0,        # Neutral (trade)
                "Invisible Watchers": 0,  # Unknown
                "Independent": 0      # Neutral
            },
            "Invisible Watchers": {
                "Rangers": 0,         # Unknown
                "Polis": -1,         # Suspicious of knowledge
                "Fourth Reich": 0,    # Manipulated
                "Red Line": 0,        # Manipulated
                "Hanza": 0,          # Unknown
                "Independent": 0      # Unknown
            },
            "Independent": {
                "Rangers": 0,         # Neutral
                "Polis": 0,          # Neutral
                "Fourth Reich": -1,   # Threatened
                "Red Line": 0,        # Neutral
                "Hanza": 0,          # Neutral
                "Invisible Watchers": 0  # Unknown
            }
        }
    
    @staticmethod
    def get_metro_lines() -> Dict[str, List[str]]:
        """
        Get Metro line organization
        
        Returns:
            Dictionary mapping line names to station lists
        """
        return {
            "Sokolnicheskaya": [
                "Park Kultury", "Polis", "Okhotny Ryad", 
                "Lubyanka", "Preobrazhenskaya Ploshchad", "Sokolniki"
            ],
            "Zamoskvoretskaya": [
                "Mayakovskaya", "Tverskaya", "Teatralnaya"
            ],
            "Arbatsko-Pokrovskaya": [
                "Kiyevskaya", "Park Pobedy", "Kurskaya"
            ],
            "Koltsevaya": [
                "Komsomolskaya", "Kurskaya", "Lubyanka"
            ],
            "Kaluzhsko-Rizhskaya": [
                "VDNKh"
            ],
            "Tagansko-Krasnopresnenskaya": [
                "Taganskaya"
            ]
        }