from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ServerStatus(str, Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ServiceCheck:
    name: str
    port: int
    host: str | None = None


@dataclass(frozen=True)
class ServerConfig:
    name: str
    url: str
    role: str = "Server"
    ip: str = ""
    checks: tuple[ServiceCheck, ...] = ()


@dataclass(frozen=True)
class Settings:
    interval: float = 2.0
    timeout: float = 1.5
    stale_after: float = 8.0
    cpu_warning: float = 90.0
    memory_warning: float = 85.0
    disk_warning: float = 80.0


@dataclass
class ServerMetrics:
    cpu: float | None = None
    memory: float | None = None
    disk: float | None = None
    load: float | None = None
    uptime: float | None = None
    rx: float | None = None
    tx: float | None = None
    mem_total: float | None = None
    mem_available: float | None = None
    mem_free: float | None = None
    mem_cached: float | None = None
    mem_used: float | None = None
    disk_total: float | None = None
    disk_used: float | None = None
    hostname: str = ""
    os: str = ""
    kernel: str = ""
    gpus: list[dict[str, Any]] = field(default_factory=list)
    network_counters: tuple[float, float] | None = None
    boot_time: float | None = None


@dataclass
class PollResult:
    data: dict | None = None
    error: str = ""
    failure_status: ServerStatus = ServerStatus.UNKNOWN
    checks: dict[str, bool] = field(default_factory=dict)


@dataclass
class ServerState:
    config: ServerConfig
    status: ServerStatus = ServerStatus.UNKNOWN
    metrics: ServerMetrics | None = None
    last_seen: float | None = None  # monotonic; unaffected by NTP changes
    last_response: float | None = None  # successful metrics response, wall clock
    last_attempt: float | None = None
    latency_ms: float | None = None
    issues: list[str] = field(default_factory=lambda: ["Waiting for first response"])
    checks: dict[str, bool] = field(default_factory=dict)
    cpu_history: deque = field(default_factory=lambda: deque(maxlen=60))
    previous_network: tuple[float, float, float, float | None] | None = None


@dataclass(frozen=True)
class Event:
    timestamp: float
    name: str
    message: str
    status: ServerStatus
