import sys


# Try to import PyQt6; if unavailable, fall back to a console message
HAVE_QT = True
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
		QListWidget,
		QHBoxLayout,
	)
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
			from src.alsm.servers import load_servers

			self._servers = []
			self._load_func = load_servers
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

		def on_selection_changed(self):
			has = bool(self.servers_list.selectedItems())
			self.connect_btn.setEnabled(has)


	def gui_main():
		app = QApplication(sys.argv)
		w = MainWindow()
		w.show()
		sys.exit(app.exec())

else:
	def console_main():
		print("PyQt6 is not available in the current environment.")
		print("To enable the GUI, install PyQt6 and PyQt6-sip in the project's virtualenv:")
		print("\n    . \.venv\\Scripts\\Activate.ps1")
		print("    pip install PyQt6 PyQt6-sip\n")
		print("The script can also be extended to run in console mode; for now it exits.")


if __name__ == "__main__":
	if HAVE_QT:
		gui_main()
	else:
		console_main()