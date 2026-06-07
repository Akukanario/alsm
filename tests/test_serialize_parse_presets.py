import os
import json
import configparser
from pathlib import Path
import pytest

from PyQt6.QtWidgets import QApplication

from src.alsm.main import ServerEditorDialog
from src.alsm import ini_templates

app = None


def get_qapp():
    global app
    if not QApplication.instance():
        app = QApplication([])
    return QApplication.instance()


def test_serialize_parse_roundtrip(tmp_path):
    get_qapp()
    dlg = ServerEditorDialog()
    # ensure some known widgets exist
    dlg.extra_settings[('ServerSettings', 'MaxPlayers')].setValue(42)
    dlg.extra_settings[('ServerSettings', 'PlayerDamageMultiplier')].setValue(1.5)
    dlg.extra_settings[('ServerSettings', 'XPMultiplier')].setValue(2.0)
    dlg.extra_settings[('ServerSettings', 'DinoCountMultiplier')].setValue(0.8)
    dlg.extra_settings[('ServerSettings', 'HarvestAmountMultiplier')].setValue(1.25)
    dlg.extra_settings[('ServerSettings', 'DayCycleSpeedScale')].setValue(1.1)

    # serialize to INI text
    dlg.serialize_from_fields()
    ini_text = dlg.usersettings_content.toPlainText()
    assert 'maxplayers' in ini_text.lower()

    # change widget values to different ones
    dlg.extra_settings[('ServerSettings', 'MaxPlayers')].setValue(10)
    dlg.extra_settings[('ServerSettings', 'PlayerDamageMultiplier')].setValue(1.0)
    dlg.extra_settings[('ServerSettings', 'XPMultiplier')].setValue(1.0)

    # load from serialized text and parse
    dlg.usersettings_content.setPlainText(ini_text)
    # register lowercase aliases so parse_ini (which lowercases keys) finds widgets
    dlg.extra_settings[('ServerSettings', 'maxplayers')] = dlg.extra_settings[('ServerSettings', 'MaxPlayers')]
    dlg.extra_settings[('ServerSettings', 'playerdamagemultiplier')] = dlg.extra_settings[('ServerSettings', 'PlayerDamageMultiplier')]
    dlg.extra_settings[('ServerSettings', 'xpmultiplier')] = dlg.extra_settings[('ServerSettings', 'XPMultiplier')]
    dlg.parse_ini()

    assert int(dlg.extra_settings[('ServerSettings', 'MaxPlayers')].value()) == 42
    assert float(dlg.extra_settings[('ServerSettings', 'PlayerDamageMultiplier')].value()) == pytest.approx(1.5)
    assert float(dlg.extra_settings[('ServerSettings', 'XPMultiplier')].value()) == pytest.approx(2.0)


def test_save_and_apply_preset_includes_gameini_and_mods(tmp_path):
    # prepare a preset payload
    name = 'test-preset-auto'
    preset = {
        'ServerSettings': {
            'MaxPlayers': '16',
            'DayCycleSpeedScale': '0.9'
        },
        'gameini': '[UnrealEd.Types]\n+SomeClass=1',
        'mods': ['123456789', '987654321']
    }
    # save preset using ini_templates.save_preset (writes to presets dir)
    ok = ini_templates.save_preset(name, preset)
    assert ok
    # verify load_presets contains it
    presets = ini_templates.load_presets()
    assert name in presets
    # apply via dialog
    get_qapp()
    dlg = ServerEditorDialog()
    dlg.apply_preset_by_name(name)
    # verify fields populated
    assert 'maxplayers' in dlg.usersettings_content.toPlainText().lower()
    assert '[UnrealEd.Types]' in dlg.gameini_content.toPlainText()
    mods_txt = dlg.mods_list.toPlainText().splitlines()
    assert '123456789' in mods_txt
    # cleanup created preset file
    fn = Path(__file__).resolve().parents[1] / 'src' / 'alsm' / 'presets' / f"{name}.json"
    try:
        if fn.exists():
            fn.unlink()
    except Exception:
        pass
