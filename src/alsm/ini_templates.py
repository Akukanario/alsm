import configparser
import json
from pathlib import Path

PRESETS = {
    'PvE': {
        'ServerSettings': {
            'ServerAdminPassword': '',
            'MaxPlayers': '50',
            'AllowThirdPersonPlayer': 'False',
            'DisableStructureDecayPvE': 'True',
            'DayCycleSpeedScale': '1.0',
            'NightTimeSpeedScale': '1.0',
            'DinoCountMultiplier': '1.0',
            'HarvestAmountMultiplier': '1.0',
        }
    },
    'PvP': {
        'ServerSettings': {
            'ServerAdminPassword': '',
            'MaxPlayers': '70',
            'AllowThirdPersonPlayer': 'False',
            'DisableStructureDecayPvE': 'False',
            'DayCycleSpeedScale': '1.0',
            'NightTimeSpeedScale': '1.0',
            'DinoCountMultiplier': '1.5',
            'HarvestAmountMultiplier': '1.2',
        }
    },
    'LowPop': {
        'ServerSettings': {
            'ServerAdminPassword': '',
            'MaxPlayers': '20',
            'AllowThirdPersonPlayer': 'False',
            'DisableStructureDecayPvE': 'True',
            'DayCycleSpeedScale': '0.75',
            'NightTimeSpeedScale': '0.75',
            'DinoCountMultiplier': '0.6',
            'HarvestAmountMultiplier': '0.8',
        }
    }
}


def preset_to_ini_text(name: str) -> str:
    cfg = configparser.ConfigParser()
    preset = PRESETS.get(name)
    if not preset:
        return ''
    for section, items in preset.items():
        cfg[section] = {}
        for k, v in items.items():
            cfg[section][k] = str(v)
    from io import StringIO
    s = StringIO()
    cfg.write(s)
    return s.getvalue()


PRESETS_DIR = Path(__file__).parent / 'presets'


def load_presets() -> dict:
    # return a merged dict of built-in PRESETS and on-disk presets
    out = dict(PRESETS)
    try:
        PRESETS_DIR.mkdir(parents=True, exist_ok=True)
        for fn in PRESETS_DIR.glob('*.json'):
            try:
                with open(fn, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                name = data.get('name') or fn.stem
                out[name] = data.get('preset', {})
            except Exception:
                continue
    except Exception:
        pass
    return out


def save_preset(name: str, preset: dict) -> bool:
    try:
        PRESETS_DIR.mkdir(parents=True, exist_ok=True)
        payload = {'name': name, 'preset': preset}
        fn = PRESETS_DIR / f"{name}.json"
        with open(fn, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False
