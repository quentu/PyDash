import argparse
from dataclasses import replace
from pathlib import Path
import signal
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rich.console import Console
from rich.live import Live
from dashboard.core.config import DEFAULT_CONFIG, load_config
from dashboard.core.manager import Monitor
from dashboard.ui.layout import build_layout


def main(argv=None):
    parser = argparse.ArgumentParser(description="PyDash fullscreen server monitoring console")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="servers YAML path")
    parser.add_argument("--interval", type=float, help="override polling interval (seconds)")
    parser.add_argument("--demo", action="store_true", help="explicit four-host simulated preview; no network access")
    parser.add_argument("--once", action="store_true", help="print one bounded snapshot without alternate screen")
    args = parser.parse_args(argv)
    console = Console()
    try:
        if args.demo:
            from dashboard.core.demo import DemoMonitor
            monitor = DemoMonitor()
        else:
            servers, settings = load_config(args.config)
            monitor = Monitor(servers, settings)
        if args.interval is not None:
            import math
            if not math.isfinite(args.interval) or args.interval < 0.2:
                raise ValueError("--interval must be finite and at least 0.2s")
            monitor.settings = replace(monitor.settings, interval=args.interval,
                                       stale_after=max(monitor.settings.stale_after, args.interval * 2))
    except ValueError as exc:
        console.print(f"Configuration error: {exc}", style="red", markup=False)
        return 2
    if not args.once and not console.is_terminal:
        console.print("A terminal is required. Use --once for a plain snapshot.", markup=False)
        return 2
    stopped = False

    def stop(signum, frame):
        nonlocal stopped
        stopped = True

    old_term = signal.signal(signal.SIGTERM, stop)
    try:
        if args.once:
            end = time.monotonic() + monitor.settings.timeout + 0.1
            monitor.tick()
            while monitor.inflight and time.monotonic() < end and not stopped:
                time.sleep(0.05)
                monitor.tick()
            console.print(build_layout(monitor, console.width, console.height, args.demo))
        else:
            with Live(console=console, screen=True, auto_refresh=False, vertical_overflow="crop") as live:
                while not stopped:
                    monitor.tick()
                    live.update(build_layout(monitor, console.width, console.height, args.demo), refresh=True)
                    time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        monitor.close()
        signal.signal(signal.SIGTERM, old_term)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

