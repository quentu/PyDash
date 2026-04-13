import psutil
import time 
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live

console = Console()

def get_stats():
    return {
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory(),
        "disk": psutil.disk_usage('/'),
        "net": psutil.net_io_counters()
    }

# PANELS
def cpu_panel(cpu):
    color = "green" if cpu < 50 else "yellow" if cpu < 80 else "red"
    return Panel(f"[bold {color}]{cpu}%[/bold {color}]", title="CPU Usage")

def memory_panel(mem):
    percent = mem.percent
    color = "green" if percent < 50 else "yellow" if percent < 80 else "red"
    return Panel(
        f"{mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB\n"
        f"[bold {color}]{percent}%[/bold {color}]",
        title="Memory"
    )

def disk_panel(disk):
    percent = disk.percent
    color = "green" if percent < 50 else "yellow" if percent < 80 else "red"
    return Panel(
        f"{disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB\n"
        f"[bold {color}]{percent}%[/bold {color}]",
        title="Disk"
    )

def network_panel(net):
    table = Table.grid()
    table.add_row("Sent:", f"{net.bytes_sent // (1024**2)} MB")
    table.add_row("Recv:", f"{net.bytes_recv // (1024**2)} MB")
    return Panel(table, title="Network")

def header():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return Panel(f"[bold cyan]Server Dashboard[/bold cyan]\n{now}")

# LAYOUT
def make_layout():
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main")
    )

    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )

    layout["left"].split_column(
        Layout(name="cpu"),
        Layout(name="memory")
    )

    layout["right"].split_column(
        Layout(name="disk"),
        Layout(name="network")
    )

    return layout

# MAIN
def main():
    layout = make_layout()

    with Live(layout, refresh_per_second=2, screen=True):
        while True:
            stats = get_stats()

            layout["header"].update(header())
            layout["cpu"].update(cpu_panel(stats["cpu"]))
            layout["memory"].update(memory_panel(stats["memory"]))
            layout["disk"].update(disk_panel(stats["disk"]))
            layout["network"].update(network_panel(stats["net"]))

            time.sleep(1)

if __name__ == "__main__":
    main()
