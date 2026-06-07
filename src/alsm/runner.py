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


def run_local_stream(cmd: str, cwd: Optional[str] = None, timeout: int = 0, line_callback=None) -> Tuple[int, str, str]:
    """
    Run a local command and stream stdout/stderr line-by-line via line_callback(kind, text).
    Returns (returncode, stdout_all, stderr_all) after completion.
    If timeout<=0, no timeout is applied.
    """
    try:
        proc = subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    except Exception as e:
        return 1, '', str(e)

    out_lines = []
    err_lines = []

    def _read_stream(stream, kind, collector):
        try:
            for line in iter(stream.readline, ''):
                if not line:
                    break
                collector.append(line)
                if line_callback:
                    try:
                        line_callback(kind, line)
                    except Exception:
                        pass
        finally:
            try:
                stream.close()
            except Exception:
                pass

    t_out = threading.Thread(target=_read_stream, args=(proc.stdout, 'out', out_lines), daemon=True)
    t_err = threading.Thread(target=_read_stream, args=(proc.stderr, 'err', err_lines), daemon=True)
    t_out.start()
    t_err.start()

    # wait for process
    proc.wait()
    t_out.join()
    t_err.join()

    return proc.returncode, ''.join(out_lines), ''.join(err_lines)


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


def run_ssh_stream(host: str, port: int, username: Optional[str], password: Optional[str], cmd: str, line_callback=None, timeout: int = 300) -> Tuple[int, str, str]:
    """
    Attempt to run SSH command and stream output via line_callback(kind, text).
    If paramiko is unavailable or streaming fails, fall back to run_ssh and return full output.
    """
    try:
        import paramiko
    except Exception as e:
        # paramiko not available; fallback
        rc, out, err = run_ssh(host, port, username, password, cmd, timeout=timeout)
        if out and line_callback:
            try:
                line_callback('out', out)
            except Exception:
                pass
        if err and line_callback:
            try:
                line_callback('err', err)
            except Exception:
                pass
        return rc, out, err

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10, allow_agent=True, look_for_keys=True)
        transport = client.get_transport()
        chan = transport.open_session()
        chan.exec_command(cmd)
        out_buf = []
        err_buf = []
        while True:
            if chan.recv_ready():
                data = chan.recv(1024).decode(errors='ignore')
                out_buf.append(data)
                if line_callback:
                    try:
                        line_callback('out', data)
                    except Exception:
                        pass
            if chan.recv_stderr_ready():
                data = chan.recv_stderr(1024).decode(errors='ignore')
                err_buf.append(data)
                if line_callback:
                    try:
                        line_callback('err', data)
                    except Exception:
                        pass
            if chan.exit_status_ready() and not chan.recv_ready() and not chan.recv_stderr_ready():
                break
        exit_status = chan.recv_exit_status()
        client.close()
        return exit_status, ''.join(out_buf), ''.join(err_buf)
    except Exception as e:
        return 1, '', str(e)


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


def run_in_thread_stream(target, args=(), line_callback=None, done_callback=None):
    def _worker():
        try:
            res = target(*args, line_callback=line_callback)
            if done_callback:
                try:
                    done_callback(res)
                except Exception:
                    pass
        except TypeError:
            # target doesn't accept line_callback; call normally
            res = target(*args)
            if done_callback:
                try:
                    done_callback(res)
                except Exception:
                    pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


def run_action_stream(action: str, server, password: Optional[str] = None, line_callback=None, done_callback=None):
    """Run start/stop/backup action and stream output via line_callback(kind,text)."""
    action = action.lower()
    if action == 'start':
        cmd = _default_start_cmd(getattr(server, 'ark_path', None))
    elif action == 'stop':
        cmd = _default_stop_cmd(getattr(server, 'ark_path', None))
    elif action == 'backup':
        cmd = _default_backup_cmd(getattr(server, 'ark_path', None))
    else:
        return run_in_thread(lambda: (1, '', f'Unknown action {action}'))

    if is_local(getattr(server, 'host', '')):
        return run_in_thread_stream(run_local_stream, args=(cmd, getattr(server, 'ark_path', None), 0), line_callback=line_callback, done_callback=done_callback)
    else:
        # attempt SSH stream; if paramiko missing, run_ssh will be used inside run_ssh_stream
        def _remote_wrapper(cmd, line_callback=None):
            rc, out, err = run_ssh_stream(getattr(server, 'host'), getattr(server, 'port', 22), getattr(server, 'username', None), password, cmd)
            return rc, out, err

        return run_in_thread_stream(lambda *a, **k: run_ssh_stream(getattr(server, 'host'), getattr(server, 'port', 22), getattr(server, 'username', None), password, cmd, line_callback=line_callback), args=(), line_callback=line_callback, done_callback=done_callback)


def upload_dir_sftp(host: str, port: int, username: Optional[str], password: Optional[str], local_dir: str, remote_dir: str, key_filename: Optional[str] = None, timeout: int = 10) -> Tuple[bool, str]:
    """
    Recursively upload `local_dir` to `remote_dir` via SFTP using paramiko.
    Returns (success, message).
    """
    try:
        import paramiko
    except Exception as e:
        return False, f'Paramiko not available: {e}'

    try:
        transport = paramiko.Transport((host, port))
        if key_filename:
            pkey = None
            try:
                pkey = paramiko.RSAKey.from_private_key_file(key_filename)
            except Exception:
                pkey = None
            transport.connect(username=username, pkey=pkey)
        else:
            transport.connect(username=username, password=password)

        sftp = paramiko.SFTPClient.from_transport(transport)

        def _ensure_remote_dir(path):
            try:
                sftp.listdir(path)
            except IOError:
                parent = os.path.dirname(path.rstrip('/'))
                if parent:
                    _ensure_remote_dir(parent)
                try:
                    sftp.mkdir(path)
                except Exception:
                    pass

        _ensure_remote_dir(remote_dir)

        for root, dirs, files in os.walk(local_dir):
            rel = os.path.relpath(root, local_dir)
            if rel == '.':
                rroot = remote_dir
            else:
                rroot = os.path.join(remote_dir, rel).replace('\\', '/')
                _ensure_remote_dir(rroot)
            for f in files:
                local_path = os.path.join(root, f)
                remote_path = (rroot + '/' + f).replace('\\', '/')
                try:
                    sftp.put(local_path, remote_path)
                except Exception as e:
                    return False, f'Failed to upload {local_path}: {e}'

        sftp.close()
        transport.close()
        return True, 'Upload complete'
    except Exception as e:
        try:
            transport.close()
        except Exception:
            pass
        return False, str(e)


def send_rcon(host: str, port: int, password: str, command: str, timeout: int = 10) -> Tuple[int, str, str]:
    """
    Send an RCON command to the game server. Tries to use the `rcon` package (pip install rcon).
    Returns (code, stdout, stderr) where code==0 indicates success.
    """
    try:
        from rcon.client import Client as RconClient
    except Exception:
        try:
            # try alternative package
            from rcon import Client as RconClient
        except Exception:
            return 1, '', 'RCON library not available (install package `rcon`)'

    try:
        with RconClient(host, port, password, timeout=timeout) as c:
            resp = c.run(command)
        return 0, str(resp), ''
    except Exception as e:
        return 1, '', str(e)


def run_rcon_in_thread(host: str, port: int, password: str, command: str, callback=None):
    def _worker():
        res = send_rcon(host, port, password, command)
        if callback:
            try:
                callback(res)
            except Exception:
                pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t
