from fastapi import FastAPI
import psutil
import distro
import platform
import socket
import time
import os
from contextlib import asynccontextmanager
from threading import Event, Lock, Thread

try:
    import pynvml
except ImportError:
    pynvml = None;

_lock = Lock()
_snapshot = None

def gpu_stats():
    if pynvml is None:
        return []
    gpus = []
    try:
        count = pynvml.nvmlDeviceGetCount()
    except Exception:
        return []
    for index in range(count):
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(index)
            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            name = pynvml.nvmlDeviceGetName(handle)
            gpus.append({"index": index, "name": name.decode() if isinstance(name, bytes) else name,
                         "util": pynvml.nvmlDeviceGetUtilizationRates(handle).gpu,
                         "temp": pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU),
                         "mem_used": memory.used / 1024**2, "mem_total": memory.total / 1024**2})
        except Exception:
            continue
    return gpus


def collect_stats(cpu):
    memory, disk = psutil.virtual_memory(), psutil.disk_usage("/")
    network = psutil.net_io_counters()
    return {"hostname": socket.gethostname(), "cpu": cpu, "gpus": gpu_stats(),
            "mem_total": memory.total, "mem_available": memory.available,
            "mem_free": memory.free, "mem_used": memory.used,
            "mem_cached": getattr(memory, "cached", 0),
            "disk": disk.percent, "disk_total": disk.total,
            "disk_free": disk.free, "disk_used": disk.used,
            "uptime": int(time.time() - psutil.boot_time()), "boot_time": psutil.boot_time(),
            "load": list(os.getloadavg()) if hasattr(os, "getloadavg") else None,
            "network": {"bytes_recv": network.bytes_recv, "bytes_sent": network.bytes_sent} if network else None,
            "distro_name": distro.name(), "distro_version": distro.version(), "kernel": platform.release()}


def sample(stop):
    global _snapshot
    psutil.cpu_percent(None)  # discard the first, meaningless CPU sample
    while not stop.wait(1):
        try:
            snapshot = collect_stats(psutil.cpu_percent(None))
            with _lock:
                _snapshot = (time.monotonic(), snapshot)
        except (OSError, RuntimeError):
            # A stuck/failed sampler must not serve healthy-looking old data.
            continue


@asynccontextmanager
async def lifespan(app):
    global _snapshot
    _snapshot = None
    if pynvml is not None:
        try:
            pynvml.nvmlInit()
        except Exception:
            pass
    stop = Event()
    worker = Thread(target=sample, args=(stop,), daemon=True)
    worker.start()
    try:
        yield
    finally:
        stop.set()
        worker.join(timeout=2)
        if pynvml is not None:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass


app = FastAPI(lifespan=lifespan)


@app.get("/stats")
def get_stats():
    from fastapi.responses import JSONResponse
    with _lock:
        snapshot = _snapshot
    if snapshot is None or time.monotonic() - snapshot[0] > 5:
        return JSONResponse({"error": "Metrics sampler warming up or unavailable"}, status_code=503)
    return snapshot[1]
