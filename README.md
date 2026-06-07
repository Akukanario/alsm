ALSM — Asistente de servidores ARK (español)

Resumen
- ALSM es una herramienta GUI para gestionar servidores ARK: crear servidores desde cero o desde plantillas, editar INI, iniciar/detener/respaldar, conectarse por SSH y enviar comandos RCON.

Requisitos
- Python 3.11+ (se recomienda usar un entorno virtual).
- Dependencias (instálalas con `pip install -r requirements.txt`):
	- PyQt6
	- paramiko (SSH/SFTP)
	- rcon (opcional, para RCON)

Instalación rápida (Windows PowerShell)
```powershell
cd F:\\cursoLinux\\Curso-Linux\\ALSM
. .\\.venv\\Scripts\\Activate.ps1    # o crea un venv: python -m venv .venv; . .\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python -m src.alsm.main
```

Linux / macOS (bash)
```bash
cd /ruta/al/proyecto
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.alsm.main
```

Uso básico
- Ejecuta la aplicación y verás la lista de servidores (gestiona `servers.json` en la carpeta del proyecto).
- Crear servidor desde cero: usa el botón "Create (From Scratch)" y selecciona carpeta destino; la app generará los INI básicos.
- Editar INI: selecciona Edit para abrir el editor integrado con secciones (jugadores, dinos, recursos, estructuras).
- Crear remoto: usa "Create Remote (SSH)" para subir archivos via SFTP y escribir los INI en el servidor remoto.
- Logs y comandos: la app muestra logs en tiempo real al iniciar/parar/respaldos.
- RCON: pulsa "RCON" sobre un servidor con RCON habilitado para enviar comandos remotos.
	- Si no has instalado `rcon`, instala con `pip install rcon` para habilitar soporte RCON.

Notas y recomendaciones
- Ejecuta la app desde la raíz del proyecto para que las rutas relativas funcionen correctamente.
- Si usas Windows, activa el entorno virtual con PowerShell como se muestra arriba.
- SSH: la app usa `paramiko`; algunas distribuciones requieren paquetes del sistema para compilar dependencias.
- RCON: asegúrate de tener el puerto RCON y la contraseña configurados en el servidor ARK.

Contribuir
- Pull requests e issues bienvenidos. Para tests y desarrollo, añade casos en `tests/`.

Archivos importantes
- [src/alsm/main.py](src/alsm/main.py) — interfaz y dialogs.
- [src/alsm/runner.py](src/alsm/runner.py) — helpers para ejecutar comandos, streaming, SSH/SFTP y RCON.
- [src/alsm/ini_templates.py](src/alsm/ini_templates.py) — presets y generación de INI.
- requirements.txt — dependencias.

Contacto
- Este proyecto es parte del ejercicio del curso; para dudas sobre el uso, responde en el repositorio o explícame qué funcionalidad quieres mejorar.
