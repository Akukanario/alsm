"""
ASM settings inventory and recommended widget types for UI generation.

This file maps common ARK/ASM configuration keys to their INI section,
human description, and a recommended widget type for the GUI.

Used by the UI generator to add controls and wire them into `extra_settings`.
"""
from typing import Dict, Any

SETTINGS_MAP: Dict[str, Dict[str, Any]] = {
    'ServerSettings': {
        # System / general
        'ServerAdminPassword': {'type': 'string', 'desc': 'Admin password'},
        'MaxPlayers': {'type': 'int', 'desc': 'Maximum players'},
        'AllowThirdPersonPlayer': {'type': 'bool', 'desc': 'Allow third person view'},
        'DisableStructureDecayPvE': {'type': 'bool', 'desc': 'Disable structure decay on PvE'},
        'DayCycleSpeedScale': {'type': 'double', 'desc': 'Day cycle speed multiplier'},
        'NightTimeSpeedScale': {'type': 'double', 'desc': 'Night time speed multiplier'},
        # Rates
        'DinoCountMultiplier': {'type': 'double', 'desc': 'Dino spawn multiplier'},
        'HarvestAmountMultiplier': {'type': 'double', 'desc': 'Resource harvest multiplier'},
        'StructureDamageMultiplier': {'type': 'double', 'desc': 'Structure damage multiplier'},
        'XPMultiplier': {'type': 'double', 'desc': 'XP gain multiplier'},
        'TamingSpeedMultiplier': {'type': 'double', 'desc': 'Taming speed multiplier'},
        'DinoHarvestingDamageMultiplier': {'type': 'double', 'desc': 'Dino harvesting damage multiplier'},
        'MatingIntervalMultiplier': {'type': 'double', 'desc': 'Mating interval multiplier'},
        'BabyMatureSpeedMultiplier': {'type': 'double', 'desc': 'Baby maturation speed multiplier'},
        'BabyCuddleIntervalMultiplier': {'type': 'double', 'desc': 'Baby cuddle interval multiplier'},
        'BabyImprintingStatScaleMultiplier': {'type': 'double', 'desc': 'Baby imprinting stat scale multiplier'},
        # Player
        'PlayerDamageMultiplier': {'type': 'double', 'desc': 'Player damage multiplier'},
        'PlayerCharacterStaminaDrainMultiplier': {'type': 'double', 'desc': 'Stamina drain multiplier'},
        'PlayerCharacterWeightMultiplier': {'type': 'double', 'desc': 'Weight multiplier'},
        'PlayerCharacterTorporDrainMultiplier': {'type': 'double', 'desc': 'Torpor drain multiplier'},
        'PlayerCharacterFoodDrainMultiplier': {'type': 'double', 'desc': 'Food drain multiplier'},
        'PlayerCharacterWaterDrainMultiplier': {'type': 'double', 'desc': 'Water drain multiplier'},
        'PlayerCharacterJumpPowerMultiplier': {'type': 'double', 'desc': 'Player jump multiplier'},
        'PlayerCharacterRunSpeedMultiplier': {'type': 'double', 'desc': 'Player run speed multiplier'},
        # Dinos (general)
        'TamedDinoDamageMultiplier': {'type': 'double', 'desc': 'Tamed dino damage'},
        'TamedDinoResistanceMultiplier': {'type': 'double', 'desc': 'Tamed dino resistance'},
        'DinoCharacterFoodDrainMultiplier': {'type': 'double', 'desc': 'Dino food drain multiplier'},
        'DinoCharacterStaminaDrainMultiplier': {'type': 'double', 'desc': 'Dino stamina drain multiplier'},
        'DinoHarvestingDamageMultiplier': {'type': 'double', 'desc': 'Dino harvesting damage multiplier'},
        # Resources
        'ResourceRespawnPeriodMultiplier': {'type': 'double', 'desc': 'Resource respawn period multiplier'},
    },
    'Game.ini': {
        # Per-class / per-species overrides live here (not exhaustively listed)
        'PerLevelStatsMultiplier_Dino': {'type': 'string', 'desc': 'Per-level stat multipliers (dinos) - complex string'},
        'OverrideNamedEngramEntries': {'type': 'string', 'desc': 'Engram override entries - string/list'},
    },
    'ServerSettings_PVE': {},
}

COMMON_KEYS = [
    ('ServerSettings', k) for k in SETTINGS_MAP.get('ServerSettings', {}).keys()
]

def find_setting(section: str, key: str):
    return SETTINGS_MAP.get(section, {}).get(key)

__all__ = ['SETTINGS_MAP', 'COMMON_KEYS', 'find_setting']
