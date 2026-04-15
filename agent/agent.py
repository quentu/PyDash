from fastapi import FastAPI
import psutil
import pynvml
import socket
import time

app = FastAPI()

@app.get("/stats")
def get_stats():
    gpu = 0
    gpu_mem_used = 0
    gpu_mem_total = 0

    try:
        pynvml.nvmlInit()
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

            name = pynvml.nvmlDeviceGetName(handle).decode()
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

    except Exception:
        gpus = []

    return {
        "hostname": socket.gethostname(),
        "cpu": psutil.cpu_percent(),
        "gpus": gpus,
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent,
        "uptime": int(time.time() - psutil.boot_time())
        }
