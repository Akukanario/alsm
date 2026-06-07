from dataclasses import dataclass, asdict
from pathlib import Path
import json
from typing import List, Optional


@dataclass
class Server:
    name: str
    host: str
    port: int = 22
    username: Optional[str] = None
    password: Optional[str] = None
    autostart: bool = False
    ark_path: Optional[str] = None
    ssh_key_path: Optional[str] = None
    systemd_unit: Optional[str] = None
    map: Optional[str] = None
    ark_start_params: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Server":
        return Server(
            name=d.get("name", ""),
            host=d.get("host", ""),
            port=int(d.get("port", 22)),
            username=d.get("username"),
            password=d.get("password"),
            autostart=bool(d.get("autostart", False)),
            ark_path=d.get("ark_path"),
            ssh_key_path=d.get("ssh_key_path"),
            systemd_unit=d.get("systemd_unit"),
            map=d.get("map"),
            ark_start_params=d.get("ark_start_params"),
        )


def _default_config_path() -> Path:
    # repo root / servers.json (src/alsm/ -> parents[2] = repo root)
    return Path(__file__).resolve().parents[2] / "servers.json"


def load_servers(path: Optional[str] = None) -> List[Server]:
    p = Path(path) if path else _default_config_path()
    if not p.exists():
        # create a minimal example config
        default = [
            {
                "name": "Example ARK Server",
                "host": "192.168.1.100",
                "port": 22,
                "username": "root",
                "autostart": False,
                "ark_path": "/home/ark/server",
            }
        ]
        p.write_text(json.dumps(default, indent=2), encoding="utf-8")
    raw = json.loads(p.read_text(encoding="utf-8"))
    return [Server.from_dict(item) for item in raw]


def save_servers(servers: List[Server], path: Optional[str] = None) -> None:
    p = Path(path) if path else _default_config_path()
    data = [s.to_dict() for s in servers]
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    # quick smoke test
    sv = load_servers()
    print(f"Loaded {len(sv)} server(s)")
    for s in sv:
        print(s)
