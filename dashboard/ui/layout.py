from rich.layout import Layout
import math
import time
from collections import Counter
from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from dashboard.core.models import ServerStatus
from dashboard.ui.panels import COLORS, SYMBOLS, duration, make_panel, pair, percent, text

def header(monitor, width, demo=False):
    counts = Counter(state.status for state in monitor.states)
    offline = counts[ServerStatus.OFFLINE]
    degraded = counts[ServerStatus.DEGRADED]
    unknown = counts[ServerStatus.UNKNOWN]
    attention = f"{offline} HOST{'S' if offline != 1 else ''} UNREACHABLE" if offline else "ATTENTION REQUIRED" if degraded else "AWAITING DATA" if unknown else "ALL SYSTEMS HEALTHY"
    color = "red" if offline else "yellow" if degraded else "bright_black" if unknown else "green"
    title = pair(text("INFRASTRUCTURE STATUS", "bold white"), text("DEMO • SIMULATED" if demo else "PYDASH / LIVE", "yellow" if demo else "dim"))
    summary = Text(f"HOSTS {len(monitor.states)}  ", style="bold")
    for status in ServerStatus:
        summary.append(f" {SYMBOLS[status]} {counts[status]} {status.value} ", style=f"bold {COLORS[status]}")
    summary.no_wrap, summary.overflow = True, "ellipsis"
    refreshed = time.strftime("%H:%M:%S", time.localtime(monitor.last_refresh)) if monitor.last_refresh else "--:--:--"
    timing = pair(text(f"LAST REFRESH {refreshed}   •   POLL {monitor.settings.interval:g}s", "dim"), text(attention, f"bold {color}"))
    return Panel(Group(title, summary, timing), box=box.SIMPLE, padding=(0, 1), border_style=color)


def build_layout(monitor, width, height, demo=False, now=None):
    now = time.monotonic() if now is None else now
    states = monitor.states
    columns = 2 if width >= 112 and len(states) > 1 else 1
    rows = math.ceil(len(states) / columns)
    header_height = 5
    event_height = 5 if height - header_height - 1 >= rows * 14 + 5 else 0
    available = height - header_height - event_height - 1
    root = Layout()
    top = Layout(header(monitor, width, demo), name="header", size=header_height)
    body = Layout(name="hosts")
    footer = Layout(text("  CTRL+C exit  •  TCP checks run from this display  •  -- means unavailable", "dim"), size=1)
    parts = [top, body]
    if event_height:
        event_lines = []
        for event in list(monitor.events)[:3]:
            stamp = time.strftime("%H:%M:%S", time.localtime(event.timestamp))
            event_lines.append(text(f"{stamp}  {SYMBOLS[event.status]} {event.name}  {event.message}", COLORS[event.status]))
        if not event_lines:
            event_lines = [text("Waiting for host status changes", "dim")]
        parts.append(Layout(Panel(Group(*event_lines), title="RECENT EVENTS", title_align="left",
                                  border_style="bright_black", padding=(0, 2), box=box.ROUNDED), size=event_height))
    parts.append(footer)
    root.split_column(*parts)
    if available < rows * 4:
        table = Table(box=box.SIMPLE, expand=True, padding=(0, 1))
        table.add_column("STATUS", width=10)
        table.add_column("HOST", ratio=1, no_wrap=True, overflow="ellipsis")
        if width >= 65:
            table.add_column("CPU / MEM / DISK", no_wrap=True)
        table.add_column("LAST SEEN", no_wrap=True)
        visible = max(0, available - 4)
        for state in states[:visible]:
            values = [text(state.status.value, COLORS[state.status]), text(state.config.name, "bold")]
            if width >= 65:
                values.append(text(" / ".join(percent(getattr(state.metrics, k, None)) for k in ("cpu", "memory", "disk"))))
            values.append(text("Never" if state.last_seen is None else duration(now - state.last_seen) + " ago", "dim"))
            table.add_row(*values)
        notice = f"Resize terminal: {len(states) - visible} host(s) cannot fit" if len(states) > visible else "Compact inventory · enlarge terminal for host cards"
        body.update(Group(table, text(notice, "yellow")))
        return root
    row_layouts = []
    base_height, extra = divmod(available, rows)
    for index in range(rows):
        row_height = base_height + (index < extra)
        row = Layout(size=row_height)
        children = []
        for column, state in enumerate(states[index * columns:(index + 1) * columns]):
            card_width = width // columns + (column < width % columns)
            children.append(Layout(make_panel(state, card_width, row_height, monitor.settings, now)))
        if len(children) < columns:
            children.append(Layout(Text("")))
        row.split_row(*children)
        row_layouts.append(row)
    body.split_column(*row_layouts)
    return root