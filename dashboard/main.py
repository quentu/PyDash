import time
from rich.live import Live

from core.config import load_servers
from core.manager import collect_all
from ui.layout import build_layout
from ui.panels import make_panel

def main():
    servers = load_servers()
    layout = build_layout(servers)

    with Live(layout, refresh_per_second=2, screen=True):
        while True:
            stats = collect_all(servers)

            for name, data in stats.items():
                layout[name].update(make_panel(name, data))

            time.sleep(2)

if __name__ == "__main__":
    main()
