from rich.panel import Panel

def make_panel(name, data):
    if "error" in data:
        return Panel(f"[red]{data['error']}[/red]", title=name)

    cpu = data["cpu"]
    mem = data["memory"]
    disk = data["disk"]

    def color(val):
        return "green" if val < 50 else "yellow" if val < 80 else "red"

    content = (
        f"CPU: [{color(cpu)}]{cpu}%[/]\n"
        f"MEM: [{color(mem)}]{mem}%[/]\n"
        f"DISK: [{color(disk)}]{disk}%[/]"
    )

    return Panel(content, title=name)
