import sys
import os
import configparser
from pathlib import Path


# Try to import PyQt6; if unavailable, try PySide6; otherwise fall back to console
HAVE_QT = True
QT_BINDING = None
try:
	from PyQt6.QtWidgets import (
		QApplication,
		QMainWindow,
		QWidget,
		QVBoxLayout,
		QLabel,
		QPushButton,
		QDialog,
		QFormLayout,
		QLineEdit,
		QSpinBox,
		QDialogButtonBox,
		QMessageBox,
			QCheckBox,
			QFileDialog,
			QTextEdit,
		QListWidget,
		QHBoxLayout,
	)
	QT_BINDING = "PyQt6"
except Exception:
	try:
		from PySide6.QtWidgets import (
			QApplication,
			QMainWindow,
			QWidget,
			QVBoxLayout,
			QLabel,
			QPushButton,
			QDialog,
			QFormLayout,
			QLineEdit,
			QSpinBox,
			QDialogButtonBox,
			QMessageBox,
			QListWidget,
			QHBoxLayout,
			QCheckBox,
			QFileDialog,
			QInputDialog,
			QTextEdit,
		)
		QT_BINDING = "PySide6"
	except Exception:
		HAVE_QT = False


if HAVE_QT:
	class ConnectDialog(QDialog):
		def __init__(self, parent=None):
			super().__init__(parent)
			self.setWindowTitle("SSH Connect")
			layout = QFormLayout(self)

			self.host = QLineEdit(self)
			self.host.setPlaceholderText("hostname or IP")
			layout.addRow("Host:", self.host)

			self.port = QSpinBox(self)
			self.port.setRange(1, 65535)
			self.port.setValue(22)
			layout.addRow("Port:", self.port)

			self.username = QLineEdit(self)
			layout.addRow("Username:", self.username)

			self.password = QLineEdit(self)
			self.password.setEchoMode(QLineEdit.EchoMode.Password)
			layout.addRow("Password:", self.password)

			buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
			buttons.accepted.connect(self.accept)
			buttons.rejected.connect(self.reject)
			layout.addRow(buttons)

		def get_data(self):
			return {
				"host": self.host.text().strip(),
				"port": int(self.port.value()),
				"username": self.username.text().strip(),
				"password": self.password.text(),
			}


		class ServerEditorDialog(QDialog):
			def __init__(self, parent=None, server=None):
				super().__init__(parent)
				self.setWindowTitle("Server Editor")
				layout = QFormLayout(self)

				self.name = QLineEdit(self)
				layout.addRow("Name:", self.name)

				self.host = QLineEdit(self)
				layout.addRow("Host:", self.host)

				self.port = QSpinBox(self)
				self.port.setRange(1, 65535)
				self.port.setValue(22)
				layout.addRow("Port:", self.port)

				self.username = QLineEdit(self)
				layout.addRow("Username:", self.username)

				self.ssh_key = QLineEdit(self)
				layout.addRow("SSH key path:", self.ssh_key)
				self.ssh_browse = QPushButton("Browse...", self)
				self.ssh_browse.clicked.connect(self.browse_key)
				layout.addRow(self.ssh_browse)

				self.usersettings_path = QLineEdit(self)
				layout.addRow("User settings INI path:", self.usersettings_path)
				self.usersettings_browse = QPushButton("Browse...", self)
				self.usersettings_browse.clicked.connect(self.browse_usersettings)
				layout.addRow(self.usersettings_browse)

				self.usersettings_content = QTextEdit(self)
				self.usersettings_content.setPlaceholderText("Optional contents of userserverettings.ini\n(you can leave blank and provide path only)")
				layout.addRow("INI content:", self.usersettings_content)

				# Parse / serialize controls for INI content
				self.parse_btn = QPushButton("Parse INI", self)
				self.parse_btn.clicked.connect(self.parse_ini)
				self.serialize_btn = QPushButton("Serialize fields -> INI", self)
				self.serialize_btn.clicked.connect(self.serialize_from_fields)
				layout.addRow(self.parse_btn, self.serialize_btn)

				# dynamic area for parsed INI fields
				self.ini_area = QScrollArea(self)
				self.ini_container = QWidget(self)
				self.ini_layout = QVBoxLayout(self.ini_container)
				self.ini_area.setWidgetResizable(True)
				self.ini_area.setWidget(self.ini_container)
				layout.addRow(self.ini_area)

				self.write_ini_on_save = QCheckBox("Write INI file to path on save", self)
				layout.addRow(self.write_ini_on_save)

				self.ark_path = QLineEdit(self)
				layout.addRow("ARK path:", self.ark_path)

				self.map = QLineEdit(self)
				layout.addRow("Map:", self.map)

				self.systemd_unit = QLineEdit(self)
				layout.addRow("systemd unit:", self.systemd_unit)

				self.ark_start_params = QLineEdit(self)
				layout.addRow("Start params:", self.ark_start_params)

				self.autostart = QCheckBox(self)
				layout.addRow("Autostart:", self.autostart)

				buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
				buttons.accepted.connect(self.accept)
				buttons.rejected.connect(self.reject)
				layout.addRow(buttons)

				buttons.accepted.connect(self.accept)

				if server:
					# prefill
					self.name.setText(getattr(server, "name", ""))
					self.host.setText(getattr(server, "host", ""))
					self.port.setValue(getattr(server, "port", 22))
					if getattr(server, "username", None):
						self.username.setText(server.username)
					if getattr(server, "ssh_key_path", None):
						self.ssh_key.setText(server.ssh_key_path)
					if getattr(server, "ark_path", None):
						self.ark_path.setText(server.ark_path)
					if getattr(server, "map", None):
						self.map.setText(server.map)
					if getattr(server, "systemd_unit", None):
						self.systemd_unit.setText(server.systemd_unit)
					if getattr(server, "ark_start_params", None):
						self.ark_start_params.setText(server.ark_start_params)
					self.autostart.setChecked(bool(getattr(server, "autostart", False)))
					if getattr(server, "usersettings_path", None):
						self.usersettings_path.setText(server.usersettings_path)
					if getattr(server, "usersettings_content", None):
						self.usersettings_content.setPlainText(server.usersettings_content)

			def browse_key(self):
				fn, _ = QFileDialog.getOpenFileName(self, "Select SSH private key")
				if fn:
					self.ssh_key.setText(fn)

			def browse_usersettings(self):
				fn, _ = QFileDialog.getOpenFileName(self, "Select userserverettings.ini")
				if fn:
					self.usersettings_path.setText(fn)
					try:
						with open(fn, "r", encoding="utf-8") as f:
							self.usersettings_content.setPlainText(f.read())
					except Exception:
						# ignore read errors, keep path
						pass

			def on_accept(self):
				# Validate required fields before closing
				name = self.name.text().strip()
				host = self.host.text().strip()
				if not name:
					QMessageBox.critical(self, "Validation", "Name is required")
					return
				if not host:
					QMessageBox.critical(self, "Validation", "Host is required")
					return
				ssh_key = self.ssh_key.text().strip()
				if ssh_key and not os.path.exists(ssh_key):
					res = QMessageBox.question(self, "SSH key not found", "The SSH key path does not exist. Continue anyway?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
					if res != QMessageBox.StandardButton.Yes:
						return
				# all good
				# ensure fields are serialized back to the INI content before accepting
				try:
					self.serialize_from_fields()
				except Exception:
					pass
				self.accept()

			def parse_ini(self):
				text = self.usersettings_content.toPlainText()
				if not text.strip():
					QMessageBox.information(self, "Parse INI", "No INI content to parse")
					return
				cfg = configparser.ConfigParser()
				try:
					cfg.read_string(text)
				except configparser.MissingSectionHeaderError:
					# try wrapping in a default section
					try:
						cfg.read_string("[DEFAULT]\n" + text)
					except Exception as e:
						QMessageBox.critical(self, "Parse Error", str(e))
						return
				# clear previous widgets
				for i in reversed(range(self.ini_layout.count())):
					w = self.ini_layout.itemAt(i).widget()
					if w:
						w.setParent(None)
				self.ini_widgets = {}
				# create widgets per section/option
				for section in cfg.sections() or ["DEFAULT"]:
					label = QLabel(f"[{section}]", self)
					self.ini_layout.addWidget(label)
					items = cfg[section].items()
					for opt, val in items:
						# attempt to detect type
						v = val
						if v.lower() in ("true", "false", "yes", "no", "on", "off"):
							chk = QCheckBox(opt, self)
							chk.setChecked(v.lower() in ("true", "yes", "on"))
							self.ini_layout.addWidget(chk)
							self.ini_widgets[(section, opt)] = chk
							continue
						# numeric int
						try:
							ival = int(v)
							hl = QHBoxLayout()
							lbl = QLabel(opt, self)
							slider = QSlider()
							slider.setOrientation(1)  # Qt.Horizontal
							# heuristic range
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
						# fallback to text
						le = QLineEdit(self)
						le.setText(v)
						self.ini_layout.addWidget(QLabel(opt, self))
						self.ini_layout.addWidget(le)
						self.ini_widgets[(section, opt)] = le
				# done
				QMessageBox.information(self, "Parse INI", "Parsed INI into editable fields")

			def serialize_from_fields(self):
				# build config from widgets
				cfg = configparser.ConfigParser()
				for (section, opt), widget in getattr(self, 'ini_widgets', {}).items():
					if isinstance(widget, QCheckBox):
						val = str(widget.isChecked())
					elif isinstance(widget, QSpinBox):
						val = str(widget.value())
					elif isinstance(widget, QLineEdit):
						val = widget.text()
					else:
						# QTextEdit or others
						try:
							val = widget.toPlainText()
						except Exception:
							val = str(widget)
					if section not in cfg:
						cfg[section] = {}
					cfg[section][opt] = val
				# write to string
				from io import StringIO
				s = StringIO()
				cfg.write(s)
				self.usersettings_content.setPlainText(s.getvalue())

			def get_data(self):
				return {
					"name": self.name.text().strip(),
					"host": self.host.text().strip(),
					"port": int(self.port.value()),
					"username": self.username.text().strip(),
					"ssh_key_path": self.ssh_key.text().strip() or None,
					"ark_path": self.ark_path.text().strip() or None,
					"map": self.map.text().strip() or None,
					"systemd_unit": self.systemd_unit.text().strip() or None,
					"ark_start_params": self.ark_start_params.text().strip() or None,
					"autostart": bool(self.autostart.isChecked()),
					"usersettings_path": self.usersettings_path.text().strip() or None,
					"usersettings_content": self.usersettings_content.toPlainText().strip() or None,
					"write_ini_on_save": bool(self.write_ini_on_save.isChecked()),
				}


	class MainWindow(QMainWindow):
		def __init__(self):
			super().__init__()
			self.setWindowTitle("ALSM")

			# central widget and layout
			central = QWidget(self)
			self.setCentralWidget(central)
			layout = QVBoxLayout(central)

			self.label = QLabel("ALSM - ARK Linux Server Manager", self)
			layout.addWidget(self.label)

			# Servers list + buttons
			hl = QHBoxLayout()
			self.servers_list = QListWidget(self)
			self.servers_list.itemSelectionChanged.connect(self.on_selection_changed)
			hl.addWidget(self.servers_list)

			btns_v = QVBoxLayout()
			self.refresh_btn = QPushButton("Refresh", self)
			self.refresh_btn.clicked.connect(self.load_server_list)
			btns_v.addWidget(self.refresh_btn)

			self.add_btn = QPushButton("Add", self)
			self.add_btn.clicked.connect(self.on_add)
			btns_v.addWidget(self.add_btn)

			self.template_btn = QPushButton("New (Template)", self)
			self.template_btn.clicked.connect(self.on_new_from_template)
			btns_v.addWidget(self.template_btn)

			self.edit_btn = QPushButton("Edit", self)
			self.edit_btn.clicked.connect(self.on_edit)
			self.edit_btn.setEnabled(False)
			btns_v.addWidget(self.edit_btn)

			self.delete_btn = QPushButton("Delete", self)
			self.delete_btn.clicked.connect(self.on_delete)
			self.delete_btn.setEnabled(False)
			btns_v.addWidget(self.delete_btn)

			self.connect_btn = QPushButton("Connect via SSH", self)
			self.connect_btn.clicked.connect(self.on_connect)
			self.connect_btn.setEnabled(False)
			btns_v.addWidget(self.connect_btn)

			self.start_btn = QPushButton("Start", self)
			self.start_btn.clicked.connect(self.on_start)
			self.start_btn.setEnabled(False)
			btns_v.addWidget(self.start_btn)

			self.stop_btn = QPushButton("Stop", self)
			self.stop_btn.clicked.connect(self.on_stop)
			self.stop_btn.setEnabled(False)
			btns_v.addWidget(self.stop_btn)

			self.backup_btn = QPushButton("Backup", self)
			self.backup_btn.clicked.connect(self.on_backup)
			self.backup_btn.setEnabled(False)
			btns_v.addWidget(self.backup_btn)

			btns_v.addStretch()
			hl.addLayout(btns_v)
			layout.addLayout(hl)

			self.status = QLabel("Ready", self)
			layout.addWidget(self.status)

			# load servers from config
			# Try to import `load_servers` flexibly so the script runs both
			# when executed as a module (python -m src.alsm.main) and when
			# executed directly from the `src/alsm` folder (python main.py).
			try:
				from src.alsm.servers import load_servers, save_servers, Server
			except Exception:
				try:
					# when running from src/alsm as a script
					from servers import load_servers, save_servers, Server
				except Exception:
					# when running as a package (relative import)
					from .servers import load_servers, save_servers, Server

			self._servers = []
			self._load_func = load_servers
			self._save_func = save_servers
			self._Server = Server
			self.load_server_list()

		def on_connect(self):
				# If a server is selected, prefill dialog with its data
				sel = None
				if hasattr(self, "servers_list") and self.servers_list.selectedItems():
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
				self.status.setText("Connecting to {}...".format(data["host"]))
				QApplication.processEvents()
				try:
					import paramiko

					client = paramiko.SSHClient()
					client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
					client.connect(
						hostname=data["host"],
						port=data["port"],
						username=data["username"],
						password=data["password"],
						timeout=5,
					)
					# simple test command
					stdin, stdout, stderr = client.exec_command("echo connected")
					out = stdout.read().decode().strip()
					client.close()
					QMessageBox.information(self, "SSH", f"Connection successful: {out}")
					self.status.setText("Connected")
				except Exception as e:
					QMessageBox.critical(self, "SSH Error", str(e))
					self.status.setText("Connection failed")

		def _run_action(self, action_name: str):
			# helper to run start/stop/backup on selected server
			if not (hasattr(self, "servers_list") and self.servers_list.selectedItems()):
				self.status.setText("No server selected")
				return
			idx = self.servers_list.currentRow()
			server = self._servers[idx]

			from src.alsm import runner
			pwd = None

			# If remote and server has no stored password, ask for one (prefer SSH keys)
			if not runner.is_local(getattr(server, "host", "")) and getattr(server, "username", None):
				# ask password interactively (won't be saved)
				from PyQt6.QtWidgets import QInputDialog
				pw, ok = QInputDialog.getText(self, "SSH Password", f"Password for {server.username}@{server.host}", QLineEdit.EchoMode.Password)
				if ok and pw:
					pwd = pw

			def _cb(res):
				code, out, err = res
				text = f"{action_name}: exit={code}"
				if out:
					text += f" out={out.strip()}"
				if err:
					text += f" err={err.strip()}"
				# schedule UI update on main thread
				from PyQt6.QtCore import QTimer

				QTimer.singleShot(0, lambda: self.status.setText(text))

			self.status.setText(f"{action_name} running...")
			runner.run_in_thread(
				getattr(runner, f"{action_name.lower()}_server"),
				args=(server, pwd),
				callback=_cb,
			)

		def on_start(self):
			self._run_action("Start")

		def on_stop(self):
			self._run_action("Stop")

		def on_backup(self):
			self._run_action("Backup")

		def load_server_list(self):
			try:
				self._servers = self._load_func()
			except Exception as e:
				self._servers = []
				self.status.setText(f"Failed to load servers: {e}")
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
				self._servers.append(new)
				try:
					self._save_func(self._servers)
				except Exception as e:
					self.status.setText(f"Save failed: {e}")
				# optionally write INI file to disk
				if data.get("write_ini_on_save") and data.get("usersettings_path") and data.get("usersettings_content"):
					try:
						p = Path(data.get("usersettings_path"))
						p.parent.mkdir(parents=True, exist_ok=True)
						p.write_text(data.get("usersettings_content"), encoding="utf-8")
					except Exception as e:
						self.status.setText(f"INI write failed: {e}")
						QMessageBox.warning(self, "INI Save Failed", str(e))
				self.load_server_list()

			def on_new_from_template(self):
				# create a reasonable ARK Pre-Aquatic template
				tpl = {
					"name": "New ARK Pre-Aquatic Server",
					"host": "127.0.0.1",
					"port": 22,
					"username": "ark",
					"autostart": False,
					"ark_path": "/home/ark/server",
					"systemd_unit": None,
					"map": "TheIsland_P",
					"ark_start_params": "-server -log -noBattlEye",
					"usersettings_content": "[ServerSettings]\nServerAdminPassword=\nMaxPlayers=70\nQueryPort=27015\nPort=7777\n",
					"usersettings_path": None,
					"ssh_key_path": None,
				}

				# open editor prefilled
				tmp = self._Server.from_dict(tpl)
				dlg = ServerEditorDialog(self, server=tmp)
				if dlg.exec() == QDialog.DialogCode.Accepted:
					data = dlg.get_data()
					try:
						new = self._Server.from_dict(data)
					except Exception:
						new = self._Server(**data)
					self._servers.append(new)
					try:
						self._save_func(self._servers)
					except Exception as e:
						self.status.setText(f"Save failed: {e}")
					# optionally write INI
					if data.get("write_ini_on_save") and data.get("usersettings_path") and data.get("usersettings_content"):
						try:
							p = Path(data.get("usersettings_path"))
							p.parent.mkdir(parents=True, exist_ok=True)
							p.write_text(data.get("usersettings_content"), encoding="utf-8")
						except Exception as e:
							self.status.setText(f"INI write failed: {e}")
							QMessageBox.warning(self, "INI Save Failed", str(e))
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
				try:
					self._save_func(self._servers)
				except Exception as e:
					self.status.setText(f"Save failed: {e}")
				# optionally write INI file to disk
				if data.get("write_ini_on_save") and data.get("usersettings_path") and data.get("usersettings_content"):
					try:
						p = Path(data.get("usersettings_path"))
						p.parent.mkdir(parents=True, exist_ok=True)
						p.write_text(data.get("usersettings_content"), encoding="utf-8")
					except Exception as e:
						self.status.setText(f"INI write failed: {e}")
						QMessageBox.warning(self, "INI Save Failed", str(e))
				self.load_server_list()

		def on_delete(self):
			if not (self.servers_list.selectedItems()):
				return
			idx = self.servers_list.currentRow()
			server = self._servers[idx]
			res = QMessageBox.question(self, "Delete", f"Delete server '{server.name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
			if res == QMessageBox.StandardButton.Yes:
				del self._servers[idx]
				try:
					self._save_func(self._servers)
				except Exception as e:
					self.status.setText(f"Save failed: {e}")
				self.load_server_list()

		def on_selection_changed(self):
			has = bool(self.servers_list.selectedItems())
			self.connect_btn.setEnabled(has)
			self.edit_btn.setEnabled(has)
			self.delete_btn.setEnabled(has)
			self.start_btn.setEnabled(has)
			self.stop_btn.setEnabled(has)
			self.backup_btn.setEnabled(has)


	def gui_main():
		app = QApplication(sys.argv)
		w = MainWindow()
		w.show()
		sys.exit(app.exec())

else:
	def console_main():
		print("PyQt6 is not available in the current environment.")
		print("To enable the GUI, install PyQt6 and PyQt6-sip in the project's virtualenv:")
		print(r"\n  Windows (PowerShell):")
		print(r"    . \.venv\\Scripts\\Activate.ps1")
		print(r"    pip install PyQt6 PyQt6-sip\n")
		print("  Linux / macOS:")
		print("    python3 -m venv .venv")
		print("    . .venv/bin/activate")
		print("    pip install PyQt6 PyQt6-sip\n")
		print("The script can also be extended to run in console mode; for now it exits.")


if __name__ == "__main__":
	if HAVE_QT:
		gui_main()
	else:
		console_main()