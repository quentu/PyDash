from fastapi import FastAPI
import psutil
import socket
import time

app = FastAPI()

@app.get("/stats")
def get_stats():
    return {
        "hostname": socket.gethostname(),
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent,
        "uptime": int(time.time() - psutil.boot_time())
    }
