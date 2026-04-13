from rich.panel import Panel

def make_panel(name, data):
    if "error" in data:
        return Panel(f"[red]{data['error']}[/red]", title=name)
    
    hostname = data["hostname"]
    uptime = data["uptime"]

    hours = uptime // 3600
    minutes = (uptime % 3600) // 60

    cpu = data["cpu"]
    mem = data["memory"]
    disk = data["disk"]

    def color(val):
        return "green" if val < 50 else "yellow" if val < 80 else "red"

    content = (
        f"UPTIME: {hours} hours, {minutes} mins\n"
        f"HOSTNAME: [{(hostname)}]{hostname}\n"
        f"CPU: [{color(cpu)}]{cpu}%[/]\n"
        f"MEM: [{color(mem)}]{mem}%[/]\n"
        f"DISK: [{color(disk)}]{disk}%[/]"
    )

    return Panel(content, title=name)
