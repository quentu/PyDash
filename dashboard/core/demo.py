import math
import time
from dashboard.core.manager import Monitor
from dashboard.core.models import ServerConfig, Settings, PollResult, ServerStatus, ServiceCheck


class DemoMonitor(Monitor):
    def __init__(self):
        servers = [ServerConfig(name, "http://example.invalid/stats", role, ip,
                                (ServiceCheck(service, 443),))
                   for name, role, ip, service in (
                        ("monitor-01", "Monitoring / Network", "192.0.2.10", "HTTPS"),
                        ("storage-01", "Production / Storage", "192.0.2.20", "Jellyfin"),
                        ("backup-01", "Backup / Quorum", "192.0.2.30", "Backup"),
                        ("hypervisor-01", "Virtualization", "192.0.2.40", "Proxmox"))]
        super().__init__(servers, Settings())
        self.started = time.monotonic()
        self.last_demo_poll = 0

    def tick(self, now=None, wall=None):
        now = time.monotonic() if now is None else now
        wall = time.time() if wall is None else wall
        if now - self.last_demo_poll < self.settings.interval:
            return
        elapsed = now - self.started
        self.last_demo_poll, self.last_refresh = now, wall
        for index, state in enumerate(self.states):
            if index == 2 and elapsed % 45 < 20:
                if state.last_seen is None:
                    state.last_seen, state.last_response = now - 222, wall - 222
                self._failure(state, ServerStatus.OFFLINE, "Agent unreachable / timeout", wall)
                continue
            total = (16 if index != 1 else 64) * 1024**3
            memory = (42, 71, 24, 58)[index]
            data = {"hostname": state.config.name, "cpu": (24, 67, 8, 36)[index] + 4 * math.sin(elapsed / 5 + index),
                    "mem_total": total, "mem_available": total * (1 - memory / 100),
                    "disk": (38, 84, 28, 54)[index], "disk_total": 2 * 1024**4,
                    "disk_used": 2 * 1024**4 * (38, 84, 28, 54)[index] / 100,
                    "load": [0.42 + index * 0.56], "uptime": 86400 * (14 + index * 6) + elapsed,
                    "distro_name": "Debian GNU/Linux", "distro_version": "13", "kernel": "6.12-amd64",
                    "boot_time": 1, "network": {"bytes_recv": now * (index + 1) * 1024**2,
                                                "bytes_sent": now * (index + 1) * 240000}}
            self._accept(state, PollResult(data=data, checks={state.config.checks[0].name: True}), now, wall, 0.012 + index * 0.007)
