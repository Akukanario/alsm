import subprocess
import shlex
import threading
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional


def is_local(host: str) -> bool:
    if not host:
        return True
    h = host.strip().lower()
    return h in ("localhost", "127.0.0.1", "::1")


def run_local(cmd: str, cwd: Optional[str] = None, timeout: int = 300) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as e:
        return 1, "", str(e)


def run_ssh(host: str, port: int, username: Optional[str], password: Optional[str], cmd: str, timeout: int = 300) -> Tuple[int, str, str]:
    # import paramiko lazily
    try:
        import paramiko
    except Exception as e:
        return 1, "", f"Paramiko not available: {e}"

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10, allow_agent=True, look_for_keys=True)
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode()
        err = stderr.read().decode()
        exit_status = stdout.channel.recv_exit_status()
        client.close()
        return exit_status, out, err
    except Exception as e:
        return 1, "", str(e)


def _default_start_cmd(ark_path: Optional[str]) -> str:
    if not ark_path:
        return "echo 'No ark_path configured'"
    # assume a start script
    return f"cd {shlex.quote(ark_path)} && ./start.sh"


def _default_stop_cmd(ark_path: Optional[str]) -> str:
    if not ark_path:
        return "echo 'No ark_path configured'"
    return f"cd {shlex.quote(ark_path)} && ./stop.sh"


def _default_backup_cmd(ark_path: Optional[str]) -> str:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    if not ark_path:
        return "echo 'No ark_path configured'"
    out = f"/tmp/ark-backup-{ts}.tar.gz"
    return f"tar -czf {shlex.quote(out)} -C {shlex.quote(Path(ark_path).parent.as_posix())} {shlex.quote(Path(ark_path).name)} && echo {out}"


def start_server(server, password: Optional[str] = None, timeout: int = 600) -> Tuple[int, str, str]:
    cmd = _default_start_cmd(getattr(server, "ark_path", None))
    if is_local(getattr(server, "host", "")):
        return run_local(cmd, timeout=timeout)
    else:
        return run_ssh(getattr(server, "host"), getattr(server, "port", 22), getattr(server, "username", None), password, cmd, timeout=timeout)


def stop_server(server, password: Optional[str] = None, timeout: int = 600) -> Tuple[int, str, str]:
    cmd = _default_stop_cmd(getattr(server, "ark_path", None))
    if is_local(getattr(server, "host", "")):
        return run_local(cmd, timeout=timeout)
    else:
        return run_ssh(getattr(server, "host"), getattr(server, "port", 22), getattr(server, "username", None), password, cmd, timeout=timeout)


def backup_server(server, password: Optional[str] = None, timeout: int = 3600) -> Tuple[int, str, str]:
    cmd = _default_backup_cmd(getattr(server, "ark_path", None))
    if is_local(getattr(server, "host", "")):
        return run_local(cmd, timeout=timeout)
    else:
        return run_ssh(getattr(server, "host"), getattr(server, "port", 22), getattr(server, "username", None), password, cmd, timeout=timeout)


def run_in_thread(target, args=(), callback=None):
    def _worker():
        res = target(*args)
        if callback:
            try:
                callback(res)
            except Exception:
                pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t
