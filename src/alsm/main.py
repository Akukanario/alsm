import sys
import os
import configparser
from pathlib import Path

# Minimal, clean main for ALSM GUI
HAVE_QT = True
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
        QDialog, QFormLayout, QLineEdit, QSpinBox, QDialogButtonBox, QMessageBox,
        QCheckBox, QFileDialog, QTextEdit, QScrollArea, QSlider, QListWidget, QHBoxLayout
    )
    from PyQt6.QtWidgets import QComboBox, QDoubleSpinBox
    from PyQt6.QtCore import QTimer
    QT = 'PyQt6'
except Exception:
    try:
        from PySide6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
            QDialog, QFormLayout, QLineEdit, QSpinBox, QDialogButtonBox, QMessageBox,
            QCheckBox, QFileDialog, QTextEdit, QScrollArea, QSlider, QListWidget, QHBoxLayout
        )
        from PySide6.QtWidgets import QComboBox, QDoubleSpinBox
        from PySide6.QtCore import QTimer
        QT = 'PySide6'
    except Exception:
        HAVE_QT = False

if not HAVE_QT:
    def console_main():
        print('No Qt binding available. Install PyQt6 or PySide6 in the venv.')


if HAVE_QT:
    class CollapsibleSection(QWidget):
        def __init__(self, title, parent=None):
            super().__init__(parent)
            self.toggle = QPushButton(title)
            self.toggle.setCheckable(True)
            self.toggle.setChecked(False)
            self.toggle.setFlat(True)
            self.content = QWidget(self)
            self.content.setVisible(False)
            self.main = QVBoxLayout(self)
            self.main.setContentsMargins(0, 0, 0, 0)
            self.main.addWidget(self.toggle)
            self.main.addWidget(self.content)
            self.c_layout = QVBoxLayout(self.content)
            self.toggle.toggled.connect(self.content.setVisible)

        def addWidget(self, w):
            self.c_layout.addWidget(w)

    class ConnectDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle('SSH Connect')
            layout = QFormLayout(self)
            self.host = QLineEdit(self)
            layout.addRow('Host:', self.host)
            self.port = QSpinBox(self)
            self.port.setRange(1, 65535)
            self.port.setValue(22)
            layout.addRow('Port:', self.port)
            self.username = QLineEdit(self)
            layout.addRow('Username:', self.username)
            self.password = QLineEdit(self)
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addRow('Password:', self.password)
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            layout.addRow(buttons)

        def get_data(self):
            return {
                'host': self.host.text().strip(),
                'port': int(self.port.value()),
                'username': self.username.text().strip(),
                'password': self.password.text(),
            }


    class ServerEditorDialog(QDialog):
        def __init__(self, parent=None, server=None):
            super().__init__(parent)
            self.setWindowTitle('Server Editor')
            layout = QFormLayout(self)
            self.name = QLineEdit(self)
            layout.addRow('Name:', self.name)
            self.host = QLineEdit(self)
            layout.addRow('Host:', self.host)
            self.port = QSpinBox(self)
            self.port.setRange(1, 65535)
            self.port.setValue(22)
            layout.addRow('Port:', self.port)
            self.username = QLineEdit(self)
            layout.addRow('Username:', self.username)
            self.ssh_key = QLineEdit(self)
            layout.addRow('SSH key path:', self.ssh_key)
            self.ssh_browse = QPushButton('Browse...', self)
            self.ssh_browse.clicked.connect(self.browse_key)
            layout.addRow(self.ssh_browse)
            self.usersettings_path = QLineEdit(self)
            layout.addRow('User settings INI path:', self.usersettings_path)
            self.usersettings_browse = QPushButton('Browse...', self)
            self.usersettings_browse.clicked.connect(self.browse_usersettings)
            layout.addRow(self.usersettings_browse)
            # Preset selector
            try:
                from src.alsm.ini_templates import load_presets, preset_to_ini_text, save_preset
            except Exception:
                def load_presets():
                    return {}
                def preset_to_ini_text(n):
                    return ''
                def save_preset(n, p):
                    return False
            self.preset_combo = QComboBox(self)
            self._refresh_presets = lambda: self._load_preset_items(load_presets)
            self._refresh_presets()
            self.apply_preset_btn = QPushButton('Aplicar preset', self)
            self.apply_preset_btn.clicked.connect(lambda: self.apply_preset(preset_to_ini_text(self.preset_combo.currentText())))
            self.save_preset_btn = QPushButton('Guardar preset', self)
            self.save_preset_btn.clicked.connect(lambda: self.save_current_preset(save_preset))
            layout.addRow(self.preset_combo, self.apply_preset_btn)
            layout.addRow(self.save_preset_btn)
            self.usersettings_content = QTextEdit(self)
            self.usersettings_content.setPlaceholderText('Optional contents of userserverettings.ini\n(you can leave blank and provide path only)')
            layout.addRow('INI content:', self.usersettings_content)
            self.parse_btn = QPushButton('Parse INI', self)
            self.parse_btn.clicked.connect(self.parse_ini)
            self.serialize_btn = QPushButton('Serialize fields -> INI', self)
            self.serialize_btn.clicked.connect(self.serialize_from_fields)
            layout.addRow(self.parse_btn, self.serialize_btn)
            self.ini_area = QScrollArea(self)
            self.ini_container = QWidget(self)
            self.ini_layout = QVBoxLayout(self.ini_container)
            self.ini_area.setWidgetResizable(True)
            self.ini_area.setWidget(self.ini_container)
            layout.addRow(self.ini_area)
            self.write_ini_on_save = QCheckBox('Write INI file to path on save', self)
            layout.addRow(self.write_ini_on_save)
            self.ark_path = QLineEdit(self)
            layout.addRow('ARK path:', self.ark_path)
            self.map = QLineEdit(self)
            layout.addRow('Map:', self.map)
            self.systemd_unit = QLineEdit(self)
            layout.addRow('systemd unit:', self.systemd_unit)
            self.ark_start_params = QLineEdit(self)
            layout.addRow('Start params:', self.ark_start_params)
            self.autostart = QCheckBox(self)
            layout.addRow('Autostart:', self.autostart)
            # Extra accordion sections for ASM-like settings
            self.extra_settings = {}
            # Player settings
            pl_sec = CollapsibleSection('Ajustes de jugador')
            self.maxplayers2 = QSpinBox(self)
            self.maxplayers2.setRange(1, 500)
            self.maxplayers2.setValue(70)
            pl_sec.addWidget(QLabel('MaxPlayers:'))
            pl_sec.addWidget(self.maxplayers2)
            self.player_damage = QDoubleSpinBox(self)
            self.player_damage.setRange(0.1, 10.0)
            self.player_damage.setSingleStep(0.1)
            self.player_damage.setValue(1.0)
            pl_sec.addWidget(QLabel('PlayerDamageMultiplier:'))
            pl_sec.addWidget(self.player_damage)
            layout.addRow(pl_sec)
            self.extra_settings[('ServerSettings', 'MaxPlayers')] = self.maxplayers2
            self.extra_settings[('ServerSettings', 'PlayerDamageMultiplier')] = self.player_damage
            # Dino settings
            dino_sec = CollapsibleSection('Ajustes de dinos')
            self.dino_multiplier2 = QDoubleSpinBox(self)
            self.dino_multiplier2.setRange(0.1, 10.0)
            self.dino_multiplier2.setSingleStep(0.1)
            self.dino_multiplier2.setValue(1.0)
            dino_sec.addWidget(QLabel('DinoCountMultiplier:'))
            dino_sec.addWidget(self.dino_multiplier2)
            layout.addRow(dino_sec)
            self.extra_settings[('ServerSettings', 'DinoCountMultiplier')] = self.dino_multiplier2
            # Resources
            res_sec = CollapsibleSection('Recursos')
            self.resource_multiplier2 = QDoubleSpinBox(self)
            self.resource_multiplier2.setRange(0.1, 10.0)
            self.resource_multiplier2.setSingleStep(0.1)
            self.resource_multiplier2.setValue(1.0)
            res_sec.addWidget(QLabel('HarvestAmountMultiplier:'))
            res_sec.addWidget(self.resource_multiplier2)
            layout.addRow(res_sec)
            self.extra_settings[('ServerSettings', 'HarvestAmountMultiplier')] = self.resource_multiplier2
            # Structures
            struct_sec = CollapsibleSection('Estructuras')
            self.structure_multiplier = QDoubleSpinBox(self)
            self.structure_multiplier.setRange(0.1, 10.0)
            self.structure_multiplier.setSingleStep(0.1)
            self.structure_multiplier.setValue(1.0)
            struct_sec.addWidget(QLabel('StructureDamageMultiplier:'))
            struct_sec.addWidget(self.structure_multiplier)
            layout.addRow(struct_sec)
            self.extra_settings[('ServerSettings', 'StructureDamageMultiplier')] = self.structure_multiplier
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
            buttons.accepted.connect(self.on_accept)
            buttons.rejected.connect(self.reject)
            layout.addRow(buttons)
            if server:
                self.name.setText(getattr(server, 'name', ''))
                self.host.setText(getattr(server, 'host', ''))
                self.port.setValue(getattr(server, 'port', 22))
                if getattr(server, 'username', None):
                    self.username.setText(server.username)
                if getattr(server, 'ssh_key_path', None):
                    self.ssh_key.setText(server.ssh_key_path)
                if getattr(server, 'ark_path', None):
                    self.ark_path.setText(server.ark_path)
                if getattr(server, 'map', None):
                    self.map.setText(server.map)
                if getattr(server, 'systemd_unit', None):
                    self.systemd_unit.setText(server.systemd_unit)
                if getattr(server, 'ark_start_params', None):
                    self.ark_start_params.setText(server.ark_start_params)
                self.autostart.setChecked(bool(getattr(server, 'autostart', False)))
                if getattr(server, 'usersettings_path', None):
                    self.usersettings_path.setText(server.usersettings_path)
                if getattr(server, 'usersettings_content', None):
                    self.usersettings_content.setPlainText(server.usersettings_content)

        def browse_key(self):
            fn, _ = QFileDialog.getOpenFileName(self, 'Select SSH private key')
            if fn:
                self.ssh_key.setText(fn)

        def browse_usersettings(self):
            fn, _ = QFileDialog.getOpenFileName(self, 'Select userserverettings.ini')
            if fn:
                self.usersettings_path.setText(fn)
                try:
                    with open(fn, 'r', encoding='utf-8') as f:
                        self.usersettings_content.setPlainText(f.read())
                except Exception:
                    pass

        def apply_preset(self, text: str):
            if not text:
                QMessageBox.information(self, 'Preset', 'Preset vacío o no disponible')
                return
            self.usersettings_content.setPlainText(text)
            try:
                self.parse_ini()
            except Exception:
                pass

        def _load_preset_items(self, load_fn):
            try:
                presets = load_fn() or {}
                self.preset_combo.clear()
                keys = list(presets.keys())
                self.preset_combo.addItems(keys)
            except Exception:
                pass

        def save_current_preset(self, save_fn):
            # serialize current fields to a dict structure compatible with presets
            try:
                # ensure INI content is up-to-date
                try:
                    self.serialize_from_fields()
                except Exception:
                    pass
                text = self.usersettings_content.toPlainText()
                if not text.strip():
                    QMessageBox.information(self, 'Guardar preset', 'No hay INI para guardar')
                    return
                # parse into config and convert into dict
                cfg = configparser.ConfigParser()
                cfg.read_string(text)
                preset = {}
                for section in cfg.sections() or ['DEFAULT']:
                    preset[section] = dict(cfg[section])
                # ask for name
                from PyQt6.QtWidgets import QInputDialog
                name, ok = QInputDialog.getText(self, 'Guardar preset', 'Nombre del preset:')
                if not ok or not name.strip():
                    return
                ok2 = save_fn(name.strip(), preset)
                if ok2:
                    QMessageBox.information(self, 'Guardar preset', 'Preset guardado')
                    try:
                        # refresh combo
                        from src.alsm.ini_templates import load_presets
                        self._load_preset_items(load_presets)
                    except Exception:
                        pass
                else:
                    QMessageBox.critical(self, 'Guardar preset', 'Fallo al guardar preset')
            except Exception as e:
                QMessageBox.critical(self, 'Guardar preset', str(e))

        def on_accept(self):
            name = self.name.text().strip()
            host = self.host.text().strip()
            if not name:
                QMessageBox.critical(self, 'Validation', 'Name is required')
                return
            if not host:
                QMessageBox.critical(self, 'Validation', 'Host is required')
                return
            ssh_key = self.ssh_key.text().strip()
            if ssh_key and not os.path.exists(ssh_key):
                res = QMessageBox.question(self, 'SSH key not found', 'The SSH key path does not exist. Continue anyway?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if res != QMessageBox.StandardButton.Yes:
                    return
            try:
                self.serialize_from_fields()
            except Exception:
                pass
            self.accept()

        def parse_ini(self):
            text = self.usersettings_content.toPlainText()
            if not text.strip():
                QMessageBox.information(self, 'Parse INI', 'No INI content to parse')
                return
            cfg = configparser.ConfigParser()
            try:
                cfg.read_string(text)
            except configparser.MissingSectionHeaderError:
                try:
                    cfg.read_string('[DEFAULT]\n' + text)
                except Exception as e:
                    QMessageBox.critical(self, 'Parse Error', str(e))
                    return
            for i in reversed(range(self.ini_layout.count())):
                w = self.ini_layout.itemAt(i).widget()
                if w:
                    w.setParent(None)
            self.ini_widgets = {}
            for section in cfg.sections() or ['DEFAULT']:
                label = QLabel(f'[{section}]', self)
                self.ini_layout.addWidget(label)
                items = cfg[section].items()
                for opt, val in items:
                    # if widget exists in extra_settings, populate it
                    if getattr(self, 'extra_settings', None) and (section, opt) in self.extra_settings:
                        w = self.extra_settings[(section, opt)]
                        try:
                            if isinstance(w, QSpinBox):
                                w.setValue(int(val))
                            elif isinstance(w, QDoubleSpinBox):
                                w.setValue(float(val))
                            elif isinstance(w, QCheckBox):
                                w.setChecked(val.lower() in ('true', 'yes', 'on'))
                            elif isinstance(w, QLineEdit):
                                w.setText(val)
                        except Exception:
                            pass
                        continue
                    v = val
                    if v.lower() in ('true', 'false', 'yes', 'no', 'on', 'off'):
                        chk = QCheckBox(opt, self)
                        chk.setChecked(v.lower() in ('true', 'yes', 'on'))
                        self.ini_layout.addWidget(chk)
                        self.ini_widgets[(section, opt)] = chk
                        continue
                    try:
                        ival = int(v)
                        hl = QHBoxLayout()
                        lbl = QLabel(opt, self)
                        slider = QSlider()
                        slider.setOrientation(1)
                        minv = max(0, ival - 1000)
                        maxv = ival + 1000
                        slider.setRange(minv, maxv)
                        slider.setValue(ival)
                        spin = QSpinBox(self)
                        spin.setRange(minv, maxv)
                        spin.setValue(ival)
                        slider.valueChanged.connect(spin.setValue)
                        spin.valueChanged.connect(slider.setValue)
                        hl.addWidget(lbl)
                        hl.addWidget(slider)
                        hl.addWidget(spin)
                        container = QWidget(self)
                        container.setLayout(hl)
                        self.ini_layout.addWidget(container)
                        self.ini_widgets[(section, opt)] = spin
                        continue
                    except Exception:
                        pass
                    le = QLineEdit(self)
                    le.setText(v)
                    self.ini_layout.addWidget(QLabel(opt, self))
                    self.ini_layout.addWidget(le)
                    self.ini_widgets[(section, opt)] = le

        def serialize_from_fields(self):
            cfg = configparser.ConfigParser()
            for (section, opt), widget in getattr(self, 'ini_widgets', {}).items():
                if isinstance(widget, QCheckBox):
                    val = str(widget.isChecked())
                elif isinstance(widget, QSpinBox):
                    val = str(widget.value())
                elif isinstance(widget, QLineEdit):
                    val = widget.text()
                else:
                    try:
                        val = widget.toPlainText()
                    except Exception:
                        val = str(widget)
                if section not in cfg:
                    cfg[section] = {}
                cfg[section][opt] = val
            # include extra_settings values
            for (section, opt), widget in getattr(self, 'extra_settings', {}).items():
                try:
                    if isinstance(widget, QCheckBox):
                        val = str(widget.isChecked())
                    elif isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                        val = str(widget.value())
                    elif isinstance(widget, QLineEdit):
                        val = widget.text()
                    else:
                        val = str(widget)
                except Exception:
                    val = ''
                if section not in cfg:
                    cfg[section] = {}
                cfg[section][opt] = val
            from io import StringIO
            s = StringIO()
            cfg.write(s)
            self.usersettings_content.setPlainText(s.getvalue())

        def get_data(self):
            return {
                'name': self.name.text().strip(),
                'host': self.host.text().strip(),
                'port': int(self.port.value()),
                'username': self.username.text().strip(),
                'ssh_key_path': self.ssh_key.text().strip() or None,
                'ark_path': self.ark_path.text().strip() or None,
                'map': self.map.text().strip() or None,
                'systemd_unit': self.systemd_unit.text().strip() or None,
                'ark_start_params': self.ark_start_params.text().strip() or None,
                'autostart': bool(self.autostart.isChecked()),
                'usersettings_path': self.usersettings_path.text().strip() or None,
                'usersettings_content': self.usersettings_content.toPlainText().strip() or None,
                'write_ini_on_save': bool(self.write_ini_on_save.isChecked()),
            }


    class CreateFromScratchDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle('Create Server From Scratch')
            layout = QFormLayout(self)
            self.target_dir = QLineEdit(self)
            browse = QPushButton('Browse...', self)
            hb = QHBoxLayout()
            hb.addWidget(self.target_dir)
            hb.addWidget(browse)
            layout.addRow('Target folder:', hb)
            browse.clicked.connect(self.browse_folder)

            self.name = QLineEdit(self)
            layout.addRow('Server name:', self.name)
            self.map = QComboBox(self)
            self.map.addItems(['TheIsland_P', 'Ragnarok', 'ScorchedEarth_P', 'Extinction', 'TheCenter', 'Valguero_P'])
            layout.addRow('Map:', self.map)
            self.maxplayers = QSpinBox(self)
            self.maxplayers.setRange(1, 500)
            self.maxplayers.setValue(70)
            layout.addRow('Max players:', self.maxplayers)
            self.difficulty = QDoubleSpinBox(self)
            self.difficulty.setRange(0.1, 10.0)
            self.difficulty.setSingleStep(0.1)
            self.difficulty.setValue(1.0)
            layout.addRow('Difficulty:', self.difficulty)
            self.dinos_multiplier = QDoubleSpinBox(self)
            self.dinos_multiplier.setRange(0.1, 10.0)
            self.dinos_multiplier.setSingleStep(0.1)
            self.dinos_multiplier.setValue(1.0)
            layout.addRow('Dinos multiplier:', self.dinos_multiplier)
            self.resources_multiplier = QDoubleSpinBox(self)
            self.resources_multiplier.setRange(0.1, 10.0)
            self.resources_multiplier.setSingleStep(0.1)
            self.resources_multiplier.setValue(1.0)
            layout.addRow('Resources multiplier:', self.resources_multiplier)

            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
            buttons.accepted.connect(self.on_accept)
            buttons.rejected.connect(self.reject)
            layout.addRow(buttons)

        def browse_folder(self):
            d = QFileDialog.getExistingDirectory(self, 'Select target folder')
            if d:
                self.target_dir.setText(d)

        def on_accept(self):
            if not self.target_dir.text().strip():
                QMessageBox.critical(self, 'Validation', 'Target folder is required')
                return
            if not self.name.text().strip():
                QMessageBox.critical(self, 'Validation', 'Server name is required')
                return
            self.accept()

        def get_data(self):
            return {
                'target_dir': self.target_dir.text().strip(),
                'name': self.name.text().strip(),
                'map': self.map.currentText(),
                'maxplayers': int(self.maxplayers.value()),
                'difficulty': float(self.difficulty.value()),
                'dinos_multiplier': float(self.dinos_multiplier.value()),
                'resources_multiplier': float(self.resources_multiplier.value()),
            }


    class RconDialog(QDialog):
        def __init__(self, parent=None, server=None):
            super().__init__(parent)
            self.setWindowTitle('RCON')
            self.server = server
            layout = QVBoxLayout(self)
            self.cmd = QLineEdit(self)
            self.cmd.setPlaceholderText('Comando RCON (ej: listPlayers)')
            layout.addWidget(self.cmd)
            self.send_btn = QPushButton('Enviar', self)
            self.send_btn.clicked.connect(self.on_send)
            layout.addWidget(self.send_btn)
            self.output = QTextEdit(self)
            self.output.setReadOnly(False)
            layout.addWidget(self.output)

        def on_send(self):
            txt = self.cmd.text().strip()
            if not txt:
                return
            if not self.server:
                QMessageBox.information(self, 'RCON', 'No server')
                return
            host = getattr(self.server, 'host', None)
            port = getattr(self.server, 'port', 27020)
            pwd = getattr(self.server, 'rcon_password', None) or getattr(self.server, 'rcon', None)
            if not pwd:
                # ask for password
                from PyQt6.QtWidgets import QInputDialog
                pw, ok = QInputDialog.getText(self, 'RCON password', 'Password RCON:', QLineEdit.EchoMode.Password)
                if not ok or not pw:
                    return
                pwd = pw

            self.output.append(f'-- Enviando: {txt}')
            from src.alsm import runner

            def _cb(res):
                code, out, err = res
                def _append():
                    if out:
                        self.output.append('--- RESPUESTA ---')
                        self.output.append(out)
                    if err:
                        self.output.append('--- ERROR ---')
                        self.output.append(err)
                QTimer.singleShot(0, _append)

            runner.run_rcon_in_thread(host, int(port), pwd, txt, callback=_cb)


    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle('ALSM')
            central = QWidget(self)
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)
            self.label = QLabel('ALSM - ARK Linux Server Manager', self)
            layout.addWidget(self.label)
            hl = QHBoxLayout()
            self.servers_list = QListWidget(self)
            self.servers_list.itemSelectionChanged.connect(self.on_selection_changed)
            hl.addWidget(self.servers_list)
            btns_v = QVBoxLayout()
            self.refresh_btn = QPushButton('Refresh', self)
            self.refresh_btn.clicked.connect(self.load_server_list)
            btns_v.addWidget(self.refresh_btn)
            self.add_btn = QPushButton('Add', self)
            self.add_btn.clicked.connect(self.on_add)
            btns_v.addWidget(self.add_btn)
            self.template_btn = QPushButton('New (Template)', self)
            self.template_btn.clicked.connect(self.on_new_from_template)
            btns_v.addWidget(self.template_btn)
            self.create_btn = QPushButton('Create (From Scratch)', self)
            self.create_btn.clicked.connect(self.on_create_scratch)
            btns_v.addWidget(self.create_btn)
            self.create_remote_btn = QPushButton('Create Remote (SSH)', self)
            self.create_remote_btn.clicked.connect(self.on_create_remote)
            btns_v.addWidget(self.create_remote_btn)
            self.edit_btn = QPushButton('Edit', self)
            self.edit_btn.clicked.connect(self.on_edit)
            self.edit_btn.setEnabled(False)
            btns_v.addWidget(self.edit_btn)
            self.delete_btn = QPushButton('Delete', self)
            self.delete_btn.clicked.connect(self.on_delete)
            self.delete_btn.setEnabled(False)
            btns_v.addWidget(self.delete_btn)
            self.connect_btn = QPushButton('Connect via SSH', self)
            self.connect_btn.clicked.connect(self.on_connect)
            self.connect_btn.setEnabled(False)
            btns_v.addWidget(self.connect_btn)
            self.rcon_btn = QPushButton('RCON', self)
            self.rcon_btn.clicked.connect(self.on_rcon)
            self.rcon_btn.setEnabled(False)
            btns_v.addWidget(self.rcon_btn)
            self.start_btn = QPushButton('Start', self)
            self.start_btn.clicked.connect(self.on_start)
            self.start_btn.setEnabled(False)
            btns_v.addWidget(self.start_btn)
            self.stop_btn = QPushButton('Stop', self)
            self.stop_btn.clicked.connect(self.on_stop)
            self.stop_btn.setEnabled(False)
            btns_v.addWidget(self.stop_btn)
            self.backup_btn = QPushButton('Backup', self)
            self.backup_btn.clicked.connect(self.on_backup)
            self.backup_btn.setEnabled(False)
            btns_v.addWidget(self.backup_btn)
            self.open_folder_btn = QPushButton('Abrir carpeta', self)
            self.open_folder_btn.clicked.connect(self.on_open_folder)
            self.open_folder_btn.setEnabled(False)
            btns_v.addWidget(self.open_folder_btn)
            self.open_config_btn = QPushButton('Abrir config', self)
            self.open_config_btn.clicked.connect(self.on_open_config)
            self.open_config_btn.setEnabled(False)
            btns_v.addWidget(self.open_config_btn)
            btns_v.addStretch()
            hl.addLayout(btns_v)
            layout.addLayout(hl)
            self.status = QLabel('Ready', self)
            layout.addWidget(self.status)
            # Log viewer
            self.log = QTextEdit(self)
            self.log.setReadOnly(True)
            self.log.setPlaceholderText('Output log...')
            layout.addWidget(self.log)
            try:
                from src.alsm.servers import load_servers, save_servers, Server
            except Exception:
                try:
                    from servers import load_servers, save_servers, Server
                except Exception:
                    from .servers import load_servers, save_servers, Server
            self._servers = []
            self._load_func = load_servers
            self._save_func = save_servers
            self._Server = Server
            self.load_server_list()

        def on_connect(self):
            sel = None
            if hasattr(self, 'servers_list') and self.servers_list.selectedItems():
                idx = self.servers_list.currentRow()
                if 0 <= idx < len(self._servers):
                    sel = self._servers[idx]
            dlg = ConnectDialog(self)
            if sel:
                dlg.host.setText(sel.host)
                dlg.port.setValue(sel.port)
                if sel.username:
                    dlg.username.setText(sel.username)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                data = dlg.get_data()
            else:
                return

        def on_rcon(self):
            if not (hasattr(self, 'servers_list') and self.servers_list.selectedItems()):
                return
            idx = self.servers_list.currentRow()
            server = self._servers[idx]
            dlg = RconDialog(self, server=server)
            dlg.exec()

        def _run_action(self, action_name: str):
            if not (hasattr(self, 'servers_list') and self.servers_list.selectedItems()):
                self.status.setText('No server selected')
                return
            idx = self.servers_list.currentRow()
            server = self._servers[idx]
            from src.alsm import runner
            pwd = None
            # if remote and username exists, ask for password (simple prompt)
            if not runner.is_local(getattr(server, 'host', '')) and getattr(server, 'username', None):
                try:
                    from PyQt6.QtWidgets import QInputDialog
                    pw, ok = QInputDialog.getText(self, 'SSH Password', f'Password for {server.username}@{server.host}', QLineEdit.EchoMode.Password)
                    if ok and pw:
                        pwd = pw
                except Exception:
                    pwd = None

            def _cb(res):
                code, out, err = res
                # append to log with timestamp
                import datetime

                def _append():
                    ts = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    header = f"[{ts}] {action_name}: exit={code}\n"
                    self.log.append(header)
                    if out:
                        self.log.append('--- STDOUT ---')
                        self.log.append(out)
                    if err:
                        self.log.append('--- STDERR ---')
                        self.log.append(err)
                    self.status.setText(f"{action_name} finished (exit={code})")

                QTimer.singleShot(0, _append)

            self.status.setText(f'{action_name} running...')

            def _line_cb(kind, text):
                def _append_line():
                    ts = __import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    prefix = 'OUT' if kind == 'out' else 'ERR'
                    self.log.append(f'[{ts}] {prefix}: {text.rstrip()}')
                QTimer.singleShot(0, _append_line)

            def _done_cb(res):
                try:
                    code, out, err = res
                except Exception:
                    code, out, err = (1, '', str(res))

                def _finish():
                    self.status.setText(f"{action_name} finished (exit={code})")
                QTimer.singleShot(0, _finish)

            try:
                runner.run_action_stream(action_name, server, pwd, line_callback=_line_cb, done_callback=_cb)
            except Exception:
                # fallback to old behavior
                runner.run_in_thread(getattr(runner, f"{action_name.lower()}_server"), args=(server, pwd), callback=_cb)

        def on_start(self):
            self._run_action('Start')

        def on_stop(self):
            self._run_action('Stop')

        def on_backup(self):
            self._run_action('Backup')

        def load_server_list(self):
            try:
                self._servers = self._load_func()
            except Exception as e:
                self._servers = []
                self.status.setText(f'Failed to load servers: {e}')
            self.servers_list.clear()
            for s in self._servers:
                self.servers_list.addItem(f"{s.name} — {s.host}:{s.port}")

        def on_add(self):
            dlg = ServerEditorDialog(self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                data = dlg.get_data()
                try:
                    new = self._Server.from_dict(data)
                except Exception:
                    new = self._Server(**data)
                # Persist INI automatically: prefer provided path, else use ark_path default
                content = data.get('usersettings_content')
                path_str = data.get('usersettings_path')
                if not path_str and getattr(new, 'ark_path', None):
                    pdefault = Path(new.ark_path) / 'ShooterGame' / 'Saved' / 'Config' / 'LinuxServer' / 'GameUserSettings.ini'
                    path_str = str(pdefault)
                if content and path_str:
                    try:
                        p = Path(path_str)
                        p.parent.mkdir(parents=True, exist_ok=True)
                        p.write_text(content, encoding='utf-8')
                        new.usersettings_path = str(p)
                        new.usersettings_content = content
                    except Exception as e:
                        self.status.setText(f'INI write failed: {e}')
                        QMessageBox.warning(self, 'INI Save Failed', str(e))
                self._servers.append(new)
                try:
                    self._save_func(self._servers)
                except Exception as e:
                    self.status.setText(f'Save failed: {e}')
                self.load_server_list()

        def on_new_from_template(self):
            tpl = {
                'name': 'New ARK Pre-Aquatic Server',
                'host': '127.0.0.1',
                'port': 22,
                'username': 'ark',
                'autostart': False,
                'ark_path': '/home/ark/server',
                'systemd_unit': None,
                'map': 'TheIsland_P',
                'ark_start_params': '-server -log -noBattlEye',
                'usersettings_content': '[ServerSettings]\nServerAdminPassword=\nMaxPlayers=70\nQueryPort=27015\nPort=7777\n',
                'usersettings_path': None,
                'ssh_key_path': None,
            }
            tmp = self._Server.from_dict(tpl)
            dlg = ServerEditorDialog(self, server=tmp)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                data = dlg.get_data()
                try:
                    new = self._Server.from_dict(data)
                except Exception:
                    new = self._Server(**data)
                # Auto-write INI to default path under ark_path if not provided
                content = data.get('usersettings_content')
                path_str = data.get('usersettings_path')
                if not path_str and getattr(new, 'ark_path', None):
                    pdefault = Path(new.ark_path) / 'ShooterGame' / 'Saved' / 'Config' / 'LinuxServer' / 'GameUserSettings.ini'
                    path_str = str(pdefault)
                if content and path_str:
                    try:
                        p = Path(path_str)
                        p.parent.mkdir(parents=True, exist_ok=True)
                        p.write_text(content, encoding='utf-8')
                        new.usersettings_path = str(p)
                        new.usersettings_content = content
                    except Exception as e:
                        self.status.setText(f'INI write failed: {e}')
                        QMessageBox.warning(self, 'INI Save Failed', str(e))
                self._servers.append(new)
                try:
                    self._save_func(self._servers)
                except Exception as e:
                    self.status.setText(f'Save failed: {e}')
                self.load_server_list()

        def on_edit(self):
            if not (self.servers_list.selectedItems()):
                return
            idx = self.servers_list.currentRow()
            server = self._servers[idx]
            dlg = ServerEditorDialog(self, server=server)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                data = dlg.get_data()
                try:
                    updated = self._Server.from_dict(data)
                except Exception:
                    updated = self._Server(**data)
                self._servers[idx] = updated
                # Auto-write INI if content exists; prefer provided path, else deduce from ark_path
                content = data.get('usersettings_content')
                path_str = data.get('usersettings_path')
                if not path_str and getattr(updated, 'ark_path', None):
                    pdefault = Path(updated.ark_path) / 'ShooterGame' / 'Saved' / 'Config' / 'LinuxServer' / 'GameUserSettings.ini'
                    path_str = str(pdefault)
                if content and path_str:
                    try:
                        p = Path(path_str)
                        p.parent.mkdir(parents=True, exist_ok=True)
                        p.write_text(content, encoding='utf-8')
                        updated.usersettings_path = str(p)
                        updated.usersettings_content = content
                    except Exception as e:
                        self.status.setText(f'INI write failed: {e}')
                        QMessageBox.warning(self, 'INI Save Failed', str(e))
                try:
                    self._save_func(self._servers)
                except Exception as e:
                    self.status.setText(f'Save failed: {e}')
                self.load_server_list()

        def on_delete(self):
            if not (self.servers_list.selectedItems()):
                return
            idx = self.servers_list.currentRow()
            server = self._servers[idx]
            res = QMessageBox.question(self, 'Delete', f"Delete server '{server.name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if res == QMessageBox.StandardButton.Yes:
                del self._servers[idx]
                try:
                    self._save_func(self._servers)
                except Exception as e:
                    self.status.setText(f'Save failed: {e}')
                self.load_server_list()

        def on_selection_changed(self):
            has = bool(self.servers_list.selectedItems())
            self.connect_btn.setEnabled(has)
            self.edit_btn.setEnabled(has)
            self.delete_btn.setEnabled(has)
            self.start_btn.setEnabled(has)
            self.stop_btn.setEnabled(has)
            self.backup_btn.setEnabled(has)
            self.open_folder_btn.setEnabled(has)
            self.open_config_btn.setEnabled(has)
            self.rcon_btn.setEnabled(has)
        def on_create_scratch(self):
            dlg = CreateFromScratchDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            data = dlg.get_data()
            target = Path(data['target_dir'])
            server_dir = target / data['name']
            try:
                if server_dir.exists():
                    res = QMessageBox.question(self, 'Exists', f"Folder {server_dir} exists. Use it?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if res != QMessageBox.StandardButton.Yes:
                        return
                # create directory structure
                cfg_dir = server_dir / 'ShooterGame' / 'Saved' / 'Config' / 'LinuxServer'
                cfg_dir.mkdir(parents=True, exist_ok=True)
                # create GameUserSettings.ini
                gu_path = cfg_dir / 'GameUserSettings.ini'
                gu_content = f"[ServerSettings]\nSessionName={data['name']}\nMaxPlayers={data['maxplayers']}\nMapName={data['map']}\n"
                gu_path.write_text(gu_content, encoding='utf-8')
                # create Game.ini
                game_ini = cfg_dir / 'Game.ini'
                gi_content = (
                    '[ServerSettings]\n'
                    f"DifficultyOffsetMultiplier={data['difficulty']}\n"
                    f"DinoCountMultiplier={data['dinos_multiplier']}\n"
                    f"HarvestAmountMultiplier={data['resources_multiplier']}\n"
                )
                game_ini.write_text(gi_content, encoding='utf-8')
                # create simple start/stop scripts
                start_sh = server_dir / 'start.sh'
                start_sh.write_text(f"#!/bin/sh\ncd \"{server_dir}\"\n# Launch placeholder - edit as needed\n./ShooterGame/Binaries/Linux/ShooterGameServer {data['map']}?listen -server -log\n", encoding='utf-8')
                stop_sh = server_dir / 'stop.sh'
                stop_sh.write_text("#!/bin/sh\n# Add stop logic (systemctl stop or kill)\n", encoding='utf-8')
                try:
                    os.chmod(start_sh, 0o755)
                    os.chmod(stop_sh, 0o755)
                except Exception:
                    pass
            except Exception as e:
                QMessageBox.critical(self, 'Create failed', str(e))
                return
            # register server in servers list
            srv = {
                'name': data['name'],
                'host': '127.0.0.1',
                'port': 22,
                'username': 'ark',
                'autostart': False,
                'ark_path': str(server_dir),
                'systemd_unit': None,
                'map': data['map'],
                'ark_start_params': '',
                'usersettings_content': gu_content,
                'usersettings_path': str(gu_path),
                'ssh_key_path': None,
            }
            try:
                new = self._Server.from_dict(srv)
            except Exception:
                new = self._Server(**srv)
            self._servers.append(new)
            try:
                self._save_func(self._servers)
            except Exception as e:
                self.status.setText(f'Save failed: {e}')
            self.load_server_list()
            QMessageBox.information(self, 'Created', f'Server created at {server_dir}')

        def on_create_remote(self):
            # create local temp structure then upload via SFTP
            dlg = CreateFromScratchDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            data = dlg.get_data()
            import tempfile
            tmp = tempfile.TemporaryDirectory()
            local_base = Path(tmp.name) / data['name']
            try:
                # create same structure as on_create_scratch but in tmp
                cfg_dir = local_base / 'ShooterGame' / 'Saved' / 'Config' / 'LinuxServer'
                cfg_dir.mkdir(parents=True, exist_ok=True)
                gu_path = cfg_dir / 'GameUserSettings.ini'
                gu_content = f"[ServerSettings]\nSessionName={data['name']}\nMaxPlayers={data['maxplayers']}\nMapName={data['map']}\n"
                gu_path.write_text(gu_content, encoding='utf-8')
                game_ini = cfg_dir / 'Game.ini'
                gi_content = (
                    '[ServerSettings]\n'
                    f"DifficultyOffsetMultiplier={data['difficulty']}\n"
                    f"DinoCountMultiplier={data['dinos_multiplier']}\n"
                    f"HarvestAmountMultiplier={data['resources_multiplier']}\n"
                )
                game_ini.write_text(gi_content, encoding='utf-8')
                start_sh = local_base / 'start.sh'
                start_sh.write_text(f"#!/bin/sh\ncd \"{local_base}\"\n./ShooterGame/Binaries/Linux/ShooterGameServer {data['map']}?listen -server -log\n", encoding='utf-8')
                stop_sh = local_base / 'stop.sh'
                stop_sh.write_text("#!/bin/sh\n# stop script\n", encoding='utf-8')
                try:
                    os.chmod(start_sh, 0o755)
                    os.chmod(stop_sh, 0o755)
                except Exception:
                    pass
            except Exception as e:
                QMessageBox.critical(self, 'Create remote failed', str(e))
                tmp.cleanup()
                return

            # ask SSH details
            cdlg = ConnectDialog(self)
            if cdlg.exec() != QDialog.DialogCode.Accepted:
                tmp.cleanup()
                return
            sshd = cdlg.get_data()
            remotedir, ok = QInputDialog.getText(self, 'Remote path', 'Remote installation path (e.g. /home/ark/server):')
            if not ok or not remotedir.strip():
                QMessageBox.information(self, 'Create remote', 'Remote path required')
                tmp.cleanup()
                return

            # attempt upload
            from src.alsm import runner
            self.status.setText('Uploading to remote...')

            def _done(res):
                ok2, msg = res
                def _ui():
                    if ok2:
                        # register server
                        srv = {
                            'name': data['name'],
                            'host': sshd.get('host'),
                            'port': int(sshd.get('port') or 22),
                            'username': sshd.get('username'),
                            'autostart': False,
                            'ark_path': remotedir,
                            'systemd_unit': None,
                            'map': data['map'],
                            'ark_start_params': '',
                            'usersettings_content': gu_content,
                            'usersettings_path': str(Path(remotedir) / 'ShooterGame' / 'Saved' / 'Config' / 'LinuxServer' / 'GameUserSettings.ini'),
                            'ssh_key_path': None,
                        }
                        try:
                            new = self._Server.from_dict(srv)
                        except Exception:
                            new = self._Server(**srv)
                        self._servers.append(new)
                        try:
                            self._save_func(self._servers)
                        except Exception as e:
                            self.status.setText(f'Save failed: {e}')
                        self.load_server_list()
                        QMessageBox.information(self, 'Upload', 'Upload and registration complete')
                    else:
                        QMessageBox.critical(self, 'Upload failed', msg)
                    tmp.cleanup()
                    self.status.setText('Ready')
                QTimer.singleShot(0, _ui)

            def _line(kind, text):
                def _append():
                    ts = __import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    self.log.append(f'[{ts}] {kind}: {text.rstrip()}')
                QTimer.singleShot(0, _append)

            # run upload in thread
            def _upload_worker():
                try:
                    ok2, msg = runner.upload_dir_sftp(sshd.get('host'), int(sshd.get('port') or 22), sshd.get('username'), sshd.get('password'), str(local_base), remotedir)
                    return ok2, msg
                except Exception as e:
                    return False, str(e)

            runner.run_in_thread(lambda: _upload_worker(), args=(), callback=_done)

        def on_open_folder(self):
            if not (hasattr(self, 'servers_list') and self.servers_list.selectedItems()):
                return
            idx = self.servers_list.currentRow()
            server = self._servers[idx]
            path = getattr(server, 'ark_path', None)
            if not path:
                QMessageBox.information(self, 'Abrir carpeta', 'No hay `ark_path` configurado para este servidor')
                return
            p = Path(path)
            if not p.exists():
                QMessageBox.information(self, 'Abrir carpeta', f'Carpeta no encontrada: {p}')
                return
            try:
                if os.name == 'nt':
                    os.startfile(str(p))
                elif sys.platform == 'darwin':
                    import subprocess
                    subprocess.run(['open', str(p)])
                else:
                    import subprocess
                    subprocess.run(['xdg-open', str(p)])
            except Exception as e:
                QMessageBox.critical(self, 'Abrir carpeta', str(e))

        def on_open_config(self):
            if not (hasattr(self, 'servers_list') and self.servers_list.selectedItems()):
                return
            idx = self.servers_list.currentRow()
            server = self._servers[idx]
            cfg_path = getattr(server, 'usersettings_path', None)
            if not cfg_path and getattr(server, 'ark_path', None):
                cfg_path = str(Path(server.ark_path) / 'ShooterGame' / 'Saved' / 'Config' / 'LinuxServer' / 'GameUserSettings.ini')
            if not cfg_path:
                QMessageBox.information(self, 'Abrir config', 'No hay ruta de configuración disponible para este servidor')
                return
            p = Path(cfg_path)
            if not p.exists():
                QMessageBox.information(self, 'Abrir config', f'Archivo INI no encontrado: {p}')
                return
            try:
                if os.name == 'nt':
                    os.startfile(str(p))
                elif sys.platform == 'darwin':
                    import subprocess
                    subprocess.run(['open', str(p)])
                else:
                    import subprocess
                    subprocess.run(['xdg-open', str(p)])
            except Exception as e:
                QMessageBox.critical(self, 'Abrir config', str(e))


    def gui_main():
        app = QApplication(sys.argv)
        w = MainWindow()
        w.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    if HAVE_QT:
        gui_main()
    else:
        console_main()