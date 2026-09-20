import math
from dashboard.core.models import ServerMetrics, ServerStatus


def number(value, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        value = float(value)
    except (OverflowError, ValueError):
        return None
    if not math.isfinite(value) or value < 0 or (maximum is not None and value > maximum):
        return None
    return value


def clean(value):
    # Remote labels are plain text, never Rich markup or terminal control codes.
    return "".join(c for c in str(value) if c.isprintable())[:180]


def normalize(data):
    total, available, used = (number(data.get(k)) for k in ("mem_total", "mem_available", "mem_used"))
    memory = None
    if total and available is not None and available <= total:
        used = total - available
        memory = 100 * used / total
    elif total and used is not None and used <= total:
        memory = 100 * used / total
    load = data.get("load")
    if isinstance(load, (list, tuple)):
        load = load[0] if load else None
    network = data.get("network")
    counters = None
    if isinstance(network, dict):
        rx, tx = number(network.get("bytes_recv")), number(network.get("bytes_sent"))
        if rx is not None and tx is not None:
            counters = (rx, tx)
    gpus = []
    if isinstance(data.get("gpus"), list):
        for gpu in data["gpus"][:16]:
            if isinstance(gpu, dict):
                gpus.append({"name": clean(gpu.get("name", "GPU")),
                             **{k: number(gpu.get(k), 100 if k == "util" else None)
                                for k in ("util", "temp", "mem_used", "mem_total")}})
    return ServerMetrics(
        cpu=number(data.get("cpu"), 100), memory=memory,
        disk=number(data.get("disk"), 100), load=number(load),
        uptime=number(data.get("uptime")), mem_total=total, mem_used=used,
        mem_available=available, mem_free=number(data.get("mem_free")), mem_cached=number(data.get("mem_cached")),
        disk_total=number(data.get("disk_total")), disk_used=number(data.get("disk_used")),
        hostname=clean(data.get("hostname", "")),
        os=clean(f"{data.get('distro_name', '')} {data.get('distro_version', '')}".strip()),
        kernel=clean(data.get("kernel", "")), gpus=gpus,
        network_counters=counters, boot_time=number(data.get("boot_time")),
    )


def evaluate(metrics, checks, settings):
    issues = []
    for label, value, threshold in (("CPU", metrics.cpu, settings.cpu_warning),
                                     ("Memory", metrics.memory, settings.memory_warning),
                                     ("Disk", metrics.disk, settings.disk_warning)):
        if value is None:
            issues.append(f"{label} unavailable")
        elif value >= threshold:
            issues.append(f"{label} ≥ {threshold:g}%")
    issues.extend(f"{name} TCP check failed" for name, ok in checks.items() if not ok)
    return (ServerStatus.DEGRADED if issues else ServerStatus.ONLINE), issues
