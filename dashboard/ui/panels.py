from rich.panel import Panel
from rich.console import Group
from rich.text import Text
from rich.layout import Layout
from rich.columns import Columns

def percentify(numerator, denominator):
    res = int((round((numerator / denominator), 2) * 100))
    return res
def gib(val):
    res = round((val / (1.074 * 10**9)), 2)
    return res

def color(val, invert=False):
    if invert == False:
        return "green" if val < 50 else "yellow" if val < 70 else "red"
    elif invert == True:
        return "red" if val < 50 else "yellow" if val < 70 else "green"

def bar(val, width=20, invert=False):
    filled = int(val / 100 * width)
    empty = width - filled
    c = color(val, invert)
    return f"[{c}]{'■' * filled}[/][bright_black]{'■' * empty}[/] [{c}]{val}%[/]"

def sub_panel(data, var_title1, var_title2=None, graph=None):
    if graph is None:   
        panel = Panel(
                    data,
                    title=var_title1,
                    title_align="left",
                    padding=(0, 0, 0, 1),
                )
    else:
        panel = Panel(
                    data,
                    graph,
                    title=var_title,
                    padding=(0, 1, 0, 0),
                )
    return panel

def make_disk_panel(disk, disk_total, disk_free, disk_used):

    total = f"[bright_white bold] TOTAL: {gib(disk_total)} GiB"
    used = sub_panel(f"[bright_white]{bar(percentify(disk_used, disk_total))}",f"USED ─ {gib(disk_used)} GiB")
    free = sub_panel(f"[bright_white]{bar(percentify(disk_free, disk_total), 20, True)}",f"FREE ─ {gib(disk_free)} GiB")

    content = Group(
        total,
        used,
        free,
    )

    return Panel(
        content,
        title="[cyan bold]DISK[/]",
        border_style="bright_black",
        padding=(0, 0, 0, 0),
    )
def make_mem_panel(mem_total, mem_available, mem_free, mem_used, mem_cached):
    
    total = f"[bright_white bold] TOTAL: {gib(mem_total)} GiB"
    used = sub_panel(f"[bright_white]{bar(percentify(mem_used, mem_total))}",f"USED ─ {gib(mem_used)} GiB")
    available = sub_panel(f"[bright_white]{bar(percentify(mem_available, mem_total), 20, True)}",f"AVAILABLE ─ {gib(mem_available)} GiB")
    cached = sub_panel(f"[bright_white]{bar(percentify(gib(mem_cached),gib(mem_total)))}",f"CACHED ─ {gib(mem_cached)} GiB")
    free = sub_panel(f"[bright_white]{bar(percentify(gib(mem_free),gib(mem_total)), 20, True)}",f"FREE ─ {gib(mem_free)} GiB")

    content = Group(
        total,
        used,
        available,
        cached,
        free,
    )

    return Panel(
        content,
        title="[cyan bold]MEMORY[/]",
        border_style="bright_black",
        padding=(0, 0, 0, 0),
    )
def make_gpu_panel(gpu_data):
    if not gpu_data:
        return ""
 
    gpu_title = "[cyan bold]GPUS[/]" if len(gpu_data) > 1 else "[cyan bold]GPU[/]"
    sub_panels = []
 
    for gpu in gpu_data:
        label = f"GPU{gpu['index']}" if gpu['index'] > 0 else "GPU"
        gpu_name = gpu["name"]
        temp = gpu["temp"]
        util = gpu["util"]
 
        util_bar = sub_panel(
            f"[bright_white]{bar(util, 20)}",
            f"UTIL ─ {label}",
        )
        temp_bar = sub_panel(
            f"[bright_white]{bar(temp, 20)}",
            f"TEMP ─ {temp}°C",
        )
        gpu_group = Group(
            f"[bright_black]{gpu_name}[/]",
            util_bar,
            temp_bar,
        )
        sub_panels.append(gpu_group)
 
    content = Group(*sub_panels)
 
    return Panel(
        content,
        title=gpu_title,
        border_style="bright_black",
        padding=(0, 0, 0, 0),
    )

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
    mem_total = data["mem_total"]
    mem_available = data["mem_available"]
    mem_free = data["mem_free"]
    mem_used = data["mem_used"]
    mem_cached = data["mem_cached"]
    
    disk = data["disk"]
    disk_total = data["disk_total"]
    disk_free = data["disk_free"]
    disk_used = data["disk_used"]

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
                f"[bright_black]{label:<7} :[/]  {bar(gpu['util'],20)} "
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
        f"{gpu_lines}"
    )
    
    #split1 = Layout()
    split1 = Columns([
        make_disk_panel(disk, disk_total, disk_free, disk_used),
        make_mem_panel(mem_total, mem_available, mem_free, mem_used, mem_cached),
        make_gpu_panel(gpus),
    ], equal=False, expand=True)
    
    content = Group(
        lines,
        split1,
    )

    return Panel(
        content,
        title=f"[cyan bold]{name}[/]",
        border_style="bright_black",
        padding=(0, 1, 0, 0),
        )
