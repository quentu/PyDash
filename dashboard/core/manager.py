from concurrent.futures import ThreadPoolExecutor
from collectors.api import fetch

def collect_all(servers):
    results = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch, s): s["name"]
            for s in servers
        }

        for future in futures:
            name = futures[future]
            results[name] = future.result()

    return results
