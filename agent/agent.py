from fastapi import FastAPI
import psutil
import pynvml
import distro
import platform
import socket
import time

app = FastAPI()

try:
    pynvml.nvmlInit()
except:
    pass

@app.get("/stats")
def get_stats():
    gpu = 0
    gpu_mem_used = 0
    gpu_mem_total = 0

    try:
        device_count = pynvml.nvmlDeviceGetCount()

        gpus = []

        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)

            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)

            samples = []
            for _ in range(5):
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                samples.append(util.gpu)
                time.sleep(0.05)

            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode()
            temp = pynvml.nvmlDeviceGetTemperature(
                handle, pynvml.NVML_TEMPERATURE_GPU
            )

            gpus.append({
                "index": i,
                "name": name,
                "util": sum(samples) / len(samples),
                "temp": temp,
                "mem_used": mem.used / 1024**2,
                "mem_total": mem.total / 1024**2
                })

    except Exception as e:
        gpus = []
        #return {
        #    "error": str(e),
        #    "hostname": socket.gethostname()
        #}
    
    return {
        "hostname": socket.gethostname(),
        "cpu": psutil.cpu_percent(),
        "gpus": gpus,

        "mem_total": psutil.virtual_memory().total,
        "mem_available": psutil.virtual_memory().available,
        "mem_free": psutil.virtual_memory().free,
        "mem_used": psutil.virtual_memory().used,
        "mem_cached": psutil.virtual_memory().cached,

        "disk": psutil.disk_usage('/').percent,
        "disk_total": psutil.disk_usage('/').total,
        "disk_free": psutil.disk_usage('/').free,
        "disk_used": psutil.disk_usage('/').used,
        "uptime": int(time.time() - psutil.boot_time()),
        "distro_name": distro.name(),
        "distro_version": distro.version(),
        "kernel": platform.release()
        }
