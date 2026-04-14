from fastapi import FastAPI
import psutil
import pynvml
import socket
import time

app = FastAPI()

@app.get("/stats")
def get_stats():
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    
    gpu_mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
    gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle)

    return {
        "hostname": socket.gethostname(),
        "cpu": psutil.cpu_percent(),
        "gpu_mem_used": gpu_mem.used / 1024**2
        "gpu_mem_total": gpu_mem.total / 1024**2
        "gpu": gpu_util.gpu
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent,
        "uptime": int(time.time() - psutil.boot_time())
    }
