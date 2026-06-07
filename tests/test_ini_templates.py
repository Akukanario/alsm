import sys
from pathlib import Path


ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'src'))

from alsm import ini_templates  # type: ignore


def test_preset_to_ini_text_known():
    text = ini_templates.preset_to_ini_text('PvE')
    assert text
    assert 'ServerSettings' in text
    assert 'maxplayers = 50' in text


def test_preset_to_ini_text_unknown():
    assert ini_templates.preset_to_ini_text('NoExiste') == ''


def test_save_and_load(tmp_path):
    name = 'test_custom_preset'
    preset = {'ServerSettings': {'MaxPlayers': '5'}}
    original = ini_templates.PRESETS_DIR
    try:
        ini_templates.PRESETS_DIR = tmp_path
        res = ini_templates.save_preset(name, preset)
        assert res is True
        loaded = ini_templates.load_presets()
        assert name in loaded
        assert loaded[name] == preset
    finally:
        ini_templates.PRESETS_DIR = original
