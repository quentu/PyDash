from rich.panel import Panel
from rich.console import Group
from rich.text import Text


def color(val):
    return "green" if val < 50 else "yellow" if val < 80 else "red"


def bar(val, width=20):
    filled = int(val / 100 * width)
    empty = width - filled
    c = color(val)
    return f"[{c}]{'▣' * filled}[/][bright_black]{'□' * empty}[/] [{c}]{val}%[/]"


def make_panel(name, data):
    if "error" in data:
        return Panel(f"[red]{data['error']}[/red]", title=f"[red]{name}[/red]")

    hostname = data["hostname"]
    uptime   = data["uptime"]
    cpu      = data["cpu"]
    gpus     = data.get("gpus", [])
    mem      = data["memory"]
    disk     = data["disk"]

    hours   = uptime // 3600
    minutes = (uptime % 3600) // 60
    
    gpu_lines = ""

    if gpus:
        for gpu in gpus:
            label = f"GPU{gpu['index']}"
            gpu_name  = gpu["name"]
            temp  = gpu["temp"]

            gpu_lines += (
                f"[bright_black]{label:<7} :[/]  {bar(gpu['util'])} "
                f"[bright_black]{temp}°C[/] [bright_black]{gpu_name}[/]\n"
            )
    else:
        gpu_lines = f"[bright_black]GPU     :[/]  UNAVAILABLE\n"
    
    lines = Text.from_markup(
        f"[bright_black]UPTIME  :[/]  [white]{hours}h {minutes}m[/]\n"
        f"[bright_black]HOST    :[/]  [cyan bold]{hostname}[/]\n"
        f"\n"
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
