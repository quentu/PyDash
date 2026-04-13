import requests

def fetch(server):
    try:
        r = requests.get(server["url"], timeout=2)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}
