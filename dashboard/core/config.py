import os
import shutil
import yaml
from pathlib import Path
import math
from urllib.parse import urlsplit
from dashboard.core.models import ServerConfig, ServiceCheck, Settings

CONFIG_DIR = Path(
    os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
) / "pydash"

DEFAULT_CONFIG = CONFIG_DIR / "servers.yaml"

BUNDLED_CONFIG = Path(__file__).resolve().parents[1] / "config" / "servers.yaml"

def ensure_default_config():
    if DEFAULT_CONFIG.exists():
        return
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BUNDLED_CONFIG, DEFAULT_CONFIG)

def load_config(path=DEFAULT_CONFIG):
    path = Path(path)

    if path == DEFAULT_CONFIG:
        ensure_default_config()
    try:
        document = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"Cannot load {path}: {exc}") from exc
    if not isinstance(document, dict) or not isinstance(document.get("servers"), list):
        raise ValueError("Configuration must contain a servers list")
    if not document["servers"]:
        raise ValueError("Configure at least one server")
    options = document.get("dashboard", {})
    if not isinstance(options, dict):
        raise ValueError("dashboard must be a mapping")
    unknown = set(options) - set(Settings.__dataclass_fields__)
    if unknown:
        raise ValueError(f"Unknown dashboard option(s): {', '.join(sorted(unknown))}")
    for key, value in options.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"dashboard.{key} must be a positive finite number")
        if key.endswith("warning") and value > 100:
            raise ValueError(f"dashboard.{key} must be at most 100")
    settings = Settings(**options)
    if settings.interval < 0.2 or settings.timeout < 0.1:
        raise ValueError("interval must be >= 0.2s and timeout >= 0.1s")
    if settings.stale_after < max(settings.interval, settings.timeout):
        raise ValueError("stale_after must be >= interval and timeout")
    servers, names = [], set()
    for item in document["servers"]:
        if not isinstance(item, dict):
            raise ValueError("Each server must be a mapping")
        name, url = item.get("name"), item.get("url")
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError("Server names must be nonempty and unique")
        if not isinstance(url, str):
            raise ValueError(f"{name}: url is required")
        try:
            address = urlsplit(url)
            _ = address.port
            if address.scheme not in ("http", "https") or not address.hostname:
                raise ValueError()
        except ValueError as exc:
            raise ValueError(f"{name}: use a valid http(s) stats URL") from exc
        checks = item.get("checks", [])
        if not isinstance(checks, list) or len(checks) > 16:
            raise ValueError(f"{name}: checks must be a list of at most 16 TCP checks")
        parsed, check_names = [], set()
        for check in checks:
            if not isinstance(check, dict):
                raise ValueError(f"{name}: each check must be a mapping")
            label, port, host = check.get("name"), check.get("port"), check.get("host")
            if not isinstance(label, str) or not label.strip() or label in check_names:
                raise ValueError(f"{name}: check names must be nonempty and unique")
            if type(port) is not int or not 1 <= port <= 65535:
                raise ValueError(f"{name}: check port must be 1–65535")
            if host is not None and (not isinstance(host, str) or not host.strip()):
                raise ValueError(f"{name}: check host must be a nonempty string")
            parsed.append(ServiceCheck(label, port, host))
            check_names.add(label)
        role, ip = item.get("role", "Server"), item.get("ip", address.hostname)
        if not isinstance(role, str) or not isinstance(ip, str):
            raise ValueError(f"{name}: role and ip must be strings")
        servers.append(ServerConfig(name, url, role, ip, tuple(parsed)))
        names.add(name)
    return servers, settings

def load_servers(path=DEFAULT_CONFIG):
    return load_config(path)[0]
