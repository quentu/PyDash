import requests
import json
import socket
import time
from urllib.parse import urlsplit
from dashboard.core.models import PollResult, ServerStatus

MAX_PAYLOAD = 1024 * 1024

def fetch(server, timeout=1.5):
    deadline = time.monotonic() + timeout
    try:
        with requests.get(server.url, timeout=(timeout, timeout), stream=True) as response:
            if not response.ok:
                return PollResult(error=f"Agent HTTP {response.status_code}", failure_status=ServerStatus.DEGRADED)
            body = bytearray()
            for chunk in response.iter_content(16384):
                body.extend(chunk)
                if len(body) > MAX_PAYLOAD:
                    return PollResult(error="Agent payload exceeds 1 MiB")
                if time.monotonic() > deadline:
                    return PollResult(error="Agent response timed out", failure_status=ServerStatus.OFFLINE)
            try:
                data = json.loads(body)
            except (ValueError, UnicodeError):
                return PollResult(error="Invalid JSON from agent")
            if not isinstance(data, dict) or not any(k in data for k in ("cpu", "mem_total", "disk", "uptime")):
                return PollResult(error="Unrecognized agent metrics payload")
        checks = {}
        for check in server.checks:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                checks[check.name] = False
                continue
            try:
                with socket.create_connection((check.host or urlsplit(server.url).hostname, check.port), timeout=min(0.3, remaining)):
                    checks[check.name] = True
            except OSError:
                checks[check.name] = False
        return PollResult(data=data, checks=checks)
    except requests.exceptions.SSLError:
        return PollResult(error="Agent TLS verification failed", failure_status=ServerStatus.DEGRADED)
    except (requests.Timeout, requests.ConnectionError):
        return PollResult(error="Agent unreachable / timeout", failure_status=ServerStatus.OFFLINE)
    except requests.RequestException:
        return PollResult(error="Agent request failed", failure_status=ServerStatus.DEGRADED)
