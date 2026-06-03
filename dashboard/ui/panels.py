from rich.panel import Panel
from rich.console import Group
from rich.text import Text


def color(val):
    return "green" if val < 50 else "yellow" if val < 80 else "red"


def bar(val, width=20):
    filled = int(val / 100 * width)
    empty = width - filled
    c = color(val)
    return f"[{c}]{'■' * filled}[/][bright_black]{'■' * empty}[/] [{c}]{val}%[/]"


def make_panel(name, data):
    name = data ["hostname"]

    if "error" in data:
        return Panel(f"[red]{data['error']}[/red]", title=f"[red]{name}[/red]")

    hostname = data["hostname"]
    distro_name = data.get("distro_name","Unknown")
    distro_version = data.get("distro_version", "Unknown")
    kernel   = data.get("kernel", "Unknown")
    uptime   = data["uptime"]
    cpu      = data["cpu"]
    gpus     = data.get("gpus", [])
    mem      = data["memory"]
    disk     = data["disk"]
    
    days    = uptime // 86400
    hours   = (uptime % 86400) // 3600
    minutes = ((uptime % 86400) % 3600) // 60
    
    gpu_lines = ""

    if gpus:
        for gpu in gpus:
            if gpu['index'] > 0:
                label = f"GPU{gpu['index']}"
            else:
                label = f"GPU"
            gpu_name  = gpu["name"]
            temp  = gpu["temp"]

            gpu_lines += (
                f"[bright_black]{label:<7} :[/]  {bar(gpu['util'])} "
                f"[bright_black]{temp}°C[/] [bright_black]{gpu_name}[/]\n"
            )
    else:
        gpu_lines = ""
    #    gpu_lines = f"[bright_black]GPU     :[/]  NOT INSTALLED\n"
    
    lines = Text.from_markup(
        f"[bright_black]UPTIME  :[/]  [white]{days}d {hours}h {minutes}m[/]\n"
        f"[bright_black]HOST    :[/]  [cyan bold]{hostname}[/]\n"
        f"[bright_black]OS      :[/]  [cyan bold]{distro_name} {distro_version}[/]\n"
        f"[bright_black]KERNEL  :[/]  [cyan bold]{kernel}[/]\n"
        f"[bright_black]CPU     :[/]  {bar(cpu)}\n"
        f"{gpu_lines}"
        f"[bright_black]MEM     :[/]  {bar(mem)}\n"
        f"[bright_black]DISK    :[/]  {bar(disk)}\n"
    )

    return Panel(
        lines,
        title=f"[cyan bold]{name}[/]",
        border_style="bright_black",
        padding=(0, 1),
        )
