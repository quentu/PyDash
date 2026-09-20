from rich.panel import Panel
from rich.console import Group
from rich.text import Text
from rich.layout import Layout
from rich.columns import Columns
from rich import box
import time
from dashboard.core.health import clean
from dashboard.core.models import ServerStatus

COLORS = {ServerStatus.ONLINE: "green", ServerStatus.DEGRADED: "yellow",
          ServerStatus.OFFLINE: "red", ServerStatus.UNKNOWN: "bright_black"}
SYMBOLS = {ServerStatus.ONLINE: "●", ServerStatus.DEGRADED: "▲",
           ServerStatus.OFFLINE: "●", ServerStatus.UNKNOWN: "○"}


def text(value, style=""):
    return Text(clean(value), style=style, no_wrap=True, overflow="ellipsis")


def duration(seconds):
    if seconds is None:
        return "--"
    seconds = max(0, int(seconds))
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s" if seconds else "<1s"


def bytes_short(value):
    if value is None:
        return "--"
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.1f}{unit}" if unit != "B" else f"{value:.0f}B"
        value /= 1024


def percent(value):
    return "--" if value is None else f"{value:.0f}%"


def metric_row(label, value, threshold, width, detail=""):
    color = "bright_black" if value is None else "red" if value >= 95 else "yellow" if value >= threshold else "green"
    row = Table.grid(expand=True, padding=(0, 1))
    row.add_column(width=7)
    row.add_column(width=5, justify="right")
    row.add_column(ratio=1)
    if width >= 66:
        row.add_column(width=21, justify="right")
    bar_width = max(3, min(40, width - (43 if width >= 66 else 21)))
    filled = 0 if value is None else round(bar_width * value / 100)
    bar = Text("━" * filled, style=color)
    bar.append("─" * (bar_width - filled), style="bright_black")
    cells = [text(label, "bold"), text(percent(value), color), bar]
    if width >= 66:
        cells.append(text(detail, "dim"))
    row.add_row(*cells)
    return row


def pair(left, right):
    row = Table.grid(expand=True, padding=(0, 1))
    row.add_column(ratio=1, no_wrap=True, overflow="ellipsis")
    row.add_column(justify="right", no_wrap=True, overflow="ellipsis")
    row.add_row(left, right)
    return row


def make_panel(state, width, height, settings, now=None):
    now = time.monotonic() if now is None else now
    color = COLORS[state.status]
    name = text(state.config.name.upper(), "bold white")
    name.truncate(max(1, width - len(state.status.value) - 11), overflow="ellipsis")
    title = Text.assemble(name, (f"  {SYMBOLS[state.status]} {state.status.value}", f"bold {color}"))
    seen = "Never" if state.last_seen is None else duration(now - state.last_seen) + " ago"
    metrics = state.metrics
    cpu, memory, disk = (getattr(metrics, key, None) for key in ("cpu", "memory", "disk"))
    issue = "; ".join(state.issues) if state.issues else "All reported checks healthy"
    budget = max(1, height - 2)
    lines = []
    if budget <= 5:
        if state.status in (ServerStatus.OFFLINE, ServerStatus.UNKNOWN) or metrics is None:
            lines.append(text(issue, color))
        else:
            lines.append(text(f"CPU {percent(cpu)}   MEM {percent(memory)}   DISK {percent(disk)}"))
        if budget >= 2:
            lines.append(text(f"Seen: {seen}" + (f" • {issue}" if state.issues else ""), color if state.issues else "dim"))
        if budget >= 3:
            lines.append(text(f"{state.config.role} · {state.config.ip}", "dim"))
        if budget >= 4:
            lines.append(text(f"LOAD {getattr(metrics, 'load', None) if getattr(metrics, 'load', None) is not None else '--'}   UP {duration(getattr(metrics, 'uptime', None))}", "dim"))
        if budget >= 5:
            lines.append(text(f"NET ↓ {bytes_short(getattr(metrics, 'rx', None))}/s ↑ {bytes_short(getattr(metrics, 'tx', None))}/s", "dim"))
    else:
        lines.append(pair(text(state.config.role, "dim"), text(state.config.ip, "dim")))
        if budget >= 12:
            lines.append(Text(""))
        for label, value, threshold, used, total in (
            ("CPU", cpu, settings.cpu_warning, None, None),
            ("MEMORY", memory, settings.memory_warning, getattr(metrics, "mem_used", None), getattr(metrics, "mem_total", None)),
            ("DISK /", disk, settings.disk_warning, getattr(metrics, "disk_used", None), getattr(metrics, "disk_total", None)),
        ):
            detail = f"{bytes_short(used)} / {bytes_short(total)}" if total else ""
            lines.append(metric_row(label, value, threshold, width - 6, detail))
        details = []
        load = "--" if metrics is None or metrics.load is None else f"{metrics.load:.2f}"
        details.append(pair(text(f"LOAD  {load}"), text(f"UPTIME  {duration(getattr(metrics, 'uptime', None))}")))
        details.append(text(f"NET   ↓ {bytes_short(getattr(metrics, 'rx', None))}/s   ↑ {bytes_short(getattr(metrics, 'tx', None))}/s"))
        checks = Text("CHECKS  ", style="dim")
        if state.config.checks:
            for index, check in enumerate(state.config.checks):
                if index:
                    checks.append("  ")
                ok = state.checks.get(check.name)
                checks.append(("✓ " if ok else "✗ " if ok is False else "○ ") + clean(check.name),
                              style="green" if ok else "yellow" if ok is False else "bright_black")
        else:
            checks.append("Agent /stats only", style="dim")
        checks.no_wrap, checks.overflow = True, "ellipsis"
        details.append(checks)
        if metrics:
            for gpu in metrics.gpus:
                temp = "--" if gpu["temp"] is None else f"{gpu['temp']:.0f}°C"
                details.append(text(f"GPU   {gpu['name']} · {percent(gpu['util'])} · {temp} · {format(gpu['mem_used'], '.0f') if gpu['mem_used'] is not None else '--'}/{format(gpu['mem_total'], '.0f') if gpu['mem_total'] is not None else '--'} MiB", "dim"))
            if budget >= 16:
                details.append(text(f"RAM   Available {bytes_short(metrics.mem_available)} · Cached {bytes_short(metrics.mem_cached)} · Free {bytes_short(metrics.mem_free)}", "dim"))
                levels = "▁▂▃▄▅▆▇█"
                trend = "".join(levels[min(7, int(value * 8 / 100))] for value in state.cpu_history)
                details.append(text(f"CPU HISTORY  {trend}", "green" if cpu is not None and cpu < settings.cpu_warning else color))
            if metrics.os:
                details.append(text(f"OS    {metrics.os} · {metrics.kernel}", "dim"))
        room = budget - len(lines) - 2
        lines.extend(details[:max(0, room)])
        while len(lines) < budget - 2:
            lines.append(Text(""))
        lines.append(text(("✓ " if not state.issues else "! ") + issue, color))
        last = f"LAST SEEN  {seen}"
        if state.last_response is not None and width >= 70:
            last += f" · {time.strftime('%H:%M:%S', time.localtime(state.last_response))}"
        latency = "" if state.latency_ms is None else f"{state.latency_ms:.0f}ms"
        lines.append(pair(text(last, "dim"), text(latency, "dim")))
    return Panel(Group(*lines), title=title, title_align="left", box=box.ROUNDED,
                 border_style=color, padding=(0, 2 if width >= 45 else 1), height=height)

     
